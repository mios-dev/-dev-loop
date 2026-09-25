#!/usr/bin/env python3
"""Scan the files a run is about to attach (and the reply draft, saved as a file) for credentials
and personal data. Offline; Python 3 standard library only; never touches the network. Tar
archives are opened and every member is scanned, including tar layers nested inside them.

  python3 secret_scan.py FILE [FILE ...] [--allow EXACT ...] [--two-sided DEVLOOP-PLANTED-<ID>]
  python3 secret_scan.py --self-test

A finding prints its location and kind, never the matched text, so the scan cannot leak what it
found. When a planted sentinel is on the same line it is named. --allow skips a match only when
the whole matched string equals the value (anchored; never a substring). Scope: the patterns
below; an identifier type they do not cover is not detected, and the PASS line says what ran.
--two-sided adds a line holding the sentinel and a planted address to a copy of the first file,
requires a finding naming the sentinel, then requires the real files to have none. Exit 0/1/2.
"""
from __future__ import annotations

import argparse
import gzip
import io
import os
import re
import shutil
import sys
import tarfile
import tempfile

SENTINEL_RE = re.compile(r"^DEVLOOP-PLANTED-[A-Z0-9]+(-[A-Z0-9]+)*$")
SENTINEL_ANY = re.compile(r"DEVLOOP-PLANTED-[A-Z0-9]+(?:-[A-Z0-9]+)*")
PATTERNS = (
    ("private-key-block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github-pat", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})\b")),
    ("google-aiza-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("slack-xox", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("api-secret-key", re.compile(r"\bsk-(?:[a-z]+-)?[A-Za-z0-9_\-]{20,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}")),
    ("bearer-credential", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/\-]{20,}=*")),
    ("basic-auth-in-url", re.compile(r"[a-z][a-z0-9+.\-]*://[^/\s:@]+:[^/\s@]+@")),
    ("password-hash", re.compile(r"\$(?:1|2[aby]|5|6|y|argon2(?:id|i|d))\$[^\s\"']{8,}")),
    ("credential-assignment", re.compile(r"(?i)\b(?:api[_\-]?key|secret|passwd|password|access[_\-]?token)\b[\"']?\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']")),
    ("email-address", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}\b")),
)


def scan_text(text, where, allow, out):
    lines = 0
    for i, line in enumerate(text.splitlines(), 1):
        lines += 1
        for kind, rx in PATTERNS:
            for m in rx.finditer(line):
                if m.group(0) in allow:
                    continue
                s = SENTINEL_ANY.search(line)
                out.append("%s:%d: %s%s" % (where, i, kind, " (planted: %s)" % s.group(0) if s else ""))
    return lines


def scan_bytes(data, where, allow, out, depth=0):
    """Return (files, lines) scanned."""
    if data[:2] == b"\x1f\x8b" and depth < 4:
        try:
            data = gzip.decompress(data)
        except (OSError, EOFError):
            pass
    if depth < 4 and len(data) >= 512:
        try:
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as tf:
                members = [m for m in tf.getmembers() if m.isfile()]
                files = lines = 0
                for m in members:
                    f, l = scan_bytes(tf.extractfile(m).read(), "%s!%s" % (where, m.name), allow, out, depth + 1)
                    files += f
                    lines += l
                return files, lines
        except (tarfile.TarError, EOFError):
            pass
    return 1, scan_text(data.decode("utf-8", errors="replace"), where, allow, out)


def scan(paths, allow):
    out, files, lines = [], 0, 0
    for p in paths:
        try:
            with open(p, "rb") as f:
                data = f.read()
        except OSError as e:
            out.append("%s: unreadable (%s)" % (p, e))
            continue
        f_, l_ = scan_bytes(data, os.path.basename(p), allow, out)
        files += f_
        lines += l_
    if files == 0 or lines == 0:
        out.append("empty set: %d files, %d lines scanned" % (files, lines))
    return out, files, lines


