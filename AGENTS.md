# Agent rules — dotmac_engineering_coordination

This repository owns short-lived engineering coordination state and the
declarative inventory that agents use to locate Dotmac infrastructure. It does
not own deployment decisions, durable organizational knowledge, or secrets.
It is a PRIVATE repository: fleet addresses and resolved topology must never be
published in a public repository or artifact.

## Hard rules

1. Fleet records contain access metadata and secret pointers only. Passwords,
   private keys, bearer tokens, and retrieved secret values are forbidden.
2. The fleet registry is the sole checked-in inventory. Generated SSH config
   is never edited by hand and must byte-compare with the renderer in CI.
3. MCP fleet tools are read-only. They may return a command plan but never
   execute SSH, contact a provider, or dereference an OpenBao pointer.
4. A production access plan requires the caller to repeat the exact host id.
   Ambiguous, stale, conflicted, inactive, or access-unverified hosts refuse.
5. Declared fleet facts and live observations remain separate. An observation
   never silently rewrites declared purpose, ownership, or access policy.
6. Every refusal has a stable code that reaches the caller unchanged.
7. Every negative-path test suite includes a positive control and a planted
   wiring defect proving the test can fail.
8. Provider and workload observations are dated snapshots, never declaration
   writers. Raw provider responses stay outside Git; only the typed safe-field
   projection may be reviewed into this private repository.

Branch before committing. Do not push, open, or merge a pull request unless
Michael asks. Never connect to a production host unless Michael names it.
