#!/usr/bin/env python3
"""Byte counts and sha256 digests of the exact files a run attaches, and a build-twice
determinism check. Offline; Python 3 standard library only; never touches the network.

  python3 digest.py FILE...                    one JSON object per file: name, bytes, sha256
  python3 digest.py --compare DIR_A DIR_B      are two builds of the same inputs byte-identical?
  python3 digest.py --compare DIR_A DIR_B --two-sided DEVLOOP-PLANTED-<ID>
  python3 digest.py --self-test                capability probe: proves this runner executes
                                               bundled code and that the check can fail

--two-sided first runs the comparison on a copy of DIR_B with the sentinel appended to one
file and requires a failure that names the sentinel, then runs it on the real builds and
requires a pass over a non-zero number of files. Exit 0 = pass, 1 = check failed, 2 = usage.
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


def sha256_file(path):
    h = hashlib.sha256()
    n = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            n += len(chunk)
    return n, h.hexdigest()


def tree(root):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            p = os.path.join(base, name)
            out[os.path.relpath(p, root).replace(os.sep, "/")] = p
    return out


def show(data):
    # wide enough to carry a whole bundle-derived sentinel: a truncated plant is not a named plant
    return repr(bytes(data))[2:-1][:240]


def compare(a, b):
    """Return (failures, files_compared)."""
    fails = []
    ta, tb = tree(a), tree(b)
    if not ta and not tb:
        return ["empty set: neither build contains a file"], 0
    for rel in sorted(set(ta) - set(tb)):
        fails.append("NONDETERMINISTIC only in the first build: %s" % rel)
    for rel in sorted(set(tb) - set(ta)):
        fails.append("NONDETERMINISTIC only in the second build: %s" % rel)
    n = 0
    for rel in sorted(set(ta) & set(tb)):
        n += 1
        with open(ta[rel], "rb") as f:
            da = f.read()
        with open(tb[rel], "rb") as f:
            db = f.read()
        if da != db:
            k = next((i for i in range(min(len(da), len(db))) if da[i] != db[i]), min(len(da), len(db)))
            fails.append("NONDETERMINISTIC %s differs at byte %d: second build has '%s'" % (rel, k, show(db[k:k + 200])))
    return fails, n


def contains(root, token):
    t = token.encode("utf-8")
    for p in tree(root).values():
        with open(p, "rb") as f:
            if t in f.read():
                return True
    return False


def two_sided(a, b, sentinel):
    if not SENTINEL_RE.match(sentinel):
        return 2, "sentinel must look like DEVLOOP-PLANTED-<ID> (uppercase, digits, hyphens)"
    if contains(a, sentinel) or contains(b, sentinel):
        return 1, "FAIL two-sided digest: %s already occurs in the input, so a failure naming it proves nothing; pick another" % sentinel
    tmp = tempfile.mkdtemp(prefix="digest-plant-")
    try:
        planted = os.path.join(tmp, "b")
        shutil.copytree(b, planted)
        files = tree(planted)
        if not files:
            return 1, "FAIL two-sided digest: nothing to plant into (empty build)"
        first = sorted(files)[0]
        with open(files[first], "ab") as f:
            f.write(b"\n" + sentinel.encode("utf-8"))
        pf, _ = compare(a, planted)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    named = [x for x in pf if sentinel in x]
    if not named:
        return 1, "FAIL two-sided digest: the planted copy was not caught by name (%s)" % (pf[:1] or "passed")
    rf, n = compare(a, b)
    if rf or n == 0:
        return 1, "FAIL two-sided digest: plant caught, but the real builds fail: %s" % "; ".join(rf[:5] or ["0 files"])
    return 0, "PASS two-sided digest: plant %s -> FAIL naming it (%s); real -> PASS (%d files identical)" % (sentinel, named[0], n)


def self_test():
    tmp = tempfile.mkdtemp(prefix="digest-selftest-")
    try:
        for side in ("a", "b"):
            os.makedirs(os.path.join(tmp, side, "sub"))
            with open(os.path.join(tmp, side, "one.jsonl"), "wb") as f:
                f.write(b'{"k":1}\n')
            with open(os.path.join(tmp, side, "sub", "two.txt"), "wb") as f:
                f.write(b"same bytes\n")
        rc, line = two_sided(os.path.join(tmp, "a"), os.path.join(tmp, "b"), "DEVLOOP-PLANTED-SELFTEST")
        if rc != 0:
            print("SELF-TEST FAIL digest.py: " + line)
            return 1
        with open(os.path.join(tmp, "b", "sub", "two.txt"), "wb") as f:
            f.write(b"different\n")
        fails, _ = compare(os.path.join(tmp, "a"), os.path.join(tmp, "b"))
        if not any("sub/two.txt differs" in x for x in fails):
            print("SELF-TEST FAIL digest.py: a changed file was not reported: %s" % fails)
            return 1
        print("SELF-TEST PASS digest.py (python %s): %s" % (sys.version.split()[0], line))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--compare", nargs=2, metavar=("DIR_A", "DIR_B"))
    ap.add_argument("--two-sided", metavar="SENTINEL")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.compare:
        da, db = a.compare
        if not (os.path.isdir(da) and os.path.isdir(db)):
            print("usage: --compare needs two directories", file=sys.stderr)
            return 2
        if a.two_sided:
            rc, line = two_sided(da, db, a.two_sided)
            print(line)
            return rc
        fails, n = compare(da, db)
        for x in fails:
            print(x)
        if fails:
            return 1
        print("PASS digest --compare: %d files identical" % n)
        return 0
    if not a.files:
        ap.print_usage(sys.stderr)
        return 2
    rc = 0
    for p in a.files:
        if not os.path.isfile(p):
            print("FAIL digest: %s is not a file" % p)
            rc = 1
            continue
        n, h = sha256_file(p)
        if n == 0:
            print("FAIL digest: %s is 0 bytes" % p)
            rc = 1
        print(json.dumps({"name": os.path.basename(p), "bytes": n, "sha256": h}, sort_keys=True))
    return rc


if __name__ == "__main__":
    sys.exit(main())