def plant_line(sentinel):
    # the address is assembled here so this file holds no literal address of its own
    return "%s contact %s" % (sentinel, sentinel.lower() + "@" + "example.invalid")


def two_sided(paths, allow, sentinel):
    if not SENTINEL_RE.match(sentinel):
        return 2, "sentinel must look like DEVLOOP-PLANTED-<ID> (uppercase, digits, hyphens)"
    for p in paths:
        with open(p, "rb") as f:
            if sentinel.encode("utf-8") in f.read():
                return 1, "FAIL two-sided secret_scan: %s already occurs in %s; pick another" % (sentinel, p)
    tmp = tempfile.mkdtemp(prefix="scan-plant-")
    try:
        first = paths[0]
        planted = os.path.join(tmp, os.path.basename(first))
        line = (plant_line(sentinel) + "\n").encode("utf-8")
        with open(first, "rb") as f:
            data = f.read()
        try:
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as tf:
                members = [(m, tf.extractfile(m).read() if m.isfile() else None) for m in tf.getmembers()]
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tf:
                for m, body in members:
                    tf.addfile(m, io.BytesIO(body) if body is not None else None)
                ti = tarfile.TarInfo(sentinel + ".txt")
                ti.size = len(line)
                tf.addfile(ti, io.BytesIO(line))
            data = buf.getvalue()
        except tarfile.TarError:
            data = data + (b"" if data.endswith(b"\n") or not data else b"\n") + line
        with open(planted, "wb") as f:
            f.write(data)
        pf, _, _ = scan([planted] + list(paths[1:]), allow)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    named = [x for x in pf if sentinel in x]
    if not named:
        return 1, "FAIL two-sided secret_scan: the planted line was not caught by name (%s)" % (pf[:1] or "no finding")
    rf, files, lines = scan(paths, allow)
    if rf:
        return 1, "FAIL two-sided secret_scan: plant caught, but the real files have findings: %s" % "; ".join(rf[:5])
    return 0, "PASS two-sided secret_scan: plant %s -> FAIL naming it (%s); real -> PASS (%d files, %d lines, %d patterns, 0 findings)" % (
        sentinel, named[0], files, lines, len(PATTERNS))


def self_test():
    tmp = tempfile.mkdtemp(prefix="scan-selftest-")
    try:
        clean = os.path.join(tmp, "clean.jsonl")
        with open(clean, "w", encoding="utf-8") as f:
            f.write('{"messages":[{"role":"user","content":"which endpoint?"},{"role":"assistant","content":"the configured one"}]}\n')
        rc, line = two_sided([clean], set(), "DEVLOOP-PLANTED-SELFTEST")
        if rc != 0:
            print("SELF-TEST FAIL secret_scan.py: " + line)
            return 1
        dirty = os.path.join(tmp, "dirty.txt")
        with open(dirty, "w", encoding="utf-8") as f:  # built at run time so no credential-shaped literal is stored
            f.write("key " + "AKIA" + "Z" * 16 + "\n" + "-----BEGIN " + "RSA PRIVATE KEY-----\n")
        found, _, _ = scan([dirty], set())
        kinds = {x.split(": ", 1)[-1] for x in found}
        if not {"aws-access-key-id", "private-key-block"} <= kinds or any("AKIA" in x for x in found):
            print("SELF-TEST FAIL secret_scan.py: expected two findings without their text, got %s" % found)
            return 1
        print("SELF-TEST PASS secret_scan.py (python %s): %s" % (sys.version.split()[0], line))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--allow", action="append", default=[])
    ap.add_argument("--two-sided", metavar="SENTINEL")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.files:
        ap.print_usage(sys.stderr)
        return 2
    allow = set(a.allow)
    if a.two_sided:
        rc, line = two_sided(a.files, allow, a.two_sided)
        print(line)
        return rc
    found, files, lines = scan(a.files, allow)
    for x in found[:60]:
        print("FAIL secret_scan: " + x)
    if found:
        return 1
    print("PASS secret_scan: %d files, %d lines, %d patterns, 0 findings" % (files, lines, len(PATTERNS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
