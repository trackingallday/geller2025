# Geller Admin App — progress and next steps

Last written 2026-11-16.
Original plan: `/Users/rimu/.claude/plans/look-at-how-in-ethereal-wand.md`
Parity plan (current): `/Users/rimu/.claude/plans/omg-you-have-totally-atomic-acorn.md`

## Where things stand

Two repositories, both on a branch, nothing merged and nothing pushed.

| Repo | Branch | Commits |
|---|---|---|
| `geller.website` | `admin-app-backend` | 28 new, on top of `0fd6380` |
| `geller-admin-app` | `main` (new repo) | 20 |

The full Django suite runs **476 tests with 3 errors**. Those 3 are
`reports.test_browser_integration`, which fail on a corrupt chromedriver
download and failed the same way before this work started. The app passes
108 tests, `npx tsc --noEmit` and `npm run build`.

**Steps 1 to 8 of the parity plan are done, so the next paragraph is
history.** It shows why the parity plan exists.

**⚠️ The screens were read-only copies, not replacements.** All seven
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
| 9. Retire the old panels | **On hold until the client has fully tested the app.** Parity gaps closed and search improved | site `539324c`, app `3747a10` |

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

## In progress: document versions and "Send documents" (2026-11-16)

The client asked for two features:

> "if we can add a area we can add a version number and date for the
> Product information sheet, SDS, sheet, MPI Approval and also the Label"

> "email a link directly from the admin for PI Sheet and SDS to a client
> so they can download and if they go back to this link it downloads the
> latest version"

The user also wants the send feature on its own sidebar entry, easy to use.

### Decisions (user, 2026-11-16)

- **Keep a history.** Each upload is stored with a version and a date.
  Staff can see and open old versions. The newest version is current.
- **Recipients:** staff type an email address, or search and pick a
  customer or any user. More than one recipient is allowed.
- **Several products in one email.** For each product, staff tick SDS,
  Info sheet, or both.
- **The email has SDS and Info sheet links only.** MPI approval and the
  label get versions, but they are not sent.

### Facts found

- Product files: `Product.infoSheet`, `Product.sdsSheet`,
  `Product.mpi_approval_sheet` (and `application_sheet`, not in scope).
- The label is per size: `ProductVariant.label` (`chemsapp/models.py:207`).
- The "latest" link exists already: `/product_download/<id>/<sds|info>/`
  (`download_product_document`, `chemsapp/views.py:1156`). It is public and
  serves the file that is on the product now.
- Mail goes through Postmark. Copy `mail_customer` in `chemsapp/views.py`.
  Dev sends real mail, so mock it in tests and in browser checks.
- The app edits product files in
  `features/products/components/editors/ComplianceEditor.tsx`.

### Design

- New model `ProductDocument`: `product` (FK, null for a label),
  `variant` (FK, only for a label), `kind`
  (`sds`, `info`, `mpi_approval`, `label`), `file`, `version` (text),
  `issued_on` (date), `uploaded_at`, `uploaded_by`.
- **The old file fields stay the "current" pointer.** An upload of a new
  version also sets `Product.sdsSheet` (and so on) to that file. As a
  result, the website, the download link and the old dashboard keep
  working with no change.
- A data migration makes one `ProductDocument` for each file that exists
  now, with a blank version and no date.
- New model `DocumentSend`: recipients, items (product, kind, and the
  version that was current at send time), message, `sent_by`, `sent_at`.
  Staff can then answer "which SDS revision did this client get?".
- The email links go to `/product_download/<id>/<kind>/`, so a later
  click always gives the newest file.

### Order of work (one step per session)

1. **Models and migrations.** `ProductDocument`, `DocumentSend`, the data
   migration, and the sync to the old file fields. Tests.
2. **Versions API.** List the versions of a product and of each size
   label. Upload a new version (file, version, date). Delete an old,
   non-current version. Tests.
3. **App: versions in the Compliance tab and on each size.** Show the
   current version and date, "Upload new version", and the history.
   Do a browser check.
