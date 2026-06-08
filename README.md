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
custom_components/bjp_label/     Home Assistant custom integration
www/bjp-label-card/              Lovelace custom card
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
5. Copy `www/bjp-label-card/bjp-label-card.js` into Home Assistant `/config/www/bjp-label-card/`.
6. Add the card resource to Lovelace:

```yaml
url: /local/bjp-label-card/bjp-label-card.js
type: module
```

7. Add a card to a dashboard using `examples/lovelace-card.yaml`.

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
2. Enter customer name.
3. Enter phone number.
4. Enter address.
5. Tap `บันทึกและพิมพ์`.
6. The label prints on the Niimbot B1.

## Current Status

This repository contains the initial scaffold:

- Documentation.
- Home Assistant service registration.
- Lovelace card prototype.
- Phase 2 SQLite schema.

Phase 1 persistence is intentionally not implemented yet.

For the latest handoff notes, completed work, and next steps, see `PROJECT_STATUS.md`.
