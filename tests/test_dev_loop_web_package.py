#!/usr/bin/env python3
"""
Controls for the dev-loop-web upload package and its gate (skills/dev-loop/scripts/skill_package.py).

Gemini Spark takes a skill only as an uploaded SKILL.md or a .zip with SKILL.md at its root, plain
text only (a stray .pyc can fail the upload), and nothing here can run a live Spark. So the gate
is static, and this suite proves it both ways:

  POSITIVE  the real skill packs, the emitted zip passes, and two packs are byte-identical.
  NEGATIVE  each violation is planted into a COPY of the emitted package (a package fixture, not a
            harness fake), grepped back out to prove it landed, and must then fail by name:
            non-portable key, description > 1024, body >= 500 lines, .pyc (inside and outside
            __pycache__), non-plain-text type, NUL bytes, hidden file, name != folder (in
            SKILL.md and by zip name), SKILL.md not at the root, angle bracket, unquoted metadata,
            a references/ or scripts/ path that is not in the package.
  BOUNDARY  description of exactly 1024 and a body of exactly 499 lines still pass.
  PACK      junk (__pycache__, .pyc, .DS_Store) is left out, and a package that fails the gate
            never lands at --out.
  SCRIPTS   every bundled script's --self-test passes (each plants its own violation), and the
            two-sided harness refuses a sentinel already present in the input.
  VALUES    SKILL.md and references/ carry no project values (the fetched contract carries them).

Run: python3 tests/test_dev_loop_web_package.py
"""
from __future__ import annotations

import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "dev-loop-web"
TOOL = ROOT / "skills" / "dev-loop" / "scripts" / "skill_package.py"
FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        FAILURES.append(name)


def run(*args: str) -> tuple[int, str]:
    cp = subprocess.run([sys.executable, *args], capture_output=True, text=True, timeout=120)
    return cp.returncode, cp.stdout + cp.stderr