4. **Send API.** `POST /staff-api/document-sends/` with emails, items and
   a message. `GET` gives the past sends. Postmark is mocked in tests.
   A product without the file cannot be sent.
5. **App: "Send documents" screen** on the sidebar. Recipients (search a
   customer or user, or type an email), products with SDS/Info ticks
   (disabled when the file is missing), a message, a preview, and Send
   with a confirm. Below that, the recent sends. Do a browser check with
   the send mocked, or ask the user for a safe address.
6. **Checklist and deploy.** Add both features to
   `ADMIN_APP_TEST_CHECKLIST.md`. Ask the user before the push. The
   deploy runs the new migrations by itself.

**Step 1: done (2026-11-17).**

- Models at the end of `chemsapp/models.py`: `ProductDocument`,
  `DocumentSend`, `DocumentSendItem`. Migrations `0034_product_documents`
  and `0035_backfill_product_documents`.
- `ProductDocument.POINTER_FIELDS` maps each kind to its old file field.
  `is_current` is true when the pointer field holds the file of the row.
  There is no separate "current" flag.
- `record_document_versions()` runs on `post_save` of `Product` and
  `ProductVariant`. It makes a row for a pointer file that has none. As a
  result, an upload through the Django admin or the old dashboard also
  goes into the history, with no version and no date.
- To add a version in step 2: make the `ProductDocument` row first, then
  set the pointer field and save the owner. The signal then finds the row
  and makes no duplicate.
- Local database after the backfill: 313 SDS rows, 252 info rows, 0 MPI,
  0 labels.
- Tests: `chemsapp/test_product_documents.py`, 10 tests. Full suite: 510
  tests, with the same 3 chromedriver errors.

**Step 2: done (2026-11-17).**

- File: `chemsapp/document_api_views.py`. Tests:
  `chemsapp/test_document_api.py`, 11 tests. Full suite: 521 tests, with
  the same 3 chromedriver errors.
- `GET /staff-api/products/<id>/documents/` gives
  `{product_id, documents: {sds, info, mpi_approval}, labels, kinds}`.
  Each list is newest first. `labels` has one entry for each size:
  `{variant_id, code, size, versions}`.
- Each version is `{id, kind, kind_label, variant_id, file_name, url,
  version, issued_on, uploaded_at, uploaded_by, is_current, send_count}`.
- `POST` (multipart) to the same URL uploads a version: `kind`, `file`,
  `version`, `issued_on` (YYYY-MM-DD), and `variant` for a label. The new
  version becomes current. A label without a size, or with a size of
  another product, gives 400.
- `POST /staff-api/product-documents/<id>/` changes `version` or
  `issued_on`. A field that you do not send keeps its value. Staff can
  use this to give the backfilled rows a version and a date.
- `DELETE` on the same URL removes an old version. The current version
  gives 409. The file stays in storage.

**Step 3: done (2026-11-18).**

- App files in `src/features/products/`:
  - `api/documents.api.ts`: fetch, upload, edit and delete of versions.
  - `components/editors/DocumentVersions.tsx`: `ProductDocumentVersions`
    (all documents of one product) and `DocumentVersions` (one document).
  - `components/editors/DocumentVersions.test.tsx`: 6 tests.
- The Compliance tab now starts with "Documents with versions": SDS, info
  sheet, MPI approval, and one box for the label of each size. Each box
  shows the current version and date, "Upload new version" (file, version,
  issue date), and "Show N older versions". Each row has Edit (version and
  date). Only an old version has Delete, with a confirm.
- An upload saves at once. It is not part of "Save compliance". For this
  reason the panel is above the form, not in it.
- The plain file fields of SDS, info sheet and MPI approval are removed
  from the form. "Other documents" keeps only the application sheet.
- The Label file field on the size editor (`VariantEditor.tsx`) is not
  changed. An upload there goes into the history with no version and no
  date, by the signal of step 1.
- App: 132 tests, `tsc` and the build pass.

