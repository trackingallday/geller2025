# Geller Admin App — progress and next steps

Last written 2026-11-08.
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

## Parity plan: where it stands

Plan: `/Users/rimu/.claude/plans/omg-you-have-totally-atomic-acorn.md`.
Work its "Order of work" top to bottom. Measure each screen against its
feature table: every row must be doable in the app.

| Step | State | Commits |
|---|---|---|
| 1. Shared groundwork | **Done** | site `24cc536`, app `1cc8231` |
| 2. Report-type builder | **Done, driven in the browser** | site `63b2e8f` `cce0414`, app `26b1248` |
| 3. Products, made editable | **Done, driven in the browser** (all but Geller AI sync's success path: no local Geller AI runs; the failure path works. Sync all was not started, as it runs through every product) | app `bd7fb11` |
| 4. Customers, made editable | **Done, driven in the browser** (details, group, contacts, wall chart, groups, members, group prices, import check and real import) | site `f706fa8`, app (see log) |
| 5. Proposals builder | **Done, driven in the browser** (all but Send PDF, which could send real mail through Postmark in dev; unit-tested with a mock) | site `cbca24f` |
| 6. Tickets actions | **Done, driven in the browser** | site `665e163` |
| 7. Completed reports gaps | **Done, driven in the browser** (email unit-tested only; "create sample" left out on purpose, see `4c7c818`) | site `4c7c818` `6ec76a6` |
| 8. Orders actions, Users/distributors editing | **Done, driven in the browser** (create, edit, flags, link and unlink people and customers, "Email everyone" on a distributor with no email addresses. The single-user reset button and a real reset email are unit-tested only, because dev sends real mail) | site `369a564` `095b4db`, app `2d0a417` `f79e05d` |
| 9. Retire the old panels | Only after the user confirms each is in use | |

### What step 1 gives every later screen

Backend (`chemsapp/staff_api.py`): `formset_errors_response` keys formset
errors as `"<row>.<field>"`. Variant save answers the `{ok, data}` envelope
to a JSON caller. Geller AI sync reads JSON bodies. Prices carry `name` and
`min_quantity`, and the reference data lists `sizes`.

App kit, reuse it rather than writing new:
- `src/lib/form-data.ts`: `toFormData` (M2M as repeated keys, booleans
  as "true"/"false", a `File` replaces, `null` clears, `undefined` leaves),
  `toFormset` (management form, existing rows first), `formsetOrder`.
- `src/lib/field-errors.ts`: `fieldError`, `formErrors`, `rowFieldError`.
- `src/lib/search.ts`: the dashboards' picker searches.
- `src/components/shared/`: `SearchPicker`, `FileField`,
  `RichTextField` (TipTap, same HTML as CKEditor), `ConfirmDialog`
  (`useConfirm()`).
- `useReferenceData()` in `features/products/hooks/useProducts.ts`.

### What step 2 built

- Backend: `reports/builder.py` holds the shared copy, reorder and
  assignment logic. The old Django pages now call it too.
  `reports/builder_api_views.py` holds the JSON API. Every write answers
  with the whole builder tree.
- App: `/reports/types/:id?tab=build|preview|assign|settings&question=`,
  `/reports?view=types&category=`, `/reports/assign?q=&assigned=1`.
- The pattern to copy for later editors: `useBuilderWrite` in
  `features/reports/hooks/useBuilder.ts` puts the server's answer
  straight into the cache. A local draft resets when the server's copy
  changes, as in `QuestionEditor`. Field errors are read with
  `fieldError(mutation.error, "field")`.

### Lessons from driving it (apply them to every later screen)

- **Drive every action in the browser.** All tests passed, yet two
  drag-and-drop bugs showed up only in the browser.
- dnd-kit: read the in-progress layout from a ref, not from state. A
  quick drop can arrive before React re-renders a drag-over. Use
  container-first collision, as in `BuilderCanvas.tsx`.
- An update endpoint must fall back to the stored value for any field the
  caller leaves out (`_fields` in `builder_api_views.py`). Otherwise a
  partial save silently unticks a checkbox.
- Test data made in the dev database is removed afterwards. The dev
  database holds 5 report types, 0 quotes, 0 customer groups and 0 active application types; add test ones to drive group pricing or dilutions, then remove them.

## Next step: step 9, retire the old panels

Do this in small steps. Write progress here after each one. Then stop so
the user can `/clear` before the context grows large.

1. Do not remove any panel yet. First, ask the user which old panels are
   still in use. The panels are: `/product-dashboard/`,
   `/customer-dashboard/`, `/reports/`, `/reports/completed/`,
   `/quotes/dashboard/`, `/tickets/dashboard/`.
   **Answer (2026-11-08):** the user says that all six panels are in use.
   The admin header (`templates/admin/base_site.html`) and the tickets and
   quotes nav bars link to them. As a result, each panel must have full
   parity in the app before its URL changes.
   **Decision (2026-11-08):** do not retire, redirect or remove any old
   panel until the client has fully tested the new admin app. The old
   panels and the app run side by side until then. Step 2 below waits for
   the client's approval.
   **Parity check (2026-11-08), done by code, not in the browser:**
   - Each write URL of the six panels has a matching call in the app.
     The bulk `save-variants` is not used. The app saves one variant at
     a time with `variant/<id>/save/`, so no feature is missing.
   - Each search filter (`exclude_*`) of the old pickers is in
     `src/lib/search.ts`.
   - Gaps found, all small. The API already accepts each filter, so the
     work is in the app only:
     1. Tickets: no **customer** filter. The old dashboard has one, and it
        narrows when you select a distributor.
     2. Reports and Browse PDFs: no **customer** filter. Both old pages
        have one.
     3. Proposal detail: "Customer" is plain text. The old page links to
        the customer. A link to `/customers?customer=<id>` is better.
     **Closed (2026-11-08).** Tickets, Reports, Browse PDFs, Orders and
     Proposals now have a customer filter. Tickets also has an assignee
     filter. The Orders filter was a fourth gap: the parity check above
     missed it, because Orders is not one of the six panels. The proposal
     customer is now a link.
   - Search was improved on all list screens and pickers (2026-11-08):
     - `search_q` in `chemsapp/staff_api.py` finds every word, in any field
       and in any order. Add new searches with it, not with `icontains`.
     - `CUSTOMER_SEARCH_FIELDS` is the one list for the customer list and
       the customer pickers. Each list now searches more fields.
     - `SearchBox` is the one search box. It waits 250 ms and has a clear
       button. Escape also clears it. `CustomerFilter` and `AssigneeFilter`
       are in `src/components/shared/FilterPicker.tsx`.
     - Report types have a search box, `?tq=`, that runs in the browser.
     - Driven in the browser: Tickets, Reports, report types, Orders,
       Customers. Checked by unit test and API only: Products, Users,
       Distributors, Groups. The proposal link and the Proposals filter
       are not driven, because the dev database holds 0 quotes.
     - Results: Django 476 tests with the same 3 chromedriver errors. App
       108 tests, `tsc` and the build pass.
   - Not part of the six panels, but listed in the parity plan under
     "Admin extras": the variants XLSX import, the dilutions XLSX import,
     and the application-types settings. None is in the app. They are in
     `/admin/` now.
2. After the client approves, for each panel that the user lets you retire, do one panel per session:
   - Make sure that each row of its feature table in the parity plan is
     in the app.
   - Redirect its URL to the matching app screen, or remove it. Ask the
     user which.
   - Run the Django tests. Record the result here.
3. Before a merge, the user must decide about the four dashboards that are
   now staff-only. Non-staff distributors and customers cannot open them.

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
