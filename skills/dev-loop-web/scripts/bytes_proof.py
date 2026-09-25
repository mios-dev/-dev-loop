#!/usr/bin/env python3
"""Prove that bytes in hand are exactly the bytes a git host serves for a file, by recomputing
the git blob SHA-1 ("blob <size>\\0" + bytes) and comparing it with the SHA the host reported.
Offline; Python 3 standard library only; never touches the network. The proof holds however
the bytes reached this runner (fetched here, handed over as a file, or transcribed), which is
the point: the transfer path is not trusted, the recomputed hash is.

  python3 bytes_proof.py --contents-json API.json [--out FILE]
      API.json is a GitHub contents API or git blobs API response saved verbatim
      (repos/OWNER/REPO/contents/PATH?ref=SHA, or repos/OWNER/REPO/git/blobs/BLOB_SHA).
      Decodes the base64 `content`, recomputes the blob SHA, compares with `sha` and `size`.
      --out writes the decoded bytes only when the proof passes.
  python3 bytes_proof.py --file FILE --blob-sha SHA [--size N]
      Proves bytes obtained any other way (for example a raw URL) against a blob SHA taken
      from the contents API or a git tree listing.
  add --two-sided DEVLOOP-PLANTED-<ID> to either form: a copy with the sentinel appended must
      fail naming it, then the real bytes must pass.
  python3 bytes_proof.py --self-test

On a mismatch it names the likely channel alteration (trailing newline, CRLF, byte-order mark)
and shows the bytes beyond the expected size. Exit 0 = proven, 1 = not proven, 2 = usage.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
import sys

SENTINEL_RE = re.compile(r"^DEVLOOP-PLANTED-[A-Z0-9]+(-[A-Z0-9]+)*$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def blob_sha(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def show(data):
    # wide enough to carry a whole bundle-derived sentinel: a truncated plant is not a named plant
    return repr(bytes(data))[2:-1][:240]


TRANSFORMS = (
    ("a trailing newline was removed", lambda d: d + b"\n"),
    ("a trailing newline was added", lambda d: d[:-1] if d.endswith(b"\n") else None),
    ("CRLF line endings were introduced", lambda d: d.replace(b"\r\n", b"\n") if b"\r\n" in d else None),
    ("LF line endings were converted from CRLF", lambda d: d.replace(b"\n", b"\r\n") if b"\r\n" not in d else None),
    ("a byte-order mark was added", lambda d: d[3:] if d.startswith(b"\xef\xbb\xbf") else None),
)


def prove(data, want_sha, want_size=None):
    """Return (failures, byte_count)."""
    fails = []
    if not HEX40.match(want_sha or ""):
        return ["expected blob SHA %r is not 40 lowercase hex characters" % want_sha], 0
    if not data:
        return ["0 bytes: nothing to prove (an empty body is not the file)"], 0
    got = blob_sha(data)
    if got == want_sha and (want_size is None or want_size == len(data)):
        return [], len(data)
    msg = "MISMATCH: recomputed git blob %s != expected %s" % (got, want_sha)
    if want_size is not None and want_size != len(data):
        msg += "; %d bytes, expected %d (%+d)" % (len(data), want_size, len(data) - want_size)
        if len(data) > want_size:
            msg += "; bytes beyond the expected size: '%s'" % show(data[want_size:])
    for why, fn in TRANSFORMS:
        alt = fn(data)
        if alt is not None and blob_sha(alt) == want_sha:
            msg += "; the bytes match once undone: %s by the channel" % why
            break
    fails.append(msg)
    return fails, len(data)


def load_contents(path):
    with open(path, "rb") as f:
        doc = json.loads(f.read().decode("utf-8"))
    if not isinstance(doc, dict):
        raise ValueError("not a JSON object (a directory listing or an error page?)")
    if doc.get("type") not in (None, "file"):
        raise ValueError("type is %r, not a file" % doc.get("type"))
    if doc.get("encoding") != "base64":
        raise ValueError("encoding is %r, not base64 (files over 1 MB come back without inline content: "
                         "use the git blobs API with the blob SHA)" % doc.get("encoding"))
    content = doc.get("content") or ""
    try:
        data = base64.b64decode(re.sub(r"\s+", "", content), validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError("content is not valid base64: %s" % e)
    size = doc.get("size")
    return data, doc.get("sha"), size if isinstance(size, int) else None


def two_sided(data, sha, size, sentinel):
    if not SENTINEL_RE.match(sentinel):
        return 2, "sentinel must look like DEVLOOP-PLANTED-<ID> (uppercase, digits, hyphens)"
    if sentinel.encode("utf-8") in data:
        return 1, "FAIL two-sided bytes_proof: %s already occurs in the bytes; pick another" % sentinel
    pf, _ = prove(data + b"\n" + sentinel.encode("utf-8"), sha, size if size is not None else len(data))
    named = [x for x in pf if sentinel in x]
    if not named:
        return 1, "FAIL two-sided bytes_proof: the planted copy was not caught by name (%s)" % (pf[:1] or "passed")
    rf, n = prove(data, sha, size)
    if rf:
        return 1, "FAIL two-sided bytes_proof: plant caught, but the real bytes fail: %s" % rf[0]
    return 0, ("PASS two-sided bytes_proof: plant %s -> FAIL naming it (%s); real -> PASS (%d bytes, sha256 %s, git blob %s)"
               % (sentinel, named[0].split("; ")[-1], n, hashlib.sha256(data).hexdigest(), sha))


def self_test():
    # `printf 'hello\n' | git hash-object --stdin` -- an external value, not this script's own output
    if blob_sha(b"hello\n") != "ce013625030ba8dba906f756967f9e9ca394464a":
        print("SELF-TEST FAIL bytes_proof.py: the git blob formula disagrees with git hash-object")
        return 1
    data = b"# a contract\n\nline two\n"
    sha = blob_sha(data)
    rc, line = two_sided(data, sha, len(data), "DEVLOOP-PLANTED-SELFTEST")
    if rc != 0:
        print("SELF-TEST FAIL bytes_proof.py: " + line)
        return 1
    fails, _ = prove(data.rstrip(b"\n"), sha, len(data))
    if not (fails and "trailing newline was removed" in fails[0]):
        print("SELF-TEST FAIL bytes_proof.py: a stripped newline was not diagnosed: %s" % fails)
        return 1
    print("SELF-TEST PASS bytes_proof.py (python %s): %s" % (sys.version.split()[0], line))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--contents-json", metavar="API.json")
    ap.add_argument("--file")
    ap.add_argument("--blob-sha")
    ap.add_argument("--size", type=int)
    ap.add_argument("--out")
    ap.add_argument("--two-sided", metavar="SENTINEL")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.contents_json:
        try:
            data, sha, size = load_contents(a.contents_json)
        except (OSError, ValueError) as e:
            print("FAIL bytes_proof: %s: %s" % (a.contents_json, e))
            return 1
    elif a.file and a.blob_sha:
        with open(a.file, "rb") as f:
            data = f.read()
        sha, size = a.blob_sha, a.size
    else:
        ap.print_usage(sys.stderr)
        return 2
    if a.two_sided:
        rc, line = two_sided(data, sha, size, a.two_sided)
        print(line)
    else:
        fails, n = prove(data, sha, size)
        rc = 1 if fails else 0
        print(fails[0] if fails else "PASS bytes_proof: %d bytes, sha256 %s, git blob %s matches"
              % (n, hashlib.sha256(data).hexdigest(), sha))
    if rc == 0 and a.out:
        with open(a.out, "wb") as f:
            f.write(data)
    return rc


if __name__ == "__main__":
    sys.exit(main())
