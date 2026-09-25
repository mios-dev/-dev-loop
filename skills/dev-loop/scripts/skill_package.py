#!/usr/bin/env python3
"""Package a skill folder as an upload .zip for runtimes that take skills only by upload
(Gemini Spark: "a .zip containing SKILL.md in root folder", plain-text files only, no hidden
binaries such as .pyc or .DS_Store, 100 MB total) and gate the emitted package.

  python3 skill_package.py pack SKILL_DIR --out DIR/NAME.zip   build, gate, then move into place
  python3 skill_package.py check PACKAGE [--expect-name NAME]  gate a .zip or a skill folder

pack copies bytes verbatim (it never rewrites SKILL.md, so the gate sees exactly what ships),
leaves out __pycache__/, *.pyc, *.pyo and .DS_Store, writes a byte-reproducible zip (sorted
entries, fixed timestamps and modes), gates the result, and only then moves it to --out. A
package that fails the gate never lands. NAME must equal the folder name.

check fails, naming the offending key, file or count, on:
  - SKILL.md missing from the package root
  - a frontmatter key outside the portable Agent Skills subset (name, description, license,
    compatibility, metadata) -- harness extensions such as context, allowed-tools or
    argument-hint do not survive an upload
  - a name that is not lowercase-hyphen, is over 64 characters, or does not match its folder
    (the zip's stem, or the directory's name)
  - a description that is empty or over 1024 characters; a compatibility over 500
  - metadata that is not a flat map of quoted strings; an angle bracket in any value
  - a body of 500 lines or more
  - any file that is hidden, compiled (.pyc/.pyo, __pycache__), of a type outside the
    plain-text upload list, not UTF-8, or holding a NUL byte; a symlink; an unsafe path
  - a references/, scripts/ or assets/ path named in SKILL.md but absent from the package
  - a total over 100 MB
Exit 0 = uploadable, 1 = gate failed, 2 = usage. Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile

PORTABLE_KEYS = ("name", "description", "license", "compatibility", "metadata")
# Gemini Help 17094296 ("Supported file types"); plain text only.
TEXT_EXT = {".txt", ".md", ".rst", ".rtf", ".tex", ".log", ".py", ".sh", ".json", ".yaml", ".csv", ".toml",
            ".xml", ".env", ".sql", ".html", ".css", ".svg"}
TEXT_NAMES = {"Makefile", "Dockerfile"}
JUNK_DIRS = {"__pycache__"}
JUNK_FILES = {".DS_Store"}
JUNK_EXT = {".pyc", ".pyo"}
MAX_TOTAL = 100 * 1024 * 1024
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"(?<![\w/.\-])((?:references|scripts|assets)/[A-Za-z0-9_.\-/]*[A-Za-z0-9_])")
ZIP_DATE = (1980, 1, 1, 0, 0, 0)


# ---------------------------------------------------------------- frontmatter (no YAML library needed)
def split_frontmatter(text):
    """Return (frontmatter_lines, body) or raise ValueError."""
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md does not open with a '---' frontmatter line")
    m = re.search(r"\n---[ \t]*(\n|$)", text[3:])
    if not m:
        raise ValueError("SKILL.md frontmatter is never closed with '---'")
    return text[4:3 + m.start()].split("\n"), text[3 + m.end():]


def scalar(val, cont):
    if val in (">", ">-", ">+", "|", "|-", "|+"):
        parts = [c.strip() for c in cont if c.strip()]
        return (" " if val.startswith(">") else "\n").join(parts)
    if cont and any(c.strip() for c in cont):  # multi-line plain scalar
        val = " ".join([val] + [c.strip() for c in cont if c.strip()])
    if val.startswith('"'):
        try:
            return json.loads(val)
        except ValueError:
            return val.strip('"')
    if val.startswith("'") and val.endswith("'") and len(val) >= 2:
        return val[1:-1].replace("''", "'")
    return val


def parse_frontmatter(lines, fails):
    """Return {key: value}; value is a str, or a dict for a nested map. Appends to fails."""
    out, i = {}, 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip() or ln.lstrip().startswith("#"):
            i += 1
            continue
        if ln[0] in " \t":
            fails.append("frontmatter: line %d is indented with no key above it" % (i + 2))
            i += 1
            continue
        m = re.match(r"^([^:\s][^:]*?)\s*:(?:\s+(.*?))?\s*$", ln)
        if not m:
            fails.append("frontmatter: line %d is not 'key: value'" % (i + 2))
            i += 1
            continue
        key, val = m.group(1), (m.group(2) or "")
        j, cont = i + 1, []
        while j < len(lines) and (not lines[j].strip() or lines[j][0] in " \t"):
            cont.append(lines[j])
            j += 1
        if key in out:
            fails.append("frontmatter: key '%s' appears twice" % key)
        if val == "" and any(c.strip() for c in cont):
            sub = {}
            for c in cont:
                if not c.strip():
                    continue
                mm = re.match(r"^\s+([^:\s][^:]*?)\s*:\s+(.*?)\s*$", c)
                if not mm or re.match(r"^\s{4,}", c):
                    sub.setdefault("\0bad", []).append(c.strip())
                    continue
                sub[mm.group(1)] = mm.group(2)
            out[key] = sub
        else:
            out[key] = scalar(val, cont)
        i = j
    return out


# ---------------------------------------------------------------- package access
def load_zip(path, fails):
    entries = {}
    try:
        zf = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as e:
        fails.append("package: %s is not a readable zip (%s)" % (path, e))
        return entries
    with zf:
        for info in zf.infolist():
            name = info.filename
            if name.endswith("/"):
                continue
            if name.startswith("/") or "\\" in name or ".." in name.split("/"):
                fails.append("files: unsafe path %r in the zip" % name)
                continue
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                fails.append("files: %s is a symlink" % name)
                continue
            entries[name] = zf.read(info)
    return entries


def load_dir(path, fails):
    entries = {}
    for base, dirs, files in os.walk(path):
        dirs.sort()
        for n in sorted(files) + [d for d in dirs if os.path.islink(os.path.join(base, d))]:
            p = os.path.join(base, n)
            rel = os.path.relpath(p, path).replace(os.sep, "/")
            if os.path.islink(p):
                fails.append("files: %s is a symlink" % rel)
                continue
            with open(p, "rb") as f:
                entries[rel] = f.read()
    return entries


# ---------------------------------------------------------------- the gate
def gate(entries, expect_name, fails):
    """Append failures; return a summary dict."""
    info = {"files": len(entries), "bytes": sum(len(v) for v in entries.values())}
    if not entries:
        fails.append("package: empty -- no files at all")
        return info
    for rel in sorted(entries):
        parts = rel.split("/")
        base = parts[-1]
        ext = os.path.splitext(base)[1].lower()
        if ext in JUNK_EXT or any(p in JUNK_DIRS for p in parts):
            fails.append("files: %s is compiled Python bytecode (%s) -- a hidden binary; uploads refuse it"
                         % (rel, ext or "__pycache__"))
            continue
        if any(p.startswith(".") for p in parts):
            fails.append("files: %s is a hidden file%s" % (rel, " (.DS_Store)" if base in JUNK_FILES else ""))
            continue
        if ext not in TEXT_EXT and base not in TEXT_NAMES:
            fails.append("files: %s has type %r, outside the plain-text upload list" % (rel, ext or base))
            continue
        data = entries[rel]
        if b"\0" in data:
            fails.append("files: %s is not plain text (NUL byte at offset %d)" % (rel, data.index(b"\0")))
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as e:
            fails.append("files: %s is not plain text (not UTF-8 at byte %d)" % (rel, e.start))
    if info["bytes"] > MAX_TOTAL:
        fails.append("size: %d bytes in total, over the 100 MB upload limit" % info["bytes"])
    if "SKILL.md" not in entries:
        nested = sorted(k for k in entries if k.endswith("/SKILL.md"))
        fails.append("layout: SKILL.md is not at the package root%s"
                     % (" (found %s: zip the folder's contents, not the folder)" % nested[0] if nested else ""))
        return info
    try:
        text = entries["SKILL.md"].decode("utf-8")
        fm_lines, body = split_frontmatter(text)
    except (UnicodeDecodeError, ValueError) as e:
        fails.append("frontmatter: %s" % e)
        return info
    fm = parse_frontmatter(fm_lines, fails)
    for k in fm:
        if k not in PORTABLE_KEYS:
            fails.append("keys: non-portable frontmatter key '%s' (allowed: %s)" % (k, ", ".join(PORTABLE_KEYS)))
    name = fm.get("name")
    if not isinstance(name, str) or not name:
        fails.append("name: missing")
    else:
        if not NAME_RE.match(name) or len(name) > 64:
            fails.append("name: '%s' is not 1-64 lowercase letters, digits and single hyphens" % name)
        if expect_name is not None and name != expect_name:
            fails.append("name: '%s' does not match its folder '%s'" % (name, expect_name))
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        fails.append("description: missing or empty")
    else:
        info["description"] = len(desc)
        if len(desc) > 1024:
            fails.append("description: %d characters (limit 1024)" % len(desc))
    comp = fm.get("compatibility")
    if comp is not None:
        if not isinstance(comp, str) or not comp.strip():
            fails.append("compatibility: present but not a non-empty string")
        elif len(comp) > 500:
            fails.append("compatibility: %d characters (limit 500)" % len(comp))
    lic = fm.get("license")
    if lic is not None and (not isinstance(lic, str) or not lic.strip()):
        fails.append("license: present but not a non-empty string")
    meta = fm.get("metadata")
    if meta is not None:
        if not isinstance(meta, dict):
            fails.append("metadata: not a map of string keys to string values")
        else:
            for bad in meta.pop("\0bad", []):
                fails.append("metadata: '%s' is not a flat 'key: \"value\"' entry" % bad)
            for k, v in meta.items():
                if not (len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'"):
                    fails.append("metadata: '%s' value %s is not a quoted string" % (k, v))
    for k, v in fm.items():
        vals = list(v.items()) if isinstance(v, dict) else [(k, v)]
        for kk, vv in vals:
            if any(c in str(kk) + str(vv) for c in "<>"):
                fails.append("frontmatter: angle bracket in '%s' (it can inject into a host's system prompt)" % kk)
    lines = len(body.splitlines())
    info["body_lines"] = lines
    if lines >= 500:
        fails.append("body: %d lines (limit: under 500)" % lines)
    for ref in sorted(set(LINK_RE.findall(body))):
        if ref not in entries and not any(k.startswith(ref.rstrip("/") + "/") for k in entries):
            fails.append("links: SKILL.md names %s, which is not in the package" % ref)
    info["name"] = name
    return info


def check(path, expect_name=None):
    """Return (failures, info)."""
    fails = []
    if os.path.isdir(path):
        entries = load_dir(path, fails)
        default = os.path.basename(os.path.normpath(path))
    else:
        entries = load_zip(path, fails)
        default = os.path.splitext(os.path.basename(path))[0]
    info = gate(entries, expect_name if expect_name is not None else default, fails)
    return fails, info


def report(path, fails, info):
    for f in fails:
        print("FAIL %s" % f)
    if fails:
        print("== skill package %s: NOT uploadable (%d failure(s))" % (path, len(fails)))
        return 1
    print("PASS skill package %s: name %s, %d files, %d bytes, description %d/1024 chars, body %d lines (limit: under 500)"
          % (path, info.get("name"), info["files"], info["bytes"], info.get("description", 0), info.get("body_lines", 0)))
    return 0


# ---------------------------------------------------------------- pack
def collect(src):
    out, errs = {}, []
    for base, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if d not in JUNK_DIRS)
        for n in sorted(files):
            if n in JUNK_FILES or os.path.splitext(n)[1].lower() in JUNK_EXT:
                continue
            p = os.path.join(base, n)
            rel = os.path.relpath(p, src).replace(os.sep, "/")
            if os.path.islink(p):
                errs.append("files: %s is a symlink; refusing to pack it" % rel)
                continue
            with open(p, "rb") as f:
                out[rel] = f.read()
    return out, errs


def write_zip(entries, path):
    with zipfile.ZipFile(path, "w") as zf:
        for rel in sorted(entries):
            zi = zipfile.ZipInfo(rel, date_time=ZIP_DATE)
            zi.create_system = 3
            zi.external_attr = 0o100644 << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, entries[rel], compresslevel=9)


def pack(src, out):
    src = os.path.normpath(src)
    folder = os.path.basename(src)
    if not os.path.isfile(os.path.join(src, "SKILL.md")):
        print("usage: %s has no SKILL.md" % src, file=sys.stderr)
        return 2
    if os.path.basename(out) != folder + ".zip":
        print("usage: --out must be named %s.zip so the package keeps its folder name" % folder, file=sys.stderr)
        return 2
    entries, errs = collect(src)
    for e in errs:
        print("FAIL %s" % e)
    if errs:
        return 1
    parent = os.path.dirname(os.path.abspath(out))
    os.makedirs(parent, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".%s." % folder, suffix=".zip", dir=parent)
    os.close(fd)
    try:
        write_zip(entries, tmp)
        fails, info = check(tmp, expect_name=folder)
        if report(out, fails, info):
            return 1
        os.chmod(tmp, 0o644)  # mkstemp creates 0600; the package is an ordinary file the operator uploads
        os.replace(tmp, out)
        tmp = None
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
    with open(out, "rb") as f:
        data = f.read()
    print("wrote %s: %d bytes, sha256 %s, %d entries (SKILL.md at the root)"
          % (out, len(data), hashlib.sha256(data).hexdigest(), len(entries)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("pack")
    p.add_argument("skill_dir")
    p.add_argument("--out", required=True)
    c = sp.add_parser("check")
    c.add_argument("package")
    c.add_argument("--expect-name")
    a = ap.parse_args(argv)
    if a.cmd == "pack":
        return pack(a.skill_dir, a.out)
    if not os.path.exists(a.package):
        print("usage: %s does not exist" % a.package, file=sys.stderr)
        return 2
    fails, info = check(a.package, a.expect_name)
    return report(a.package, fails, info)


if __name__ == "__main__":
    sys.exit(main())
