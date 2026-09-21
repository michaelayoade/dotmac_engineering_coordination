# Physical-console recovery rehearsal

- Owner: the host's `recovery.owner_ref`
- Last reviewed: 2026-09-03
- Scope: on-premises physical hosts

This runbook proves that a named site operator can reach the exact physical
machine when network access is unavailable.

## Non-disruptive rehearsal

1. Name the exact `host_id` and identify its site, rack/device label and owner.
2. Refuse if the physical identity is ambiguous or no site operator accepts the
   handoff.
3. Locate the machine and confirm console equipment without pressing reset,
   power or boot-selection controls.
4. Compare visible host identity with the reviewed fleet record without entering
   or exposing a credential.
5. Record operator, host id, timestamp, physical asset reference and safe
   evidence of console reachability.

The plan remains `declared` until the owner records a reviewed runbook pointer,
decision time, rehearsal time and evidence.

## Recovery operation

Power cycling, boot changes, password recovery or hardware replacement requires
an explicit target, approved window and rollback or rebuild procedure.
