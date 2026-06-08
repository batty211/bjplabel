# BJP Label Backend

This folder is reserved for Phase 2.

The backend will run in the background and provide persistence/search APIs for customer history. It is not intended to be a user-facing UI.

## Planned Responsibilities

- Store customer records in SQLite.
- Search by name, phone, and address.
- Load existing customer data into the Lovelace card.
- Update `last_printed_at` and `print_count`.
- Support export/import in a later phase.

## Phase 1

No backend service is required for Phase 1. Printing should work through:

```text
Lovelace card -> bjp_label.print_label -> niimbot.print
```
