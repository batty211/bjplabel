# BJP Label Agent Guide

## Mission

BJP Label is a Home Assistant based customer label tool for in-house use. The primary user is an older adult, so every change must favor simple flows, large controls, clear Thai text, and low cognitive load.

## Non-Negotiables

- The main user interface must be a Lovelace dashboard card.
- The regular user must not need Home Assistant admin access.
- Do not build a Niimbot driver or protocol implementation.
- Niimbot printing must go through the existing `hass-niimbot` integration and its `niimbot.print` service.
- Xprinter XP-420B printing may use direct TCP `TSPL` on port `9100` with image-based Thai rendering.
- Backend or add-on work must run in the background only; it must not become the normal user UI.
- Thai text must be supported end to end. Any printed label template must use a real Thai-capable `.ttf` font.

## Product Phases

### Phase 1

- Lovelace custom card.
- Customer entry form.
- Print button.
- Save and print button may behave as print-only until persistence exists.
- Integration service dispatches to the configured printer backend.
- No SQLite persistence required.

### Phase 2

- SQLite customer history.
- Search by name, phone, and address.
- Load existing customer into the form.
- Edit customer data.
- Reprint and update print counters.

### Phase 3

- Multiple label templates.
- Preview before printing.
- Export/import customer data.
- Print statistics.
- Recent customer list.

## UX Rules

- Use Thai labels for the actual card UI.
- Make inputs and buttons large enough for tablet and mobile use.
- Keep the main workflow to one screen.
- Prefer direct action buttons: save, print, save and print, clear.
- Avoid hidden settings for routine use.
- Avoid technical messages in user-facing errors where possible.

## Engineering Rules

- Keep Home Assistant service names stable.
- Keep printer selection configurable through service/card config.
- Keep label layout values explicit so physical tuning is easy.
- Do not add database coupling to Phase 1 print behavior.
- Treat `backend/schema.sql` as Phase 2 planning until a backend service is implemented.
- Do not create commits, tags, or pushes unless the user explicitly asks for that Git action in the current turn.
- When handing work back, provide a concise summary that is enough for the user to commit manually.
