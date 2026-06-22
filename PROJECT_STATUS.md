# BJP Label Project Status

Last updated: 2026-06-22

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
- Updated setup and service examples for the new workflow.

## Verification

- Parser unit tests pass locally.
- JavaScript, Python, JSON, and YAML syntax checks pass locally.
- Home Assistant runtime setup and physical Niimbot output still require testing on the target system.

## Installation Notes

- Install and configure `hass-niimbot` first.
- Install or update BJP Label through HACS, restart Home Assistant, then add BJP Label under Devices & services.
- Put a Thai `.ttf` font such as `NotoSansThai-Regular.ttf` in a location supported by `hass-niimbot`.
- Add `BJP Label` from the dashboard card picker after restarting Home Assistant.
- Remove any old `/local/bjp-label-card/...` Resource left from a manual installation.

## Next Work

- Test Config Flow and service registration after a Home Assistant restart.
- Call `bjp_label.print_label` with `preview: true` and inspect the last-label image entity.
- Confirm the 640 x 384 pre-rotation layout on the actual Niimbot B1 50 x 80 mm labels.
- Confirm the configured Thai font renders without missing glyphs.
- Test a physical print after the preview layout is correct.

Phase 2 persistence and Phase 3 features remain intentionally out of scope.