- Check (2026-11-18): this session had no browser tool. For this reason
  the five checks used the API calls of the app, with `curl` against the
  dev server. All five passed:
  1. A new SDS upload became current. The old version moved to old.
  2. An edit of the version and date of a backfilled row worked.
  3. A delete of the current version gave 409. A delete of an old
     version worked.
  4. A label upload for one size worked. A size of another product gave
     400.
  5. `/product_download/200/sds/` gave the new file.
- The test uploads are removed from the dev database and `media/`.
- A check of the screen in a browser is still open. Add it to step 6.

**Next: step 4, the Send API.** Read `chemsapp/document_api_views.py`
first.

## In progress: Website Contacts screen (2026-11-16)

The client asked to see who downloads from the website or sends an
enquiry: name, company, date, and the product or the enquiry. These are
`Contact` rows. `sds_enquire` and `create_contact` in `chemsapp/views.py`
make them. The plan is in `~/.claude/plans/this-is-from-the-wiggly-clarke.md`.
The user decided: a new Contacts screen in the app, SDS downloads and
enquiries only. Info-sheet downloads are not logged.

**Backend: done, committed** (site `3ee150a`).

- `Contact.product` is a new nullable link (migration `0033_contact_product`).
  `sds_enquire` now sets it. Old SDS rows have no link. The API takes their
  product name from the `content` text.
- `chemsapp/contact_api_views.py`: `GET /staff-api/contacts/?q=&kind=&replied=&page=`,
  and `GET` and `PATCH /staff-api/contacts/<id>/`. PATCH changes `replied` only.
- Tests: `chemsapp/test_contact_api.py`, 11 tests.
- Migration `0033` runs by itself on deploy (pushed 2026-11-16).

**App screen: done, not committed (2026-11-16).**

- Files: `src/features/contacts/{api/contacts.api.ts,hooks/useContacts.ts,pages/ContactsPage.tsx}`.
- Route: `/contacts?q=&kind=sds|enquiry&replied=0|1&page=&contact=<id>`.
  Sidebar entry: "Website contacts" (icon `Mail`).
- Columns: Date, Name, Company, Email, Type, What, Replied. "What" is the
  product (a link when the row has `product_id`) or the message, cut short.
- A click on a row opens a panel with the full message and a `mailto:` link.
- The Replied box sends `PATCH {replied}` only. It does not open the row.
- Tests: `ContactsPage.test.tsx` (6 tests). App 126 tests, `tsc` and the
  build pass.
- `ADMIN_APP_TEST_CHECKLIST.md` has a new "Website contacts" section.

**Browser check: done (2026-11-16).** 20 of 20 checks passed, with no
page errors. Playwright drove the Chromium in `~/Library/Caches/ms-playwright`.
The checks covered every checklist item, the deep link to a panel, a
refresh, and the next page. Migration `0033` is now on the local
database. The dev database holds 3305 contacts. The 2 test rows are
removed. `sds_enquire` was not called, because it sends real mail to the
admins.

**Committed and pushed (2026-11-16):** app `4ac95a8`, site `bca6ff6`.

**Next step for Contacts:** ask the user before you push. A push to
`main` of the app deploys it. A push to `remove-frontend` deploys Django,
and the deploy runs migration `0033` by itself.

**Also open:** Application types step 4.3 (browser check). The checklist
still lists "The application-types settings" under "What is not in the
app". That line is wrong now. Remove it and add an "Application types"
section after the browser check.

## Next steps

Do this in small steps. Write progress here after each one. Then stop so
the user can `/clear` before the context grows large.

**Do not retire, redirect or remove any old panel.** The client must
fully test the new admin app first. Ask the user what to do first. The
open items are:

1. **Browser check of search and proposals: done (2026-11-08).** 20 of 20
   checks passed, with no page errors and no failed requests. The checks
   covered:
   - `/reports?view=types`: the header count changes, a refresh keeps it,
     and Escape restores it.
   - Search on Products, Users, Distributors and Groups.
   - The Proposals customer filter, a refresh with that filter, and the
     customer link on the proposal.

   The test proposals and test groups are removed. The dev database again
   holds 0 quotes and 0 groups. The Chrome extension was not connected, so
   Playwright drove the Chromium in `~/Library/Caches/ms-playwright`.
   The check found one fault, "1 report types". This fault is corrected.
   Next: item 2.
