# BJP Label Specification

## Goal

Build an internal Home Assistant tool for managing customer label data and printing labels on a Niimbot B1 printer. The printer is already available in Home Assistant through `hass-niimbot`; BJP Label must reuse that integration.

## Users

- Primary user: older adult family member.
- Operator should use a normal Home Assistant dashboard.
- Operator should not need Home Assistant admin permissions, add-on pages, or settings pages during normal use.

## MVP Phase 1

### Customer Form

Required fields:

- Customer name
- Phone number
- Address

Optional field:

- Note

Buttons:

- Save
- Print
- Save and print
- Clear

Phase 1 behavior:

- Print and Save and print both call the BJP Label print service.
- Save can validate the form and show that persistence is not available until Phase 2.
- Clear resets the form.

### Printing

Printer:

- Niimbot B1

Integration:

- Use `hass-niimbot`.
- Call `niimbot.print` directly from the BJP Label custom integration.
- Do not implement Bluetooth, raster, or printer protocol code.

Label v1:

- Line 1: customer name
- Line 2: phone number
- Lines 3-4: address
- Note is stored for future use but not printed in v1.

Thai support:

- Use a Thai-capable `.ttf` font.
- Recommended default path in Home Assistant: `/config/www/fonts/<thai-font>.ttf`.
- Service data should reference the font by filename as supported by `hass-niimbot`.

## Phase 2

### Customer History

Store:

- `id`
- `name`
- `phone`
- `address`
- `note`
- `created_at`
- `updated_at`
- `last_printed_at`
- `print_count`

### Search

Search by:

- Name
- Phone number
- Address

Capabilities:

- Typing a phone number can find matching customers.
- Selecting a customer loads data into the form.
- Loaded data can be edited.
- Existing labels can be printed again.

## Phase 3

- Multiple templates.
- Label preview before printing.
- Export/import data.
- Print statistics.
- Recent customer list.

## Acceptance Criteria

- A normal dashboard user can open the Lovelace card and print without visiting add-on or settings pages.
- The custom card works on mobile and tablet sizes.
- The integration exposes `bjp_label.print_label`.
- `bjp_label.print_label` calls `niimbot.print`.
- Thai name, phone, and address render with a Thai font and do not become square glyphs.
- The first usable workflow is: open dashboard, fill name/phone/address, tap Save and print, label prints on Niimbot B1.
