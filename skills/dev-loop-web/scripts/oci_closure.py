#!/usr/bin/env python3
"""Check (and optionally build) an OCI image layout shipped as a tar. Offline; Python 3 standard
library only; never touches the network. Values such as the ref name, the revision annotation,
the layer path prefix and the files a layer must hold are arguments copied from the contract.

  python3 oci_closure.py check LAYOUT.tar [--layout-version 1.0.0] [--ref-name NAME]
        [--revision SHA] [--layer-contains PATH ...] [--two-sided DEVLOOP-PLANTED-<ID>]
  python3 oci_closure.py build --out LAYOUT.tar --layer-root PREFIX/ --ref-name NAME
        [--revision SHA] [--annotation KEY=VALUE ...] FILE [FILE ...]
  python3 oci_closure.py --self-test

check: the tar is uncompressed; `oci-layout` equals {"imageLayoutVersion": VERSION}; `index.json`
has schemaVersion 2 and at least one descriptor; every descriptor (index -> image manifest ->
config + every layer) resolves to a blob in the same tar whose byte count equals `size` and whose
sha256 equals `digest`; the config's rootfs.diff_ids equal the uncompressed layer digests.
Index-only, sparse or externally fulfilled layouts fail. A nested image index is reported as
unsupported rather than passed.
build: one uncompressed layer holding FILEs under PREFIX, a minimal config, one image manifest,
an index, and the layout, all as a deterministic tar (sorted members, mtime 0, uid/gid 0, fixed
modes, compact sorted JSON) so two builds of the same inputs are byte-identical.
--two-sided adds an index descriptor whose ref name is the sentinel and whose blob is absent to
a copy, requires a failure naming it, then requires the real tar to pass. Exit 0/1/2.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile

SENTINEL_RE = re.compile(r"^DEVLOOP-PLANTED-[A-Z0-9]+(-[A-Z0-9]+)*$")
DIGEST_RE = re.compile(r"^sha256:([0-9a-f]{64})$")
MT_INDEX = "application/vnd.oci.image.index.v1+json"
MT_MANIFEST = "application/vnd.oci.image.manifest.v1+json"
MT_CONFIG = "application/vnd.oci.image.config.v1+json"
MT_LAYER = "application/vnd.oci.image.layer.v1.tar"
MT_LAYER_GZ = "application/vnd.oci.image.layer.v1.tar+gzip"
REF = "org.opencontainers.image.ref.name"
REV = "org.opencontainers.image.revision"
MAGIC = ((b"\x1f\x8b", "gzip"), (b"BZh", "bzip2"), (b"\xfd7zXZ\x00", "xz"), (b"\x28\xb5\x2f\xfd", "zstd"))


def cjson(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def norm(name):
    while name.startswith("./"):
        name = name[2:]
    return name


def label(where, desc):
    ann = desc.get("annotations") if isinstance(desc.get("annotations"), dict) else {}
    return "%s ref=%s" % (where, ann[REF]) if ann.get(REF) else where


def check(path, o):
    """Return (failures, descriptors_verified, summary)."""
    fails = []
    try:
        with open(path, "rb") as f:
            head = f.read(8)
    except OSError as e:
        return ["cannot read: %s" % e], 0, ""
    for magic, kind in MAGIC:
        if head.startswith(magic):
            return ["compressed (%s): the layout tar must be uncompressed" % kind], 0, ""
    try:
        tf = tarfile.open(path, mode="r:")
    except tarfile.TarError as e:
        return ["not a tar: %s" % e], 0, ""
    with tf:
        files = {}
        for m in tf.getmembers():
            n = norm(m.name)
            if n.startswith("/") or ".." in n.split("/"):
                fails.append("unsafe member path %s" % m.name)
            if m.issym() or m.islnk():
                fails.append("link member %s: blobs must be regular files" % m.name)
            elif m.isfile():
                files[n] = tf.extractfile(m).read()
    count = [0]
    used = set()

    def blob(desc, where):
        if not isinstance(desc, dict):
            fails.append("%s: descriptor is not an object" % where)
            return None
        where = label(where, desc)
        m = DIGEST_RE.match(str(desc.get("digest", "")))
        size = desc.get("size")
        if not m or not isinstance(size, int) or isinstance(size, bool):
            fails.append("%s: digest %r or size %r malformed" % (where, desc.get("digest"), size))
            return None
        p = "blobs/sha256/" + m.group(1)
        if p not in files:
            fails.append("%s: blob %s missing from the tar" % (where, p))
            return None
        data = files[p]
        if len(data) != size:
            fails.append("%s: blob %s is %d bytes, descriptor says %d" % (where, p, len(data), size))
        if sha(data) != m.group(1):
            fails.append("%s: blob %s hashes to sha256:%s, not its digest" % (where, p, sha(data)))
        count[0] += 1
        used.add(p)
        return data

    def load(data, where):
        try:
            return json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as e:
            fails.append("%s: not JSON (%s)" % (where, e))
            return None

    if "oci-layout" not in files:
        fails.append("oci-layout missing")
    else:
        lay = load(files["oci-layout"], "oci-layout")
        if lay is not None and lay != {"imageLayoutVersion": o.layout_version}:
            fails.append("oci-layout is %s, not {\"imageLayoutVersion\":\"%s\"}" % (json.dumps(lay), o.layout_version))
    idx = load(files["index.json"], "index.json") if "index.json" in files else None
    if "index.json" not in files:
        fails.append("index.json missing")
    manifests = []
    if isinstance(idx, dict):
        if idx.get("schemaVersion") != 2:
            fails.append("index.json schemaVersion is %r, not 2" % idx.get("schemaVersion"))
        descs = idx.get("manifests")
        if not isinstance(descs, list) or not descs:
            fails.append("index.json has no manifests: an index-only layout ships nothing")
            descs = []
        refs = []
        for i, d in enumerate(descs):
            where = "index.manifests[%d]" % i
            if isinstance(d, dict) and isinstance(d.get("annotations"), dict):
                refs.append(d["annotations"].get(REF))
            if isinstance(d, dict) and d.get("mediaType") == MT_INDEX:
                fails.append("%s: nested image index is not supported by this checker" % label(where, d))
                continue
            if isinstance(d, dict) and d.get("mediaType") != MT_MANIFEST:
                fails.append("%s: mediaType %r is not an image manifest" % (label(where, d), d.get("mediaType")))
            data = blob(d, where)
            if data is not None:
                man = load(data, where)
                if isinstance(man, dict):
                    manifests.append((label(where, d), man))
        if o.ref_name is not None and o.ref_name not in refs:
            fails.append("no index descriptor carries %s=%s" % (REF, o.ref_name))
    elif idx is not None:
        fails.append("index.json is not an object")
    layer_members = set()
    for where, man in manifests:
        if man.get("schemaVersion") != 2:
            fails.append("%s manifest: schemaVersion %r, not 2" % (where, man.get("schemaVersion")))
        if man.get("mediaType") not in (None, MT_MANIFEST):
            fails.append("%s manifest: mediaType %r" % (where, man.get("mediaType")))
        ann = man.get("annotations") if isinstance(man.get("annotations"), dict) else {}
        if o.revision is not None and ann.get(REV) != o.revision:
            fails.append("%s manifest: %s is %r, not %s" % (where, REV, ann.get(REV), o.revision))
        cfg_d = man.get("config")
        if not isinstance(cfg_d, dict) or cfg_d.get("mediaType") != MT_CONFIG:
            fails.append("%s config: mediaType is not %s" % (where, MT_CONFIG))
        cfg_data = blob(cfg_d, where + " config")
        cfg = load(cfg_data, where + " config") if cfg_data is not None else None
        layers = man.get("layers")
        if not isinstance(layers, list) or not layers:
            fails.append("%s manifest: no layers" % where)
            layers = []
        diff_ids = []
        for j, ld in enumerate(layers):
            lw = "%s layers[%d]" % (where, j)
            mt = ld.get("mediaType") if isinstance(ld, dict) else None
            if mt not in (MT_LAYER, MT_LAYER_GZ):
                fails.append("%s: mediaType %r is not an OCI tar layer" % (lw, mt))
            data = blob(ld, lw)
            if data is None:
                continue
            try:
                raw = gzip.decompress(data) if mt == MT_LAYER_GZ else data
                diff_ids.append("sha256:" + sha(raw))
                with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as lt:
                    layer_members.update(norm(m.name) for m in lt.getmembers() if m.isfile())
            except (OSError, tarfile.TarError, EOFError) as e:
                fails.append("%s: not a readable tar layer (%s)" % (lw, e))
        if isinstance(cfg, dict):
            rootfs = cfg.get("rootfs") if isinstance(cfg.get("rootfs"), dict) else {}
            if rootfs.get("type") != "layers" or rootfs.get("diff_ids") != diff_ids:
                fails.append("%s config: rootfs.diff_ids %s != layer digests %s" % (where, rootfs.get("diff_ids"), diff_ids))
    for p in o.layer_contains:
        if norm(p) not in layer_members:
            fails.append("no layer holds %s" % p)
    if count[0] == 0:
        fails.append("empty set: 0 descriptors verified")
    blobs = len([k for k in files if k.startswith("blobs/")])
    return fails, count[0], "%d descriptors resolved (%d blobs in the tar, %d unreferenced), %d layer files" % (
        count[0], blobs, blobs - len(used), len(layer_members))


def tar_bytes(entries):
    """entries: {path: bytes}; directories implied. Deterministic uncompressed tar."""
    buf = io.BytesIO()
    dirs = set()
    for p in entries:
        parts = p.split("/")[:-1]
        for k in range(1, len(parts) + 1):
            dirs.add("/".join(parts[:k]))
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for name in sorted(set(entries) | dirs):
            ti = tarfile.TarInfo(name)
            ti.mtime, ti.uid, ti.gid, ti.uname, ti.gname = 0, 0, 0, "", ""
            if name in entries:
                ti.type, ti.mode, ti.size = tarfile.REGTYPE, 0o644, len(entries[name])
                tf.addfile(ti, io.BytesIO(entries[name]))
            else:
                ti.type, ti.mode = tarfile.DIRTYPE, 0o755
                tf.addfile(ti)
    return buf.getvalue()


def build(files, layer_root, ref_name, revision=None, annotations=None, layout_version="1.0.0"):
    root = layer_root.strip("/")
    payload = {}
    for p in files:
        with open(p, "rb") as f:
            payload[(root + "/" if root else "") + os.path.basename(p)] = f.read()
    layer = tar_bytes(payload)
    config = cjson({"architecture": "amd64", "os": "linux",
                    "rootfs": {"type": "layers", "diff_ids": ["sha256:" + sha(layer)]}})
    man_ann = dict(annotations or {})
    if revision is not None:
        man_ann[REV] = revision
    manifest = {"schemaVersion": 2, "mediaType": MT_MANIFEST,
                "config": {"mediaType": MT_CONFIG, "digest": "sha256:" + sha(config), "size": len(config)},
                "layers": [{"mediaType": MT_LAYER, "digest": "sha256:" + sha(layer), "size": len(layer)}]}
    if man_ann:
        manifest["annotations"] = man_ann
    mb = cjson(manifest)
    index = cjson({"schemaVersion": 2, "mediaType": MT_INDEX,
                   "manifests": [{"mediaType": MT_MANIFEST, "digest": "sha256:" + sha(mb), "size": len(mb),
                                  "annotations": {REF: ref_name}}]})
    out = {"oci-layout": cjson({"imageLayoutVersion": layout_version}), "index.json": index}
    for b in (layer, config, mb):
        out["blobs/sha256/" + sha(b)] = b
    return tar_bytes(out)


def two_sided(path, o, sentinel):
    if not SENTINEL_RE.match(sentinel):
        return 2, "sentinel must look like DEVLOOP-PLANTED-<ID> (uppercase, digits, hyphens)"
    with open(path, "rb") as f:
        raw = f.read()
    if sentinel.encode("utf-8") in raw:
        return 1, "FAIL two-sided oci_closure: %s already occurs in the tar; pick another" % sentinel
    try:
        with tarfile.open(path, mode="r:") as tf:
            entries = {norm(m.name): tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}
        idx = json.loads(entries["index.json"].decode("utf-8"))
        ghost = sentinel.encode("utf-8")
        idx["manifests"].append({"mediaType": MT_MANIFEST, "digest": "sha256:" + sha(ghost), "size": len(ghost),
                                 "annotations": {REF: sentinel}})
        entries["index.json"] = cjson(idx)
    except (OSError, KeyError, ValueError, AttributeError, tarfile.TarError) as e:
        rf, _, _ = check(path, o)
        return 1, "FAIL two-sided oci_closure: cannot plant into the real tar (%s); real check: %s" % (e, "; ".join(rf[:3]))
    tmp = tempfile.mkdtemp(prefix="oci-plant-")
    try:
        planted = os.path.join(tmp, "planted.tar")
        with open(planted, "wb") as f:
            f.write(tar_bytes(entries))
        pf, _, _ = check(planted, o)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    named = [x for x in pf if sentinel in x]
    if not named:
        return 1, "FAIL two-sided oci_closure: the planted descriptor was not caught by name (%s)" % (pf[:1] or "passed")
    rf, n, summary = check(path, o)
    if rf:
        return 1, "FAIL two-sided oci_closure: plant caught, but the real tar fails: %s" % "; ".join(rf[:5])
    return 0, "PASS two-sided oci_closure: plant %s -> FAIL naming it (%s); real -> PASS (%s)" % (sentinel, named[0], summary)


class Opts(object):
    def __init__(self, layout_version="1.0.0", ref_name=None, revision=None, layer_contains=()):
        self.layout_version, self.ref_name, self.revision = layout_version, ref_name, revision
        self.layer_contains = list(layer_contains)


def self_test():
    tmp = tempfile.mkdtemp(prefix="oci-selftest-")
    try:
        src = os.path.join(tmp, "data.jsonl")
        with open(src, "wb") as f:
            f.write(b'{"k":1}\n')
        rev = "0" * 40
        t1 = build([src], "srv/selftest/", "selftest-bundle", rev)
        t2 = build([src], "srv/selftest/", "selftest-bundle", rev)
        if t1 != t2:
            print("SELF-TEST FAIL oci_closure.py: two builds of the same input differ")
            return 1
        path = os.path.join(tmp, "layout.tar")
        with open(path, "wb") as f:
            f.write(t1)
        o = Opts(ref_name="selftest-bundle", revision=rev, layer_contains=["srv/selftest/data.jsonl"])
        rc, line = two_sided(path, o, "DEVLOOP-PLANTED-SELFTEST")
        if rc != 0:
            print("SELF-TEST FAIL oci_closure.py: " + line)
            return 1
        gz = os.path.join(tmp, "layout.tar.gz")
        with open(gz, "wb") as f:
            f.write(gzip.compress(t1))
        fails, _, _ = check(gz, o)
        if not (fails and "compressed (gzip)" in fails[0]):
            print("SELF-TEST FAIL oci_closure.py: a compressed tar was not refused: %s" % fails)
            return 1
        print("SELF-TEST PASS oci_closure.py (python %s): %s" % (sys.version.split()[0], line))
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if argv == ["--self-test"]:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd")
    c = sp.add_parser("check")
    c.add_argument("tar")
    c.add_argument("--layout-version", default="1.0.0")
    c.add_argument("--ref-name")
    c.add_argument("--revision")
    c.add_argument("--layer-contains", action="append", default=[])
    c.add_argument("--two-sided", metavar="SENTINEL")
    b = sp.add_parser("build")
    b.add_argument("files", nargs="+")
    b.add_argument("--out", required=True)
    b.add_argument("--layer-root", required=True)
    b.add_argument("--ref-name", required=True)
    b.add_argument("--revision")
    b.add_argument("--annotation", action="append", default=[])
    b.add_argument("--layout-version", default="1.0.0")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "build":
        ann = {}
        for kv in a.annotation:
            if "=" not in kv:
                print("usage: --annotation KEY=VALUE", file=sys.stderr)
                return 2
            k, v = kv.split("=", 1)
            ann[k] = v
        data = build(a.files, a.layer_root, a.ref_name, a.revision, ann, a.layout_version)
        with open(a.out, "wb") as f:
            f.write(data)
        print(json.dumps({"name": os.path.basename(a.out), "bytes": len(data), "sha256": sha(data)}, sort_keys=True))
        return 0
    if a.cmd != "check":
        ap.print_usage(sys.stderr)
        return 2
    o = Opts(a.layout_version, a.ref_name, a.revision, a.layer_contains)
    if a.two_sided:
        rc, line = two_sided(a.tar, o, a.two_sided)
        print(line)
        return rc
    fails, n, summary = check(a.tar, o)
    for x in fails[:40]:
        print("FAIL oci_closure: " + x)
    if fails:
        return 1
    print("PASS oci_closure %s: %s" % (os.path.basename(a.tar), summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
