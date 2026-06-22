# BJP Label Architecture

## Overview

BJP Label has three layers:

- Lovelace custom card: the main user interface.
- Home Assistant custom integration: service/API bridge.
- Backend service: future persistence layer for SQLite customer history.

The first production path is intentionally short:

```text
Lovelace card -> bjp_label.print_label -> selected printer backend
```

## Frontend

The frontend is bundled inside the custom integration at:

```text
custom_components/bjp_label/frontend/bjp-label-card.js
```

During Home Assistant startup the integration exposes this directory at
`/bjp_label` and registers the JavaScript module with Lovelace. The card appears
in the dashboard card picker without a manually configured Resource.

Responsibilities:

- Render Thai customer inputs and the generated no-print label image.
- Require a successful preview of the current data before enabling real printing.
- Provide large touch-friendly inputs and buttons.
- Call Home Assistant services through the normal dashboard connection.
- Avoid admin-only pages during routine use.

Phase 1 service calls:

- `bjp_label.print_label` with `preview: true` and a response for Preview.
- `bjp_label.print_label` with `preview: false` for real printing.

Phase 2 service calls:

- `bjp_label.save_customer`
- `bjp_label.search_customers`
- `bjp_label.print_customer`

## Integration

The custom integration lives in:

```text
custom_components/bjp_label
```

Responsibilities:

- Register BJP Label services.
- Validate service data.
- Build the Niimbot label payload when Niimbot is selected.
- Render a Thai bitmap and send TSPL over TCP when Xprinter is selected.
- Keep printer target configurable.

The integration must not implement Niimbot transport or Bluetooth code. Xprinter support is limited to the already-configured TCP printer path.

The public `bjp_label.print_label` service is the printer-independent boundary used
by the Lovelace card. Rendering and the internal printer backend are kept separate,
so multiple printer backends can coexist without changing the normal card workflow.

`bjp_label.print_label` supports an optional service response. Preview calls return
`{"image": "data:image/..."}` from the selected backend; the card displays that data
URL directly and does not require a separate camera or image entity.

## Printing

BJP Label supports two print paths:

- Niimbot through the existing `hass-niimbot` service.
- Xprinter XP-420B through direct TCP `TSPL` with a rendered bitmap.

Niimbot example:

```yaml
action: niimbot.print
data:
  payload:
    - type: text
      value: Customer Name
      font: NotoSansThai-Regular.ttf
      x: 24
      y: 20
      size: 34
  width: 640
  height: 384
  rotate: 90
target:
  device_id: <niimbot device id>
```

Recommended first layout for Niimbot B1:

- Label width before rotation: `640`
- Label height before rotation: `384`
- Density: `3`
- Rotation: `90`
- Font: `NotoSansThai-Regular.ttf`

These are tuning defaults, not protocol assumptions.

## Backend

The backend is reserved for Phase 2.

Responsibilities:

- Store customer records in SQLite.
- Provide search APIs.
- Track print history fields.
- Run in the background only.

The backend must not become the normal user UI.

## Data

Phase 2 customer record:

- `id`
- `name`
- `phone`
- `address`
- `note`
- `created_at`
- `updated_at`
- `last_printed_at`
- `print_count`

## Permissions

Normal users interact through a dashboard card. Admin access may be required only for installation, dashboard setup, and initial configuration.
