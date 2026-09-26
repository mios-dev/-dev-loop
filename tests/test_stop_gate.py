#!/usr/bin/env python3
"""
Control for the Stop hook, which is the only thing that can actually drive the loop.

The hole this closes
--------------------
SKILL.md 1 says "Re-arm the loop at the end of every cycle until acceptance criteria are met or
an explicit stop condition (12) is reached", and nothing in this repo implemented it: there is no
scheduler, no wakeup, no cron. The loop ran exactly as long as the agent felt like continuing.

stop-gate.sh was the one mechanism in a position to re-arm, and it did the opposite. It accepted
EVERY status -- done, partial, blocked, converged_stuck, budget, halted -- as grounds to stop. So
a turn that ended `"status": "partial"` was allowed to stop, and "partial" is precisely the status
that means work remains and nothing is preventing the next iteration.

SKILL.md 12 names the stop conditions: objectives pass verification, an external blocker needs the
operator, or further iterations yield zero net convergence. `partial` is none of those. Treating it
as terminal is a Skip-as-Pass (SKILL.md 7) applied to the loop itself -- the mechanism reported
success at looping by not looping.

So the statuses split:
  terminal      done blocked converged_stuck budget halted   -> stop is allowed
  non-terminal  partial                                      -> block, and say to run the next cycle

Bounded, because a Stop hook that always blocks is an infinite loop that spends real money:
DEVLOOP_LOOP_CAP (default 5) caps the continuations, separately from DEVLOOP_STOP_CAP, which caps
retries for a turn that emitted no report at all. Two different failures, two different counters.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(os.path.dirname(HERE), "hooks", "stop-gate.sh")


def run_gate(transcript_text, stop_hook_active=False, env=None, tmpdir=None):
    """Drive the hook exactly as Claude Code does: JSON on stdin, decision on stdout."""
    d = tmpdir or tempfile.mkdtemp()
    t = os.path.join(d, "transcript.jsonl")
    with open(t, "w", encoding="utf-8") as fh:
        fh.write(transcript_text)
    e = dict(os.environ)
    e["TMPDIR"] = d
    e.update(env or {})
    payload = json.dumps({"stop_hook_active": bool(stop_hook_active), "transcript_path": t})
    p = subprocess.run(["sh", GATE], input=payload, capture_output=True, text=True, env=e)
    return p.stdout.strip(), d


def transcript(status=None, mentions_devloop=True):
    lines = []
    if mentions_devloop:
        lines.append('{"m": "invoking dev-loop"}')
    if status is not None:
        # A real transcript line is JSONL whose message content has its quotes
        # escaped ONCE. Building this with json.dumps escapes them twice and the
        # gate's regex then matches nothing -- the harness lies, not the gate.
        lines.append('{"m": "devloop_report {\\"status\\": \\"%s\\"}"}' % status)
    return "\n".join(lines) + "\n"


def blocked(out):
    if not out:
        return None
    try:
        return json.loads(out)
    except ValueError:
        return None


class TestTerminalStatusesMayStop(unittest.TestCase):
    def test_done_allows_stop(self):
        out, _ = run_gate(transcript("done"))
        self.assertEqual(out, "", "a verified objective is a real stop condition")

    def test_blocked_allows_stop(self):
        out, _ = run_gate(transcript("blocked"))
        self.assertEqual(out, "", "an external blocker needs the operator, not another cycle")

    def test_converged_stuck_allows_stop(self):
        out, _ = run_gate(transcript("converged_stuck"))
        self.assertEqual(out, "", "zero net convergence is a stop condition")

    def test_budget_allows_stop(self):
        out, _ = run_gate(transcript("budget"))
        self.assertEqual(out, "")

    def test_halted_allows_stop(self):
        out, _ = run_gate(transcript("halted"))
        self.assertEqual(out, "")


class TestPartialReArms(unittest.TestCase):
    """The defect: `partial` means work remains, so it must NOT end the loop."""

    def test_partial_blocks_and_says_continue(self):
        out, _ = run_gate(transcript("partial"))
        d = blocked(out)
        self.assertIsNotNone(d, "partial must not be accepted as a reason to stop")
        self.assertEqual(d.get("decision"), "block")
        self.assertIn("next", d.get("reason", "").lower(),
                      "the reason must tell the agent to run the next cycle")

    def test_partial_is_bounded(self):
        """A Stop hook that always blocks is an infinite loop. The cap ends it."""
        d = tempfile.mkdtemp()
        env = {"DEVLOOP_LOOP_CAP": "2"}
        seen = []
        for _ in range(4):
            out, _ = run_gate(transcript("partial"), env=env, tmpdir=d)
            seen.append(bool(blocked(out)))
        self.assertTrue(seen[0] and seen[1], "the first cycles must re-arm")
        self.assertIn(False, seen, "the cap must eventually allow the stop")


class TestPreExistingBehaviourHolds(unittest.TestCase):
    def test_no_report_still_blocks(self):
        out, _ = run_gate(transcript(None))
        d = blocked(out)
        self.assertIsNotNone(d, "a turn with no report must still be refused")
        self.assertIn("devloop_report", d.get("reason", ""))

    def test_stop_hook_active_is_honoured(self):
        out, _ = run_gate(transcript("partial"), stop_hook_active=True)
        self.assertEqual(out, "", "the loop guard is mandatory and outranks re-arming")

    def test_unrelated_session_is_not_gated(self):
        # No report AND no mention. A transcript carrying a devloop_report cannot
        # be "unrelated" -- the word devloop is inside the report marker itself --
        # so constructing that case with a report in it tests nothing.
        out, _ = run_gate('{"m": "an unrelated session"}\n')
        self.assertEqual(out, "", "a session that never ran the loop is none of this hook's business")



FIX = os.path.join(HERE, "fixtures", "transcripts")


def fixture(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as fh:
        return fh.read()


def run_event(text, event="Stop", env=None, tmpdir=None):
    d = tmpdir or tempfile.mkdtemp()
    t = os.path.join(d, "transcript.jsonl")
    with open(t, "w", encoding="utf-8") as fh:
        fh.write(text)
    e = dict(os.environ, TMPDIR=d, **(env or {}))
    payload = json.dumps({"stop_hook_active": False, "transcript_path": t, "hook_event_name": event})
    p = subprocess.run(["sh", GATE], input=payload, capture_output=True, text=True, env=e)
    return blocked(p.stdout.strip())


def asks_natively(d):
    return bool(d) and "native question UI" in d.get("reason", "")


class TestQuestionsGoThroughTheNativeUI(unittest.TestCase):
    """SKILL.md 5: operator questions go through the harness's question UI, never chat prose.
    Both fixtures are real turns from a monitor session (tool inputs and results elided):
    chat-question.jsonl ends "Want me to launch one?" in prose; native-ask.jsonl asked with
    AskUserQuestion."""

    def test_a_question_in_chat_is_sent_back(self):
        d = run_event(fixture("chat-question.jsonl"))
        self.assertTrue(asks_natively(d), d)
        self.assertIn("Want me to launch one?", d["reason"], "the reason must quote the offending line")

    def test_a_native_ask_is_not_flagged(self):
        self.assertFalse(asks_natively(run_event(fixture("native-ask.jsonl"))))

    def test_the_tool_call_exempts_the_same_prose(self):
        ask = [l for l in fixture("native-ask.jsonl").splitlines() if "AskUserQuestion" in l]
        self.assertTrue(ask, "the native fixture must carry the tool call")
        rows = fixture("chat-question.jsonl").splitlines()
        text = "\n".join(rows[:2] + ask + rows[2:]) + "\n"
        self.assertFalse(asks_natively(run_event(text)), "a turn that asked natively may also mention it")

    def test_a_lane_is_not_held_to_it(self):
        self.assertFalse(asks_natively(run_event(fixture("chat-question.jsonl"), event="SubagentStop")),
                         "a lane has no question UI; it returns blocked instead")

    def test_a_ui_less_host_can_opt_out(self):
        self.assertFalse(asks_natively(run_event(fixture("chat-question.jsonl"),
                                                 env={"DEVLOOP_NATIVE_ASK": "0"})))

    def test_an_open_operator_question_is_re_asked_every_turn(self):
        """open-blocker.jsonl is a real turn that ended blocked on "Task #8: operator decision on
        the revised SPIKE" without asking it."""
        d = run_event(fixture("open-blocker.jsonl"))
        self.assertTrue(d and "blocked on the operator" in d.get("reason", ""), d)
        self.assertIn("Task #8", d["reason"], "the reason must name the open item")

    def test_asking_it_clears_the_open_item(self):
        ask = [l for l in fixture("native-ask.jsonl").splitlines() if "AskUserQuestion" in l]
        rows = fixture("open-blocker.jsonl").splitlines()
        text = "\n".join(rows[:2] + ask + rows[2:]) + "\n"
        d = run_event(text)
        self.assertFalse(d and "blocked on the operator" in d.get("reason", ""), d)

    def test_a_report_not_blocked_is_not_held(self):
        text = fixture("open-blocker.jsonl").replace('\\"status\\": \\"blocked\\"', '\\"status\\": \\"done\\"', 1)
        self.assertNotEqual(text, fixture("open-blocker.jsonl"), "the plant must land")
        d = run_event(text)
        self.assertFalse(d and "blocked on the operator" in d.get("reason", ""), d)

    def test_it_is_bounded(self):
        d = tempfile.mkdtemp()
        seen = [asks_natively(run_event(fixture("chat-question.jsonl"), env={"DEVLOOP_ASK_CAP": "2"},
                                        tmpdir=d)) for _ in range(3)]
        self.assertEqual(seen, [True, True, False], "two send-backs, then the stop is allowed")


if __name__ == "__main__":
    unittest.main()
