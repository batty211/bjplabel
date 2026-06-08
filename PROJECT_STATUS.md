# BJP Label Project Status

Last updated: 2026-06-08

## Done

- Created initial project documentation:
  - `README.md`
  - `SPEC.md`
  - `ARCHITECTURE.md`
  - `ACHITECTURE.md`
  - `AGENTS.md`
- Created Home Assistant custom integration scaffold:
  - `custom_components/bjp_label/manifest.json`
  - `custom_components/bjp_label/__init__.py`
  - `custom_components/bjp_label/const.py`
  - `custom_components/bjp_label/services.yaml`
- Added MVP service `bjp_label.print_label`.
- `bjp_label.print_label` builds a simple customer label payload and calls existing `niimbot.print`.
- Added Phase 2 placeholder services:
  - `bjp_label.save_customer`
  - `bjp_label.search_customers`
  - `bjp_label.print_customer`
- Created Lovelace custom card scaffold:
  - `www/bjp-label-card/bjp-label-card.js`
- Card includes Thai form fields:
  - Customer name
  - Phone number
  - Address
  - Note
- Card includes large Thai action buttons:
  - Save
  - Print
  - Save and print
  - Clear
- Created Phase 2 backend planning files:
  - `backend/README.md`
  - `backend/schema.sql`
- Added example configs:
  - `examples/lovelace-card.yaml`
  - `examples/print-label-service.yaml`
- Added HACS metadata:
  - `hacs.json`
  - `issue_tracker` in integration manifest
  - real GitHub documentation URL in integration manifest
- Bumped integration version to `0.1.1`.
- Created and pushed commit/tag already on remote:
  - commit `297b678` / tag `0.1.1`
- Recorded Git working rule in `AGENTS.md`:
  - Do not commit, tag, or push unless the user explicitly asks in the current turn.

## Current Git State

- Remote `main` is at commit `297b678`.
- Tag `0.1.1` exists.
- Uncommitted local change:
  - `AGENTS.md`
  - `PROJECT_STATUS.md`

## Important Notes

- The integration must use existing `hass-niimbot`.
- Do not write a Niimbot driver or protocol implementation.
- Normal user UI must stay in Lovelace Dashboard.
- Backend/add-on must stay background-only.
- User should not need Home Assistant admin access for normal use.
- Thai printing requires a real Thai-capable `.ttf` font, for example `NotoSansThai-Regular.ttf`.
- Recommended Home Assistant font location:
  - `/config/www/fonts/NotoSansThai-Regular.ttf`

## Next Work

### Immediate

- In Home Assistant/HACS, refresh or reinstall BJP Label using version `0.1.1`.
- Confirm HACS no longer reports: `The version 5ba14e6 for this integration can not be used with HACS`.
- Install/restart Home Assistant and verify `bjp_label.print_label` appears in services/actions.
- Copy or serve `www/bjp-label-card/bjp-label-card.js` under `/config/www/bjp-label-card/`.
- Add Lovelace resource:

```yaml
url: /local/bjp-label-card/bjp-label-card.js
type: module
```

- Add dashboard card using `examples/lovelace-card.yaml`.
- Replace `replace_with_niimbot_device_id` with the actual Niimbot B1 device id.
- Test with `preview: true` first.
- Test real print after preview works.

### Phase 1 Fixes Likely Needed After HA Test

- Verify Home Assistant accepts the service schema and target forwarding.
- Tune label layout for the actual B1 label size.
- Confirm Thai font is found by `hass-niimbot`.
- Improve user-facing card error messages if HA returns technical errors.
- Consider bundling Lovelace card installation guidance more clearly because HACS integration install does not automatically install `/www` files.

### Phase 2

- Implement SQLite persistence.
- Wire `save_customer`, `search_customers`, and `print_customer`.
- Add customer search UI in the Lovelace card.
- Load selected customer into the form.
- Update `last_printed_at` and `print_count`.

### Phase 3

- Add multiple label templates.
- Add print preview.
- Add import/export.
- Add print statistics.
- Add recent customer list.
