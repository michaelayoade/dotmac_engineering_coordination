# Contabo console recovery rehearsal

- Owner: the host's `recovery.owner_ref`
- Last reviewed: 2026-09-03
- Scope: hosts whose recovery method is `provider_console`

This rehearsal proves that an authorised operator can reach the provider recovery
surface for the exact declared instance. It does not authorise a reboot,
shutdown, rescue boot, credential reset or reinstall.

## Read-only rehearsal

1. Name the exact `host_id` and obtain its reviewed fleet record.
2. Refuse if the host is inactive, conflicted, stale, or its provider reference
   and current Contabo inventory do not identify one unique instance.
3. Authenticate to the Contabo control plane through the approved human access
   path. Never copy the account credential into this repository, a command,
   workflow output or evidence record.
4. Open the exact instance's console/recovery page without invoking an action.
5. Compare the displayed instance id, hostname and addresses with the reviewed
   declaration and current provider observation.
6. Exit without changing state. Record the operator, host id, provider instance
   id, timestamp, and the non-secret provider event/reference when available.

The plan becomes `verified` only when the owner accepts that evidence and sets
`decided_at`, `last_rehearsed_at`, and a typed evidence reference.

## Recovery operation

An actual rescue boot, restart, password reset or reinstall is a separate
production mutation requiring explicit target and approved change authority.
