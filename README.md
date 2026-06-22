# BJP Label

BJP Label is a Home Assistant project for entering customer details and printing Thai customer labels on either a Niimbot printer or an Xprinter XP-420B.

The project is designed for household use through a normal Lovelace dashboard. The main user does not need to be a Home Assistant admin.

## What This Uses

- Home Assistant Lovelace custom card for the user interface.
- HACS custom integration as the bridge between the card and Home Assistant services.
- Existing `hass-niimbot` integration for Niimbot printing.
- Direct TCP `TSPL` printing for Xprinter XP-420B on port `9100`.
- SQLite in a later phase for customer history.

Niimbot printing intentionally goes through `niimbot.print`. Xprinter printing renders Thai text to an image first, then sends that bitmap over TSPL.

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

1. Install and configure `hass-niimbot` in Home Assistant if you will use a Niimbot printer.
2. Or prepare the Xprinter XP-420B IP address and confirm it accepts TCP printing on port `9100`.
3. Add this repository to HACS as a custom repository with category `Integration`.
4. Install BJP Label from HACS and restart Home Assistant.
5. Go to Settings / Devices & services, add `BJP Label`, then select the printer backend, label size, and Thai font.
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

The Niimbot path supports referencing custom fonts placed in `www/fonts` or the integration font locations. The Xprinter path uses the same Thai `.ttf` file to render the bitmap preview and print image.

## MVP Workflow

1. Open the Home Assistant dashboard.
2. Paste the customer's name, phone number, and address into the single text box.
3. Check the detected name, formatted phone number, address, and postal code.
4. Wait for the automatic no-print preview and inspect the label image.
5. Tap `พิมพ์จริง` only after the preview is correct.
6. The label prints through the selected backend.

The Print button stays disabled until the current data has a successful preview.
Editing either text box invalidates the old preview and generates a new one.

## Current Status

This repository contains the Phase 1 printing workflow:

- Documentation.
- UI-based Home Assistant setup and service registration.
- Single-input Lovelace card with lightweight Thai customer text parsing.
- Offline postcode lookup from Thai subdistrict, district, and province names.
- Phase 2 SQLite schema.

Phase 1 persistence is intentionally not implemented yet.

For the latest handoff notes, completed work, and next steps, see `PROJECT_STATUS.md`.