def read_zip(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as zf:
        return {i.filename: zf.read(i) for i in zf.infolist() if not i.filename.endswith("/")}


def write_zip(path: Path, entries: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for k in sorted(entries):
            zf.writestr(k, entries[k])


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frontmatter_replace(skill_md: bytes, old: str, new: str) -> bytes:
    s = skill_md.decode("utf-8")
    assert old in s, f"fixture drift: {old!r} not in SKILL.md"
    return s.replace(old, new, 1).encode("utf-8")


def test_corpus(tmp: Path) -> Path:
    """Empty-Set Pass guard, then the positive control."""
    print("corpus + positive control:")
    check("SKILL.md exists", (SKILL / "SKILL.md").is_file())
    refs = sorted((SKILL / "references").glob("*.md"))
    scripts = sorted((SKILL / "scripts").glob("*.py"))
    check("references/ is non-empty", len(refs) >= 3, f"{[p.name for p in refs]}")
    check("scripts/ is non-empty", len(scripts) >= 6, f"{[p.name for p in scripts]}")
    a, b = tmp / "a" / "dev-loop-web.zip", tmp / "b" / "dev-loop-web.zip"
    rc, out = run(str(TOOL), "pack", str(SKILL), "--out", str(a))
    check("pack of the real skill exits 0", rc == 0, out[-400:])
    rc2, _ = run(str(TOOL), "pack", str(SKILL), "--out", str(b))
    check("second pack exits 0", rc2 == 0)
    check("two packs are byte-identical (idempotence)", a.is_file() and b.is_file() and sha(a) == sha(b))
    rc, out = run(str(TOOL), "check", str(a))
    check("check of the emitted zip exits 0", rc == 0, out[-400:])
    check("PASS line states name and body budget", "PASS skill package" in out and "name dev-loop-web" in out, out[-300:])
    ent = read_zip(a)
    check("SKILL.md is at the zip root", "SKILL.md" in ent, f"{sorted(ent)[:5]}")
    check("no compiled or hidden entry in the zip",
          not any(k.endswith((".pyc", ".pyo")) or "__pycache__" in k or "/." in "/" + k for k in ent), f"{sorted(ent)}")
    check("every referenced file shipped", {f"references/{p.name}" for p in refs} | {f"scripts/{p.name}" for p in scripts} <= set(ent))
    return a


PLANTS = [
    # (id, mutate(entries) -> entries, grep-back (entry, bytes-or-None), expected failure text)
    ("claude-only key", lambda e: {**e, "SKILL.md": frontmatter_replace(e["SKILL.md"], "license: MIT\n", "license: MIT\ncontext: fork\n")},
     ("SKILL.md", b"\ncontext: fork\n"), "non-portable frontmatter key 'context'"),
    ("allowed-tools key", lambda e: {**e, "SKILL.md": frontmatter_replace(e["SKILL.md"], "license: MIT\n", "license: MIT\nallowed-tools: Read\n")},
     ("SKILL.md", b"\nallowed-tools: Read\n"), "non-portable frontmatter key 'allowed-tools'"),
    ("description 1025", None, None, "description: 1025 characters (limit 1024)"),
    ("body 500 lines", None, None, "body: 500 lines (limit: under 500)"),
    ("pyc in __pycache__", lambda e: {**e, "scripts/__pycache__/digest.cpython-311.pyc": b"\xa7\r\r\n" + bytes(12)},
     ("scripts/__pycache__/digest.cpython-311.pyc", None), "scripts/__pycache__/digest.cpython-311.pyc is compiled Python bytecode (.pyc)"),
    ("bare pyc", lambda e: {**e, "scripts/DEVLOOP-PLANTED-PYC.pyc": b"\xa7\r\r\n" + bytes(12)},
     ("scripts/DEVLOOP-PLANTED-PYC.pyc", None), "scripts/DEVLOOP-PLANTED-PYC.pyc is compiled Python bytecode (.pyc)"),
    ("binary type", lambda e: {**e, "assets/DEVLOOP-PLANTED-BIN.png": b"\x89PNG\r\n\x1a\n" + bytes(8)},
     ("assets/DEVLOOP-PLANTED-BIN.png", None), "assets/DEVLOOP-PLANTED-BIN.png has type '.png', outside the plain-text upload list"),
    ("text in a type off the list", lambda e: {**e, "scripts/DEVLOOP-PLANTED-TYPE.js": b"console.log('valid UTF-8, wrong type')\n"},
     ("scripts/DEVLOOP-PLANTED-TYPE.js", b"console.log"), "scripts/DEVLOOP-PLANTED-TYPE.js has type '.js', outside the plain-text upload list"),
    ("NUL in a .txt",lambda e: {**e, "references/DEVLOOP-PLANTED-NUL.txt": b"plain\0text\n"},
     ("references/DEVLOOP-PLANTED-NUL.txt", b"\0"), "references/DEVLOOP-PLANTED-NUL.txt is not plain text (NUL byte"),
    ("hidden .DS_Store", lambda e: {**e, ".DS_Store": b"\0\0\0\x01Bud1"},
     (".DS_Store", None), ".DS_Store is a hidden file (.DS_Store)"),
    ("hidden plain-text file", lambda e: {**e, "references/.DEVLOOP-PLANTED-HIDDEN.md": b"# plain text, allowed type, hidden name\n"},
     ("references/.DEVLOOP-PLANTED-HIDDEN.md", b"hidden name"), "references/.DEVLOOP-PLANTED-HIDDEN.md is a hidden file"),
    ("name != folder",lambda e: {**e, "SKILL.md": frontmatter_replace(e["SKILL.md"], "name: dev-loop-web\n", "name: dev-loop-webx\n")},
     ("SKILL.md", b"name: dev-loop-webx\n"), "name: 'dev-loop-webx' does not match its folder 'dev-loop-web'"),
    ("SKILL.md nested", lambda e: {f"dev-loop-web/{k}": v for k, v in e.items()},
     ("dev-loop-web/SKILL.md", None), "SKILL.md is not at the package root (found dev-loop-web/SKILL.md"),
    ("angle bracket", lambda e: {**e, "SKILL.md": frontmatter_replace(e["SKILL.md"], "Use when a task", "Use when <b>a task")},
     ("SKILL.md", b"<b>a task"), "angle bracket in 'description'"),
    ("unquoted metadata", lambda e: {**e, "SKILL.md": frontmatter_replace(e["SKILL.md"], 'version: "0.1.0"', "version: 0.1.0")},
     ("SKILL.md", b"  version: 0.1.0\n"), "metadata: 'version' value 0.1.0 is not a quoted string"),
    ("missing referenced file", lambda e: {**e, "SKILL.md": e["SKILL.md"] + b"\nSee `scripts/devloop_planted_missing.py`.\n"},
     ("SKILL.md", b"scripts/devloop_planted_missing.py"), "links: SKILL.md names scripts/devloop_planted_missing.py"),
]


def desc_of_len(e: dict[str, bytes], n: int) -> dict[str, bytes]:
    s = e["SKILL.md"].decode("utf-8")
    m = re.search(r"^description: (.*)$", s, re.M)
    head = "Plants DEVLOOP-PLANTED-DESC. "
    new = (head + "x" * n)[:n]
    return {**e, "SKILL.md": (s[:m.start(1)] + new + s[m.end(1):]).encode("utf-8")}


def body_of_lines(e: dict[str, bytes], n: int) -> dict[str, bytes]:
    s = e["SKILL.md"].decode("utf-8")
    end = s.index("\n---\n", 3) + len("\n---\n")
    body = s[end:].splitlines()
    pad = [f"DEVLOOP-PLANTED-BODY {i}" for i in range(n - len(body))]
    return {**e, "SKILL.md": (s[:end] + "\n".join(body + pad) + "\n").encode("utf-8")}


def test_plants(clean: Path, tmp: Path) -> None:
    print("negative controls (each plant into a copy of the emitted package, grepped back, then must fail by name):")
    base = read_zip(clean)
    for pid, mutate, grep, expect in PLANTS:
        if pid == "description 1025":
            ent, grep = desc_of_len(base, 1025), ("SKILL.md", b"DEVLOOP-PLANTED-DESC")
        elif pid == "body 500 lines":
            ent, grep = body_of_lines(base, 500), ("SKILL.md", b"DEVLOOP-PLANTED-BODY")
        else:
            ent = mutate(dict(base))
        z = tmp / "plants" / re.sub(r"[^a-z0-9]+", "-", pid) / "dev-loop-web.zip"
        z.parent.mkdir(parents=True, exist_ok=True)
        write_zip(z, ent)
        landed = read_zip(z)
        entry, needle = grep
        check(f"[{pid}] plant landed", entry in landed and (needle is None or needle in landed[entry]),
              f"{entry} / {needle!r} not found in the planted zip")
        rc, out = run(str(TOOL), "check", str(z))
        check(f"[{pid}] gate fails (rc 1)", rc == 1, f"rc={rc} {out[-300:]}")
        check(f"[{pid}] failure names the plant", expect in out, f"expected {expect!r} in:\n{out[-600:]}")
    z = tmp / "plants" / "renamed" / "devloop-planted-name.zip"
    z.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(clean, z)
    rc, out = run(str(TOOL), "check", str(z))
    check("[zip renamed] gate fails naming the folder", rc == 1 and "does not match its folder 'devloop-planted-name'" in out, out[-300:])


def test_boundaries(clean: Path, tmp: Path) -> None:
    print("boundaries (the limits are exact, not off by one):")
    base = read_zip(clean)
    for label, ent in (("description of exactly 1024 passes", desc_of_len(base, 1024)),
                       ("body of exactly 499 lines passes", body_of_lines(base, 499))):
        z = tmp / "edge" / re.sub(r"[^a-z0-9]+", "-", label) / "dev-loop-web.zip"
        z.parent.mkdir(parents=True, exist_ok=True)
        write_zip(z, ent)
        rc, out = run(str(TOOL), "check", str(z))
        check(label, rc == 0, out[-400:])
    try:
        import yaml  # optional cross-check: the gate's own parser must measure what a YAML parser measures
        s = (SKILL / "SKILL.md").read_text("utf-8")
        fm = yaml.safe_load(s.split("---")[1])
        rc, out = run(str(TOOL), "check", str(clean))
        check("gate's description length equals PyYAML's", f"description {len(fm['description'])}/1024" in out, out[-300:])
    except ImportError:
        print("  skip gate/PyYAML cross-check (PyYAML not installed)")


def test_pack_behaviour(tmp: Path) -> None:
    print("pack: junk left out, a failing package never lands:")
    src = tmp / "src" / "dev-loop-web"
    shutil.copytree(SKILL, src)
    (src / "scripts" / "__pycache__").mkdir(exist_ok=True)
    (src / "scripts" / "__pycache__" / "x.cpython-311.pyc").write_bytes(b"\xa7\r\r\n")
    (src / ".DS_Store").write_bytes(b"\0\0\0\x01Bud1")
    out_zip = tmp / "packjunk" / "dev-loop-web.zip"
    rc, out = run(str(TOOL), "pack", str(src), "--out", str(out_zip))
    ent = read_zip(out_zip) if out_zip.is_file() else {}
    check("pack with junk in the source still exits 0", rc == 0, out[-300:])
    check("junk is not in the zip", ent and not any("__pycache__" in k or k.endswith(".pyc") or ".DS_Store" in k for k in ent), f"{sorted(ent)}")
    skill_md = src / "SKILL.md"
    skill_md.write_bytes(frontmatter_replace(skill_md.read_bytes(), "license: MIT\n", "license: MIT\nargument-hint: x\n"))
    bad_zip = tmp / "packbad" / "dev-loop-web.zip"
    rc, out = run(str(TOOL), "pack", str(src), "--out", str(bad_zip))
    check("pack of a non-portable skill exits 1 naming the key", rc == 1 and "'argument-hint'" in out, out[-300:])
    check("the failing package did not land at --out", not bad_zip.exists())
    check("no temp file left beside --out", not any(bad_zip.parent.glob(".dev-loop-web.*")))


def test_scripts() -> None:
    print("bundled scripts (each self-test plants its own violation and requires it caught by name):")
    names = sorted(p.name for p in (SKILL / "scripts").glob("*.py"))
    check("six scripts found", len(names) == 6, f"{names}")
    for n in names:
        rc, out = run(str(SKILL / "scripts" / n), "--self-test")
        check(f"{n} --self-test", rc == 0 and out.startswith("SELF-TEST PASS") and "DEVLOOP-PLANTED-SELFTEST" in out, out[-400:])
    tmp = Path(tempfile.mkdtemp(prefix="dlw-sent-"))
    try:
        for side in ("a", "b"):
            (tmp / side).mkdir()
            (tmp / side / "f.txt").write_text("DEVLOOP-PLANTED-TAKEN\n")
        rc, out = run(str(SKILL / "scripts" / "digest.py"), "--compare", str(tmp / "a"), str(tmp / "b"),
                      "--two-sided", "DEVLOOP-PLANTED-TAKEN")
        check("a sentinel already in the input is refused (self-certifying guard)", rc == 1 and "already occurs" in out, out[-300:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_no_project_values() -> None:
    """The skill is the HOW; the contract fetched on each run carries the values. A project name or a
    verdict word in the skill text is a second copy of the contract that nothing would keep in sync."""
    print("no project values in the skill text:")
    # project name in any case; verdict words only as the contract spells them (upper case) --
    # lower-case "rejected" is a preference-data key and "accepted" is ordinary prose
    rx = re.compile(r"(?i:\bmios\b)|\b(?:SUBMITTED|REJECTED|BLOCKED|ACCEPTED)\b|VERDICT:")
    planted = "DEVLOOP-PLANTED-VALUES: end with VERDICT: SUBMITTED for the MiOS task"
    check("detector catches a planted project value", sorted(set(rx.findall(planted))) == ["MiOS", "SUBMITTED", "VERDICT:"],
          f"{rx.findall(planted)}")
    texts = {p.relative_to(SKILL).as_posix(): p.read_text("utf-8") for p in [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*"))]}
    check("skill text found", len(texts) >= 4)
    for rel, t in texts.items():
        hits = sorted(set(rx.findall(t)))
        check(f"{rel} carries no project name or verdict word", not hits, f"{hits}")


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="dlw-pkg-"))
    try:
        clean = test_corpus(tmp)
        if clean.is_file():
            test_plants(clean, tmp)
            test_boundaries(clean, tmp)
        test_pack_behaviour(tmp)
        test_scripts()
        test_no_project_values()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): {', '.join(FAILURES)}")
        return 1
    print("all dev-loop-web package controls passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
