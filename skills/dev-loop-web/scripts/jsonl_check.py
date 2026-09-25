#!/usr/bin/env python3
"""Check a JSONL dataset line by line. Offline; Python 3 standard library only; never touches
the network. Every project value (the exact key set, the minimum count, the split rule) is an
argument copied from the contract fetched on this run; nothing here is a default for a project.

  python3 jsonl_check.py FILE --keys k1,k2[,...] [--min N]
        [--shape openai-chat|openai-preference] [--roles system,user,assistant]
        [--split-hex-prefixes 0,1 [--split-with-newline]] [--against OTHER.jsonl ...]
        [--two-sided DEVLOOP-PLANTED-<ID>]
  python3 jsonl_check.py --self-test

Always checked: UTF-8, no byte-order mark, no blank line, no CRLF, one JSON object per line,
exactly the --keys top-level key set, no duplicate line (and none shared with --against files),
at least --min records and never zero.
  --shape openai-chat        `messages` is a non-empty list; roles from --roles; a system message
                             only first; the last message is an assistant with non-empty content.
  --shape openai-preference  `input.messages` ends with a user turn; `preferred_output` and
                             `non_preferred_output` each hold exactly one non-empty assistant
                             message, and the two differ.
  --split-hex-prefixes P,Q   a record is validation when the lowercase sha256 hex of its line
                             starts with one of the prefixes; both splits must be non-empty. The
                             line is hashed without its newline unless --split-with-newline; use
                             whichever reading the contract states, and say which.
--two-sided appends a record carrying the sentinel as an extra key to a copy, requires the check
to fail naming it, then requires the real file to pass. Exit 0 = pass, 1 = fail, 2 = usage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

SENTINEL_RE = re.compile(r"^DEVLOOP-PLANTED-[A-Z0-9]+(-[A-Z0-9]+)*$")


def nonempty_text(v):
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, list):  # content parts
        return any(isinstance(p, dict) and isinstance(p.get("text"), str) and p["text"].strip() for p in v)
    return False


def shape_chat(obj, roles):
    msgs = obj.get("messages")
    if not isinstance(msgs, list) or not msgs:
        return ["messages is not a non-empty list"]
    out = []
    for j, m in enumerate(msgs):
        if not isinstance(m, dict):
            out.append("messages[%d] is not an object" % j)
            continue
        r = m.get("role")
        if r not in roles:
            out.append("messages[%d] role %r not in %s" % (j, r, sorted(roles)))
        if r == "system" and j != 0:
            out.append("messages[%d] is a system message after the first position" % j)
    last = msgs[-1] if isinstance(msgs[-1], dict) else {}
    if last.get("role") != "assistant" or not nonempty_text(last.get("content")):
        out.append("the last message is not an assistant message with non-empty content")
    return out


def one_assistant(v, name):
    if not isinstance(v, list) or len(v) != 1 or not isinstance(v[0], dict):
        return None, ["%s is not a list of exactly one message" % name]
    m = v[0]
    if m.get("role") != "assistant" or not nonempty_text(m.get("content")):
        return None, ["%s[0] is not an assistant message with non-empty content" % name]
    return m.get("content"), []


def shape_preference(obj, roles):
    out = []
    inp = obj.get("input")
    msgs = inp.get("messages") if isinstance(inp, dict) else None
    if not isinstance(msgs, list) or not msgs:
        out.append("input.messages is not a non-empty list")
    else:
        for j, m in enumerate(msgs):
            if not isinstance(m, dict) or m.get("role") not in roles:
                out.append("input.messages[%d] role not in %s" % (j, sorted(roles)))
        if not (isinstance(msgs[-1], dict) and msgs[-1].get("role") == "user"):
            out.append("input.messages does not end with a user turn")
    p, e1 = one_assistant(obj.get("preferred_output"), "preferred_output")
    n, e2 = one_assistant(obj.get("non_preferred_output"), "non_preferred_output")
    out += e1 + e2
    if p is not None and n is not None and p == n:
        out.append("preferred_output and non_preferred_output are identical")
    return out


def read_lines(path):
    with open(path, "rb") as f:
        raw = f.read()
    text = raw.decode("utf-8")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return raw, text, lines


def check(path, o):
    """Return (failures, records, summary)."""
    fails = []
    try:
        raw, text, lines = read_lines(path)
    except UnicodeDecodeError as e:
        return ["not UTF-8 at byte %d" % e.start], 0, ""
    except OSError as e:
        return ["cannot read: %s" % e], 0, ""
    if not raw:
        return ["empty file: 0 records"], 0, ""
    if text.startswith("﻿"):
        fails.append("line 1: starts with a byte-order mark")
    others = {}
    for other in o.against:
        try:
            for j, ln in enumerate(read_lines(other)[2], 1):
                others.setdefault(ln, "%s line %d" % (os.path.basename(other), j))
        except (OSError, UnicodeDecodeError) as e:
            fails.append("--against %s unreadable: %s" % (other, e))
    seen, n, val = {}, 0, 0
    for i, line in enumerate(lines, 1):
        if not line.strip():
            fails.append("line %d: blank line" % i)
            continue
        if line.endswith("\r"):
            fails.append("line %d: CRLF line ending" % i)
        try:
            obj = json.loads(line)
        except ValueError as e:
            fails.append("line %d: not JSON (%s)" % (i, getattr(e, "msg", e)))
            continue
        if not isinstance(obj, dict):
            fails.append("line %d: not a JSON object" % i)
            continue
        n += 1
        keys = set(obj)
        if keys != o.keys:
            fails.append("line %d: key set mismatch: extra %s missing %s" % (i, sorted(keys - o.keys), sorted(o.keys - keys)))
        if line in seen:
            fails.append("line %d: duplicate of line %d" % (i, seen[line]))
        else:
            seen[line] = i
        if line in others:
            fails.append("line %d: duplicate of %s" % (i, others[line]))
        if o.shape == "openai-chat":
            fails += ["line %d: %s" % (i, x) for x in shape_chat(obj, o.roles)]
        elif o.shape == "openai-preference":
            fails += ["line %d: %s" % (i, x) for x in shape_preference(obj, o.roles)]
        if o.prefixes:
            b = (line + "\n" if o.with_newline else line).encode("utf-8")
            if hashlib.sha256(b).hexdigest().startswith(o.prefixes):
                val += 1
    summary = "%d records, keys %s" % (n, sorted(o.keys))
    if o.shape:
        summary += ", shape %s" % o.shape
    if n == 0:
        fails.append("empty set: 0 records parsed")
    if n < o.min:
        fails.append("%d records, below the minimum %d" % (n, o.min))
    if o.prefixes and n:
        summary += ", split train %d / validation %d (prefixes %s, line hashed %s newline)" % (
            n - val, val, ",".join(o.prefixes), "with" if o.with_newline else "without")
        if val == 0 or val == n:
            fails.append("split: train %d / validation %d, both must be non-empty" % (n - val, val))
    return fails, n, summary


def two_sided(path, o, sentinel):
    if not SENTINEL_RE.match(sentinel):
        return 2, "sentinel must look like DEVLOOP-PLANTED-<ID> (uppercase, digits, hyphens)"
    with open(path, "rb") as f:
        raw = f.read()
    if sentinel.encode("utf-8") in raw:
        return 1, "FAIL two-sided jsonl_check: %s already occurs in the file; pick another" % sentinel
    try:
        rec = json.loads(raw.decode("utf-8").split("\n", 1)[0])
        rec = rec if isinstance(rec, dict) else {}
    except ValueError:
        rec = {}
    rec[sentinel] = 1
    tmp = tempfile.mkdtemp(prefix="jsonl-plant-")
    try:
        planted = os.path.join(tmp, os.path.basename(path))
        shutil.copyfile(path, planted)
        with open(planted, "ab") as f:
            if raw and not raw.endswith(b"\n"):
                f.write(b"\n")
            f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n")
        pf, _, _ = check(planted, o)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    named = [x for x in pf if sentinel in x]
    if not named:
        return 1, "FAIL two-sided jsonl_check: the planted record was not caught by name (%s)" % (pf[:1] or "passed")
    rf, n, summary = check(path, o)
    if rf:
        return 1, "FAIL two-sided jsonl_check: plant caught, but the real file fails: %s" % "; ".join(rf[:5])
    return 0, "PASS two-sided jsonl_check %s: plant %s -> FAIL naming it (%s); real -> PASS (%s)" % (
        os.path.basename(path), sentinel, named[0], summary)


class Opts(object):
    def __init__(self, keys, min_=1, shape=None, roles=("system", "user", "assistant"), prefixes=(), with_newline=False, against=()):
        self.keys = set(keys)
        self.min = min_
        self.shape = shape
        self.roles = set(roles)
        self.prefixes = tuple(prefixes)
        self.with_newline = with_newline
        self.against = list(against)


def self_test():
    tmp = tempfile.mkdtemp(prefix="jsonl-selftest-")
    try:
        chat = os.path.join(tmp, "chat.jsonl")
        with open(chat, "w", encoding="utf-8") as f:
            for q in range(12):
                f.write(json.dumps({"messages": [{"role": "user", "content": "q%d" % q},
                                                 {"role": "assistant", "content": "a%d" % q}]}, separators=(",", ":")) + "\n")
        o = Opts(["messages"], min_=12, shape="openai-chat", prefixes=("0", "1", "2", "3", "4", "5", "6", "7"))
        rc, line = two_sided(chat, o, "DEVLOOP-PLANTED-SELFTEST")
        if rc != 0:
            print("SELF-TEST FAIL jsonl_check.py: " + line)
            return 1
        bad = os.path.join(tmp, "bad.jsonl")
        with open(bad, "w", encoding="utf-8") as f:
            f.write('{"messages":[{"role":"user","content":"q"}]}\n\n')
        fails, _, _ = check(bad, Opts(["messages"], shape="openai-chat"))
        if not (any("blank line" in x for x in fails) and any("last message" in x for x in fails)):
            print("SELF-TEST FAIL jsonl_check.py: defects not reported: %s" % fails)
            return 1
        print("SELF-TEST PASS jsonl_check.py (python %s): %s" % (sys.version.split()[0], line))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--keys", help="exact top-level key set, comma-separated (from the contract)")
    ap.add_argument("--min", type=int, default=1)
    ap.add_argument("--shape", choices=["openai-chat", "openai-preference"])
    ap.add_argument("--roles", default="system,user,assistant")
    ap.add_argument("--split-hex-prefixes", default="")
    ap.add_argument("--split-with-newline", action="store_true")
    ap.add_argument("--against", action="append", default=[])
    ap.add_argument("--two-sided", metavar="SENTINEL")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.file or not a.keys:
        print("usage: FILE and --keys are required (the key set comes from the contract)", file=sys.stderr)
        return 2
    prefixes = tuple(p.strip().lower() for p in a.split_hex_prefixes.split(",") if p.strip())
    o = Opts([k.strip() for k in a.keys.split(",") if k.strip()], a.min, a.shape,
             [r.strip() for r in a.roles.split(",") if r.strip()], prefixes, a.split_with_newline, a.against)
    if a.two_sided:
        rc, line = two_sided(a.file, o, a.two_sided)
        print(line)
        return rc
    fails, n, summary = check(a.file, o)
    for x in fails[:40]:
        print("FAIL jsonl_check %s: %s" % (os.path.basename(a.file), x))
    if len(fails) > 40:
        print("FAIL jsonl_check %s: ... %d more" % (os.path.basename(a.file), len(fails) - 40))
    if fails:
        return 1
    print("PASS jsonl_check %s: %s" % (os.path.basename(a.file), summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
