# ADR 000: Phase 0 environment notes

Development so far ran on native Windows (PowerShell/Git Bash), which lacks `make`, `go`, `helm`, `k3d`
and `terraform`. The spec targets WSL2 Ubuntu; `make` targets assume WSL. The Dashboard scaffold uses the
current Vite template (React 19, oxlint) rather than eslint; `npm run lint` runs oxlint.
