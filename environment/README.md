# environment/ — compat wrappers

The canonical environment scripts live in `skills/dev-loop/scripts/env/` so they
ship with every dev-loop skill install. These wrappers just forward to them:

| Wrapper | Canonical | Purpose |
|---|---|---|
| `setup-antigravity.sh` | `…/env/setup-antigravity.sh` | Idempotent provisioning (Fedora dnf / Debian apt): keyring stack, agy CLI, skill install |
| `agy-login.sh` | `…/env/agy-login.sh` | Two-step first-run login: prints the Google auth URL, then `--code '<code>'` finishes onboarding and verifies |
| `agy-doctor.sh` | `…/env/agy-doctor.sh` | PASS/WARN/FAIL health checks; `--probe` = one real headless agy call |
| `agy-keyring.sh` | `…/env/agy-keyring.sh` | Sourceable Secret Service bootstrap so the login persists |
