#!/usr/bin/env python3
"""
Control for the fan-out measurement in agy_session.py.

The hole this closes
--------------------
The dispatch prompt tells the manager to start every independent lane in the SAME turn.
Nothing measured whether it did. agy_host.sh already records what that costs, from an
earlier run: the manager "provisioned all three worktrees, invoked the first native lane,
and ended its turn saying it was waiting for the lane to report" -- three worktrees left
at dirty=0.

The poll prompt then made it worse. It said, unconditionally, "Do NOT start new work and
do NOT re-dispatch a lane that is already running." Those are two different instructions
wearing one sentence: not re-dispatching a RUNNING lane is a rule, and not starting a lane
that was never dispatched is the opposite of what the run needs. A manager that dispatched
one lane of four was being told to sit and wait for it, and the session then spent its
whole poll budget serialising.

So the session counts distinct subagent step indices, compares that with the number of
antigravity lanes, and when lanes were never started says so explicitly in the next turn.

Two properties have to hold or the measurement is theatre:
  * a subagent step reports ACTIVE and then DONE under ONE step_index, so counting events
    instead of indices would report a fan-out that never happened;
  * the catch-up sentence must appear ONLY when a lane was never dispatched -- telling a
    manager to "dispatch every lane" while all of them are already running is how you get
    a lane run twice.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "skills" / "dev-loop" / "scripts"
spec = importlib.util.spec_from_file_location("agy_session", SCRIPTS / "agy_session.py")
AS = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AS)

LANES4 = ["srf-libexec", "srf-lib", "srf-tests", "srf-native"]


class TestUndispatched(unittest.TestCase):
    def test_the_measured_incident_is_counted(self):
        """One subagent for four lanes: three were never started."""
        self.assertEqual(AS.undispatched({19}, LANES4), 3)

    def test_a_full_fan_out_is_zero(self):
        self.assertEqual(AS.undispatched({19, 20, 21, 22}, LANES4), 0)

    def test_active_then_done_is_one_dispatch_not_two(self):
        """A set keyed by step_index; counting events would read 2 of 4 as a fan-out."""
        steps = set()
        for state in ("ACTIVE", "DONE"):          # same step, two events
            steps.add(19)
        self.assertEqual(len(steps), 1)
        self.assertEqual(AS.undispatched(steps, LANES4), 3)

    def test_more_subagents_than_lanes_never_goes_negative(self):
        """A manager may spawn helpers of its own; that is not negative shortfall."""
        self.assertEqual(AS.undispatched({1, 2, 3, 4, 5, 6}, LANES4), 0)

    def test_no_antigravity_lanes_means_nothing_to_dispatch(self):
        self.assertEqual(AS.undispatched(set(), []), 0)


class TestPollMessage(unittest.TestCase):
    def msg(self, steps, lanes=None, outstanding=None):
        return AS.poll_message("/repo/.devloop/native",
                               outstanding if outstanding is not None else ["srf-lib"],
                               steps, lanes if lanes is not None else LANES4)

    def test_a_shortfall_tells_the_manager_to_dispatch_the_rest(self):
        m = self.msg({19})
        self.assertIn("Dispatch every", m)
        self.assertIn("all of them at once", m)
        self.assertNotIn("Do NOT start new work", m,
                         "the old unconditional sentence is what stalled the run")

    def test_a_full_fan_out_still_forbids_new_work(self):
        m = self.msg({19, 20, 21, 22})
        self.assertIn("Do NOT start new work", m)
        self.assertNotIn("Dispatch every", m)

    def test_re_dispatching_a_running_lane_is_forbidden_either_way(self):
        """The half of the old sentence that WAS a rule survives in both branches."""
        for steps in ({19}, {19, 20, 21, 22}):
            self.assertIn("Never re-dispatch a lane that is already running", self.msg(steps))

    def test_every_message_names_the_outstanding_lanes_and_the_report_path(self):
        m = self.msg({19}, outstanding=["srf-lib", "srf-tests"])
        self.assertIn("srf-lib", m)
        self.assertIn("srf-tests", m)
        self.assertIn("/repo/.devloop/native/report-<LANE_ID>.json", m)

    def test_the_shortfall_sentence_states_the_real_numbers(self):
        m = self.msg({19})
        self.assertIn("only 1 subagent(s)", m)
        self.assertIn("for 4 antigravity lane(s)", m)


class TestWiring(unittest.TestCase):
    def test_the_loop_records_subagent_steps_by_index(self):
        src = (SCRIPTS / "agy_session.py").read_text()
        self.assertIn('u.get("step_type") == "subagent"', src)
        self.assertIn('subagent_steps.add(u["step_index"])', src)

    def test_the_loop_sends_the_computed_message(self):
        src = (SCRIPTS / "agy_session.py").read_text()
        self.assertIn("poll_message(native_dir, outstanding, subagent_steps, lane_ids)", src)


if __name__ == "__main__":
    unittest.main()
