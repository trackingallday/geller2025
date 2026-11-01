# Geller Admin App — progress and next steps

Last written 2026-11-01.
Original plan: `/Users/rimu/.claude/plans/look-at-how-in-ethereal-wand.md`
Parity plan (current): `/Users/rimu/.claude/plans/omg-you-have-totally-atomic-acorn.md`

## Where things stand

Two repositories, both on a branch, nothing merged and nothing pushed.

| Repo | Branch | Commits |
|---|---|---|
| `geller.website` | `admin-app-backend` | 6 new, on top of `0fd6380` |
| `geller-admin-app` | `main` (new repo) | 7 |

The full Django suite runs **375 tests with 3 errors**. Those 3 are
`reports.test_browser_integration`, which fail on a corrupt chromedriver
download and failed the same way before this work started. The app passes
11 tests, `npx tsc --noEmit` and `npm run build`.

**⚠️ The screens are read-only copies, not replacements.** All seven
sidebar entries open a screen, but none of the custom panels' writes can be
reached: no editing, no report-type builder, no proposals builder, no ticket
actions. That missed the point of the work. The parity plan that fixes it is
`/Users/rimu/.claude/plans/omg-you-have-totally-atomic-acorn.md`. Measure
progress against its feature tables, not against "the screen renders".

### The backend

- **Staff gate** (`chemsapp/staff_api.py`) replacing all 40
  `@staff_member_required` uses on the two dashboards. Takes a DRF token or a
  session, requires `is_staff`, and refuses in the caller's own idiom — JSON
  for an API client, the usual admin login redirect for a browser.
- **JSON branch on every dashboard mutation.** 44 branches, each returning
  before any `messages.*` call. The HTML path is untouched, so the old
  templates still work.
- **Token login returns `is_staff`**, so a non-staff account is refused at the
  login screen instead of hitting 403 on every later request.
- **The four loose dashboards are staff-only now** — reports builder, completed
  reports, quotes dashboard, tickets dashboard. ⚠️ **This locks out any
  non-staff distributor or customer who used them.** Two quotes test classes
  named their user "staff" without the flag and now set it.
- **`backup_documents`** is staff-gated and no longer `@csrf_exempt`.
- **JSON read endpoints** for products, customers, reports, orders, proposals
  and tickets, plus report PDF generate/regenerate.

### The app

Scaffold, sidebar shell, token auth, `useUrlState`, and seven screens:
Products, Customers, Users, Reports, Orders, Proposals, Tickets.

Each screen was driven in a real browser against the local database: a cold
deep link opens the right record on the right tab, changing a filter rewrites
the URL, and a hard refresh restores the identical view.

Reports holds two views in one screen — the completed reports, and the
report types. A report opens a panel with its answers grouped by section,
flag options in red, and signatures and attachments inline. The PDF column
builds a missing PDF, rebuilds a stale one, and opens an existing one.

The dev database holds no proposals, so Proposals was checked against a
test proposal made for the purpose and removed afterwards.

## Next up

Follow the parity plan's order of work. Step 1 is the shared groundwork:
the backend contract fixes, then the frontend form kit. Step 2 is the
report-type builder.

## How to pick this up

```bash
# Django, on the LOCAL database — the default settings.py is Railway production
cd ~/Documents/GitHub/geller.website
.venv/bin/python manage.py runserver 8912 --settings=chemicaldatasheets.settings_dev

# The app
cd ~/Documents/GitHub/geller-admin-app
npm run dev          # http://localhost:5273
```

Sign in as `uitest` / `uitest-pw-12345`. A token for curl:

```bash
curl -s -X POST http://localhost:8912/get_auth_token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"uitest","password":"uitest-pw-12345"}'
```

Checks: `.venv/bin/python manage.py test --noinput` in the Django repo;
`npx tsc --noEmit`, `npm test` and `npm run build` in the app.

## The rule the app exists to keep

Screen state lives in the URL — selection, tab, search, filter, sort, page.
Always through `useUrlState` (`src/lib/use-url-state.ts`), never `useState`,
and never a domain object in react-router's `location.state`. Eleven tests
hold that line, including a round trip that rebuilds a view from its link.

Defaults are absent from the URL rather than spelled out, so `/customers` is
the canonical link rather than `/customers?view=customers`.

## Things worth knowing, found the hard way

- The dashboards *look* like JSON APIs — no `render()` calls anywhere — but
  they are not: ~50 `redirect()` against 17 `JsonResponse`. The mutations are
  form handlers.
- A PDF route is behind the token gate, so a plain `<a href>` cannot reach
  it: a navigation sends no Authorization header. Each PDF helper fetches
  the file and opens an object URL. **Revoke that URL on a timer, never on
  the line after `window.open`** — the new tab has not loaded it yet when
  `window.open` returns.
- `Distributor` has **no `name` field**. It is `businessname`, lowercase, with
  a camelCase property shim a queryset cannot use. `Customer.businessName` is
  genuinely camelCase. They differ.
- A `post_save` signal on `User` already creates a `Profile` *and* a token.
  Creating either again trips a unique constraint.
- `PasswordResetForm` skips any account without a usable password, so
  `set_unusable_password()` plus an invitation email silently sends nothing.
  New users get a long random password instead.
- Answer fields are `text_answer` / `file_answer` / `signature_answer`;
  `QuestionOption.text`; `ReportSection.name`. Not what their names suggest.
- An order line's `soh` and `max_stock_level` are snapshots from when the
  order was placed, not today's stock. A proposal line freezes the product's
  name, code, price and cost-in-use the same way.
- `createMemoryRouter` builds a `Request` per navigation, and jsdom's
  `AbortSignal` is not the one Node's fetch accepts. Use `MemoryRouter` in
  tests instead — patching the globals does not work.
- `~/Documents/GitHub/geller-admin` is an unrelated 2017 React 16 app. Not a
  predecessor. Leave it alone.