2. **Test checklist for the client: done (2026-11-08).** The file is
   `ADMIN_APP_TEST_CHECKLIST.md`. It has steps for each screen, cautions
   for real email and deletes, the items that stay in `/admin/`, and how
   to report a problem. It does not give the app URL. Add the URL before
   you send it to the client.
   Next: get the user's answers to items 3 and 4.
3. **Staff-only decision: closed (2026-11-08).** The user says: keep the
   four loose dashboards staff-only. No change is necessary.
4. **Admin extras: answered (2026-11-08).** The client expects only the
   **application-types settings** in the app. The variants XLSX import and
   the dilutions XLSX import stay in `/admin/`.
   **Next: build an Application types screen in the app.** The model is
   `ApplicationType` (`chemsapp/models.py:95`). The admin is
   `ApplicationTypeAdmin` (`chemsapp/admin.py:343`). The admin shows
   `name`, `category`, `value_kind`, `unit_volume_litres`, `unit_label`,
   `sort_order` and `is_active`. Staff edit `sort_order` and `is_active`
   in the list. The admin has a custom `change_list.html` and custom URLs.
   Read them first: they can hold a feature that the screen must also have.
   The custom admin URL is only the dilutions import. That stays in
   `/admin/`, so the screen needs no other feature.
   Do the work in small steps:
   1. **Done (2026-11-08).** File: `chemsapp/application_type_api_views.py`.
      Tests: `chemsapp/test_application_type_api.py` (9 tests). The
      endpoints:
      - `GET /staff-api/application-types/?q=` gives
        `{application_types, value_kinds}`.
      - `POST` to the same URL creates a type.
      - `GET`, `POST` and `DELETE` on `/staff-api/application-types/<id>/`.
        `POST` is a partial update: a field that you do not send keeps its
        value. As a result, the list can send only `{is_active}` or
        `{sort_order}`.
      - `DELETE` of a type with dilution rates returns 409. The message
        tells staff to set the type to inactive. Each row has
        `dilution_count`, so the screen can disable Delete.
      - `unit_volume_litres` is a string, or null.
      The full suite runs 485 tests with the same 3 chromedriver errors.
      Next: item 2.
   2. **Done (2026-11-08).** The screen is in `geller-admin-app`, in
      `src/features/application-types/`. The route is
      `/application-types?q=&type=<id>|new`. The sidebar entry is
      "Application types".
      - The list has a search box. Each row has an inline sort order and an
        Active checkbox. Each inline edit sends only its own field. The
        sort order saves when the field loses focus, or on Enter.
      - A click on a row opens a panel with all the fields. A save sends
        only the fields that changed. "New type" opens the same panel
        empty.
      - Delete is in the panel. It asks first. It is disabled when the type
        has dilution rates.
      - Tests: `ApplicationTypesPage.test.tsx` (12 tests). App 120 tests,
        `tsc` and the build pass. Nothing is committed.
      Next: item 3.
   3. Do a browser check. Add the screen to `ADMIN_APP_TEST_CHECKLIST.md`.
5. `tsconfig.tsbuildinfo` shows as changed in the app repo. It is a build
   file. It was left out of the commits.

## Step 9 record: retire the old panels

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
     - Driven in the browser: all list screens, the Proposals filter and
       the proposal customer link.
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
   **Answer (2026-11-08):** keep them staff-only.

## Deploy (2026-11-08)

- The app is live at https://geller-admin-app-production.up.railway.app.
- Railway service `geller-admin-app`, in the project `protective-simplicity`.
  It deploys each push to `main` of `trackingallday/geller-admin-app`
  (a private repo).
- `VITE_DJANGO_ORIGIN=https://admin.geller.co.nz` is set on the service.
  Vite reads it at build time, so a change to it needs a new deploy.
- Django (`geller2025`) deploys from the `remove-frontend` branch, not from
  `main`.
- Do not confuse `geller-admin-app` with the service `geller-admin`. That
  service is the old 2017 app.

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
