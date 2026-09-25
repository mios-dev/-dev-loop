#!/usr/bin/env python3
"""Validate a JSON document against a JSON Schema written in the OpenAI strict structured-output
subset. Offline; Python 3 standard library only; never touches the network.

  python3 schema_check.py --schema SCHEMA.json DOC.json [--two-sided DEVLOOP-PLANTED-<ID>]
  python3 schema_check.py --self-test

SCHEMA.json is either a bare schema, a {"name", "strict", "schema"} object, or a whole
response_format object {"type": "json_schema", "json_schema": {...}} copied byte for byte from
the contract. Supported keywords: type, enum, const, pattern, required, properties,
additionalProperties, items, anyOf, $ref/$defs/definitions, minItems, maxItems, minLength,
maxLength, minimum, maximum, exclusiveMinimum, exclusiveMaximum, multipleOf, plus annotations
(title, description, default, examples, $schema, $id, $comment). Any other keyword is an error:
a validator that skips what it cannot check would pass what it never checked. When the schema
says strict, it is also linted: every object schema must set additionalProperties false and
list every property in required.
--two-sided adds the sentinel as an extra top-level property to a copy of DOC, requires a
failure naming it, then requires DOC to pass. Exit 0 = valid, 1 = invalid, 2 = usage.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

SENTINEL_RE = re.compile(r"^DEVLOOP-PLANTED-[A-Z0-9]+(-[A-Z0-9]+)*$")
ANNOTATIONS = {"title", "description", "default", "examples", "$schema", "$id", "$comment"}
KEYWORDS = {"type", "enum", "const", "pattern", "required", "properties", "additionalProperties", "items", "anyOf",
            "$ref", "$defs", "definitions", "minItems", "maxItems", "minLength", "maxLength", "minimum", "maximum",
            "exclusiveMinimum", "exclusiveMaximum", "multipleOf"} | ANNOTATIONS


def unwrap(doc):
    """Return (schema, strict)."""
    if isinstance(doc, dict) and isinstance(doc.get("json_schema"), dict):
        doc = doc["json_schema"]
    if isinstance(doc, dict) and "schema" in doc and "name" in doc:
        return doc["schema"], bool(doc.get("strict"))
    return doc, False


PY_TYPES = {"string": str, "boolean": bool, "object": dict, "array": list}


def is_type(v, t):
    if t == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t == "null":
        return v is None
    return t in PY_TYPES and isinstance(v, PY_TYPES[t])


def resolve(ref, root):
    if ref == "#":
        return root
    if not ref.startswith("#/"):
        raise ValueError("only local $ref is supported, got %r" % ref)
    node = root
    for part in ref[2:].split("/"):
        node = node[part.replace("~1", "/").replace("~0", "~")]
    return node


def lint(schema, path, errs):
    if not isinstance(schema, dict):
        return
    if "properties" in schema or schema.get("type") == "object":
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is not False:
            errs.append("schema %s: strict mode needs additionalProperties false" % path)
        if set(schema.get("required", [])) != set(props):
            errs.append("schema %s: strict mode needs every property required (missing %s)"
                        % (path, sorted(set(props) - set(schema.get("required", [])))))
        for k, sub in props.items():
            lint(sub, "%s.%s" % (path, k), errs)
    if isinstance(schema.get("items"), dict):
        lint(schema["items"], path + "[]", errs)
    for key in ("anyOf",):
        for j, sub in enumerate(schema.get(key, []) or []):
            lint(sub, "%s.%s[%d]" % (path, key, j), errs)
    for key in ("$defs", "definitions"):
        for k, sub in (schema.get(key) or {}).items():
            lint(sub, "%s.%s.%s" % (path, key, k), errs)


def validate(v, s, path, root, errs, count):
    count[0] += 1
    if s is True or s == {}:
        return
    if s is False:
        errs.append("%s: no value is allowed here" % path)
        return
    if not isinstance(s, dict):
        errs.append("%s: schema node is not an object" % path)
        return
    unknown = sorted(set(s) - KEYWORDS)
    if unknown:
        errs.append("%s: unsupported schema keyword(s) %s -- refusing to pass what this checker cannot check" % (path, unknown))
    if "$ref" in s:
        try:
            validate(v, resolve(s["$ref"], root), path, root, errs, count)
        except (KeyError, ValueError, TypeError) as e:
            errs.append("%s: unresolvable $ref %r (%s)" % (path, s["$ref"], e))
    t = s.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        if not any(is_type(v, x) for x in types):
            errs.append("%s: %s is not of type %s" % (path, type(v).__name__, t))
            return
    if "enum" in s and v not in s["enum"]:
        errs.append("%s: %r is not one of %s" % (path, v, s["enum"]))
    if "const" in s and v != s["const"]:
        errs.append("%s: %r is not %r" % (path, v, s["const"]))
    if isinstance(v, str):
        if "pattern" in s and not re.search(s["pattern"], v):
            errs.append("%s: %r does not match %s" % (path, v[:80], s["pattern"]))
        if "minLength" in s and len(v) < s["minLength"]:
            errs.append("%s: shorter than %d" % (path, s["minLength"]))
        if "maxLength" in s and len(v) > s["maxLength"]:
            errs.append("%s: longer than %d" % (path, s["maxLength"]))
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        for k, bad in (("minimum", lambda a, b: a < b), ("maximum", lambda a, b: a > b),
                       ("exclusiveMinimum", lambda a, b: a <= b), ("exclusiveMaximum", lambda a, b: a >= b)):
            if k in s and bad(v, s[k]):
                errs.append("%s: %r violates %s %r" % (path, v, k, s[k]))
        if "multipleOf" in s and s["multipleOf"] and (v / s["multipleOf"]) % 1:
            errs.append("%s: %r is not a multiple of %r" % (path, v, s["multipleOf"]))
    if isinstance(v, dict):
        props = s.get("properties", {})
        for k in s.get("required", []):
            if k not in v:
                errs.append("%s: required property %r missing" % (path, k))
        for k, val in v.items():
            if k in props:
                validate(val, props[k], "%s.%s" % (path, k), root, errs, count)
            elif s.get("additionalProperties") is False:
                errs.append("%s: additional property %r not allowed" % (path, k))
            elif isinstance(s.get("additionalProperties"), dict):
                validate(val, s["additionalProperties"], "%s.%s" % (path, k), root, errs, count)
    if isinstance(v, list):
        if "minItems" in s and len(v) < s["minItems"]:
            errs.append("%s: fewer than %d items" % (path, s["minItems"]))
        if "maxItems" in s and len(v) > s["maxItems"]:
            errs.append("%s: more than %d items" % (path, s["maxItems"]))
        if isinstance(s.get("items"), dict):
            for j, item in enumerate(v):
                validate(item, s["items"], "%s[%d]" % (path, j), root, errs, count)
    if "anyOf" in s:
        for sub in s["anyOf"]:
            e = []
            validate(v, sub, path, root, e, count)
            if not e:
                break
        else:
            errs.append("%s: matches no anyOf branch" % path)


def check(schema_doc, doc):
    """Return (failures, nodes_validated, summary)."""
    schema, strict = unwrap(schema_doc)
    errs, count = [], [0]
    if strict:
        lint(schema, "$", errs)
    validate(doc, schema, "$", schema, errs, count)
    if count[0] == 0:
        errs.append("empty set: 0 schema nodes evaluated")
    return errs, count[0], "%d schema nodes evaluated%s" % (count[0], ", strict lint on" if strict else "")


def two_sided(schema_doc, doc, sentinel):
    if not SENTINEL_RE.match(sentinel):
        return 2, "sentinel must look like DEVLOOP-PLANTED-<ID> (uppercase, digits, hyphens)"
    if sentinel in json.dumps(doc):
        return 1, "FAIL two-sided schema_check: %s already occurs in the document; pick another" % sentinel
    if not isinstance(doc, dict):
        return 1, "FAIL two-sided schema_check: the document is not an object, nothing to plant into"
    planted = dict(doc)
    planted[sentinel] = "planted"
    pf, _, _ = check(schema_doc, planted)
    named = [x for x in pf if sentinel in x]
    if not named:
        return 1, "FAIL two-sided schema_check: the planted property was not caught by name (%s)" % (pf[:1] or "passed")
    rf, n, summary = check(schema_doc, doc)
    if rf:
        return 1, "FAIL two-sided schema_check: plant caught, but the real document fails: %s" % "; ".join(rf[:5])
    return 0, "PASS two-sided schema_check: plant %s -> FAIL naming it (%s); real -> PASS (%s)" % (sentinel, named[0], summary)


def self_test():
    rf = {"type": "json_schema", "json_schema": {"name": "selftest", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["id", "items"],
        "properties": {"id": {"type": "string", "pattern": "^[0-9a-f]{4}$"},
                       "items": {"type": "array", "items": {"type": "integer"}}}}}}
    rc, line = two_sided(rf, {"id": "00ff", "items": [1, 2]}, "DEVLOOP-PLANTED-SELFTEST")
    if rc != 0:
        print("SELF-TEST FAIL schema_check.py: " + line)
        return 1
    errs, _, _ = check(rf, {"id": "zz", "items": [1, "2"]})
    if not (any("does not match" in e for e in errs) and any("items[1]" in e for e in errs)):
        print("SELF-TEST FAIL schema_check.py: defects not reported: %s" % errs)
        return 1
    loose = {"type": "object", "properties": {"id": {"type": "string"}}}
    rc2, _ = two_sided(loose, {"id": "x"}, "DEVLOOP-PLANTED-SELFTEST")
    if rc2 == 0:
        print("SELF-TEST FAIL schema_check.py: a schema that allows extra properties let the plant count as caught")
        return 1
    print("SELF-TEST PASS schema_check.py (python %s): %s" % (sys.version.split()[0], line))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("doc", nargs="?")
    ap.add_argument("--schema")
    ap.add_argument("--two-sided", metavar="SENTINEL")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not (a.doc and a.schema):
        ap.print_usage(sys.stderr)
        return 2
    try:
        with open(a.schema, encoding="utf-8") as f:
            schema_doc = json.load(f)
        with open(a.doc, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError) as e:
        print("FAIL schema_check: cannot load: %s" % e)
        return 1
    if a.two_sided:
        rc, line = two_sided(schema_doc, doc, a.two_sided)
        print(line)
        return rc
    errs, n, summary = check(schema_doc, doc)
    for e in errs[:60]:
        print("FAIL schema_check: " + e)
    if errs:
        return 1
    print("PASS schema_check: %s" % summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
