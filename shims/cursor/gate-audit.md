# Cursor Rule: Gate Audit — Can This Gate Fail?

Defines the `/gate-audit` protocol: audit the repo's STANDING gate machinery (CI workflow, Makefile/justfile recipe, lint or gate script, test directory) against the "Checks That Cannot Fail" taxonomy, then plant the violation each cleared gate claims to catch and require it to go red. `gate_audit.py` detects seven mechanically decidable rows; six judgment rows are read by the agent, and the script never claims them. Audits the standing machinery whether or not it changed — unlike `/review`, which audits a diff.
