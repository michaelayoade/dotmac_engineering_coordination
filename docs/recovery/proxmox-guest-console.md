# Proxmox guest-console recovery rehearsal

- Owner: the guest's `recovery.owner_ref`
- Last reviewed: 2026-09-03
- Scope: declared hosts whose `provider_ref` is `proxmox:vm/<vmid>`

This rehearsal proves access to the guest's out-of-band console. Normal SSH,
the QEMU guest agent, and a read-only API token do not prove this route.

## Read-only rehearsal

1. Name the exact `host_id`; resolve its VMID only from `provider_ref`.
2. Read Proxmox inventory and refuse if identity is conflicted. A stopped guest
   is not started merely for this check.
3. Authenticate through an approved human console identity.
4. Open the console without issuing input that changes guest state.
5. Prove that the displayed guest is the named VM and record operator, host id,
   VMID, timestamp and a non-secret audit reference.

The plan remains `declared` until the owner reviews the evidence and records
`decided_at` and `last_rehearsed_at`.

## Recovery operation

Starting, stopping, rebooting, snapshotting or changing a VM requires explicit
target and applicable deployment/change authority.
