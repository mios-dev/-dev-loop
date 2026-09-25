# Cursor Rule: Failed-Lane Postmortem

Defines the `/postmortem` protocol: take one lane that came back not-done and separate its five causes — a denied or empty harness turn, a lost worker with no receipt, an ownership stray, a vacuous gate, and a genuine defect — because each has a different remedy and only the last is a code bug. Reads the receipts already in the run directory; runs nothing by default and never re-dispatches.
