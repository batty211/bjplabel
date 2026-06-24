# BJP Label Project Status

Last updated: 2026-06-24

## Done

- Added Home Assistant Config Flow setup for one BJP Label instance.
- Setup stores the selected `niimbot` device and Thai font filename.
- Added `phonenumbers` for Thai phone detection, validation, and formatting.
- Added lightweight order-independent parsing for Thai names, addresses, and postal codes.
- Kept `bjp_label.print_label` compatible with legacy `name`, `phone`, and `address` calls.
- Added raw `text` printing for pasted customer messages.
- Reworked the Lovelace card to one large text box with detected-data preview.
- Printing is disabled when the card cannot detect a name or phone number.
- Updated the default B1 layout to 640 x 384 pixels before rotation, density 3, rotation 90.
- Added an editable formatted-label textarea; its contents are authoritative when printing.
- Bundled and auto-registered the Lovelace card; manual Resource setup is no longer required.
- Added visible version and ready, connecting, printing, completed, and error states.
- Locked the print button while printing and after success until the data changes or is cleared.
- Added offline postcode lookup with explicit warnings for inferred, ambiguous, and missing results.
- Added parser regression tests for the supplied examples and reordered input.
- Fixed phone detection so postal codes cannot join numbers on the next line.
- Added organization-name fallback and balanced address output of up to three lines.
- Removed the automatic `ส่ง` prefix from preview and printed labels.
- Isolated the Niimbot service call behind an internal printer backend boundary.
- Added automatic no-print previews and disabled real printing until the current preview succeeds.
- Added preview image service responses, stale-response protection, retry, and preview-only mode.
- Updated setup and service examples for the new workflow.
- Fixed the options flow to follow `OptionsFlowWithReload` requirements and save backend settings without a Config-page 500 error.
- Added file-based debug logging for config-edit flow steps and exceptions to help diagnose Home Assistant Config page failures.
- Fixed options-flow initialization so debug logging also works when the Config page fails before any step renders.
- Stopped writing to the Home Assistant `config_entry` property inside `OptionsFlowWithReload` and now keep the entry in a private field to avoid Config-page creation crashes.
- Released v0.4.9 with a bordered Thai sample-style layout for Xprinter 100 x 75 mm labels while keeping the Niimbot payload unchanged.
- Released v0.4.10 with more flexible edited contact text and clear non-blocking postal-code warnings in the Lovelace card.

## Verification

- Parser unit tests pass locally.
- JavaScript, Python, JSON, and YAML syntax checks pass locally.
- Home Assistant runtime setup and physical Niimbot output still require testing on the target system.
- Physical Xprinter output for the new bordered 100 x 75 mm layout still requires testing on the target printer.

## Installation Notes

- Install and configure `hass-niimbot` first.
- Install or update BJP Label through HACS, restart Home Assistant, then add BJP Label under Devices & services.
- Put a Thai `.ttf` font such as `NotoSansThai-Regular.ttf` in a location supported by `hass-niimbot`.
- Add `BJP Label` from the dashboard card picker after restarting Home Assistant.
- Remove any old `/local/bjp-label-card/...` Resource left from a manual installation.

## Next Work

- Test Config Flow and service registration after a Home Assistant restart.
- Verify automatic preview responses and the displayed image on the target dashboard.
- Confirm the 640 x 384 pre-rotation layout on the actual Niimbot B1 50 x 80 mm labels.
- Confirm the configured Thai font renders without missing glyphs.
- Test a physical print after the preview layout is correct.

Phase 2 persistence and Phase 3 features remain intentionally out of scope.
