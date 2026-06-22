# BJP Label

BJP Label is a Home Assistant project for entering customer details and printing Thai customer labels on a Niimbot B1 label printer.

The project is designed for household use through a normal Lovelace dashboard. The main user does not need to be a Home Assistant admin.

## What This Uses

- Home Assistant Lovelace custom card for the user interface.
- HACS custom integration as the bridge between the card and Home Assistant services.
- Existing `hass-niimbot` integration for actual printing.
- SQLite in a later phase for customer history.

Printing intentionally goes through `niimbot.print`. This project does not create a new Niimbot driver.

## Repository Layout

```text
custom_components/bjp_label/     Home Assistant integration and Lovelace card
backend/                         Phase 2 backend and SQLite planning
examples/                        Dashboard and service examples
AGENTS.md                        Agent and contributor guidance
SPEC.md                          Product specification
ARCHITECTURE.md                  Architecture notes
ACHITECTURE.md                   Typo-compatible pointer to ARCHITECTURE.md
```

## Phase 1 Setup

1. Install and configure `hass-niimbot` in Home Assistant.
2. Confirm the Niimbot B1 can print from Home Assistant.
3. Add this repository to HACS as a custom repository with category `Integration`.
4. Install BJP Label from HACS and restart Home Assistant.
5. Go to Settings / Devices & services, add `BJP Label`, then select the Niimbot printer and Thai font.
6. Open a dashboard as an administrator, choose Add card, and select `BJP Label`.

The integration serves and registers its Lovelace JavaScript automatically. A normal
user only opens the dashboard and does not need administrator access. If an older
version was installed manually, remove the `/local/bjp-label-card/...` Resource once
to avoid loading two copies of the card.

Manual install is also possible by copying `custom_components/bjp_label` into Home Assistant `custom_components`.

## Thai Font

Put a Thai-capable `.ttf` file in Home Assistant, for example:

```text
/config/www/fonts/NotoSansThai-Regular.ttf
```

Then configure the card or service with:

```yaml
font: NotoSansThai-Regular.ttf
```

The `hass-niimbot` integration supports referencing custom fonts placed in `www/fonts` or the integration font locations.

## MVP Workflow

1. Open the Home Assistant dashboard.
2. Paste the customer's name, phone number, and address into the single text box.
3. Check the detected name, formatted phone number, address, and postal code.
4. Tap `พิมพ์`.
5. The 50 x 80 mm label prints on the Niimbot B1.

## Current Status

This repository contains the Phase 1 printing workflow:

- Documentation.
- UI-based Home Assistant setup and service registration.
- Single-input Lovelace card with lightweight Thai customer text parsing.
- Offline postcode lookup from Thai subdistrict, district, and province names.
- Phase 2 SQLite schema.

Phase 1 persistence is intentionally not implemented yet.

For the latest handoff notes, completed work, and next steps, see `PROJECT_STATUS.md`.
