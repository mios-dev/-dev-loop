# Cursor Rule: Preflight the Environment

Defines the `/preflight` protocol: before dispatching any lane, verify the harness binaries and
the exact CLI flags the lane command templates rely on (`adapters.py probe`), AGY auth and
headless grants (`agy-doctor.sh`), and repo conformance (`validate.sh`) — reading the printed
lines rather than the exit code, and naming the remedy instead of running it.
