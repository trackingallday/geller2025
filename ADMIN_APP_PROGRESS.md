# Geller Admin App — progress and next steps

Written 2026-11-01, when a session limit stopped work mid-way.
Plan: `/Users/rimu/.claude/plans/look-at-how-in-ethereal-wand.md`

## Where things stand

Two repositories, both on a branch, nothing merged and nothing pushed.

| Repo | Branch | Commits |
|---|---|---|
| `geller.website` | `admin-app-backend` | 6 new, on top of `0fd6380` |
| `geller-admin-app` | `main` (new repo) | 4 |

The full Django suite passes: **375 tests, 3 errors**. Those 3 are
`reports.test_browser_integration`, which fail on a corrupt chromedriver
download and failed the same way before this work started. 34 tests were
added.

### Done and verified in the browser

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
- **The app itself**: scaffold, sidebar shell, token auth, `useUrlState`, and
  four working screens — Products, Customers, Users, Tickets.

Each screen was driven in a real browser against the local database: a cold
deep link opens the right record on the right tab, changing a filter rewrites
the URL, and a hard refresh restores the identical view.

## Next up

### 1. Finish Reports (half built)

`src/features/reports/` has `api/reports.api.ts`, `hooks/useReports.ts` and
`components/ReportList.tsx`. It all typechecks but nothing imports it.

Still needed: `components/ReportDetail.tsx`, `components/ReportTypeList.tsx`,
`pages/ReportsPage.tsx`, then the route and the sidebar flag.

### 2. Finish Orders and build Proposals (barely started)

`src/features/orders/api/orders.api.ts` exists. `src/features/quotes/` is empty.
Each needs api, hooks, a detail component and a page.

**An open question the agent hit and did not resolve:** it was revoking the
blob URL immediately after `window.open`, and stopped to ask whether the new
tab would have finished loading first. It would not, reliably. Revoke on a
timer, or after the tab's load event — do not revoke synchronously.

### 3. Wire the finished screens

In `src/app.tsx` add the routes, and in `src/components/shared/AppSidebar.tsx`
flip each section's `ready` flag to `true`. Tickets shows the pattern for both.

### 4. Then, per the plan

Retire the replaced Django templates and trim the button bar in
`templates/admin/base_site.html`. **Last**, and only once each replacement is
genuinely in use.

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
- `createMemoryRouter` builds a `Request` per navigation, and jsdom's
  `AbortSignal` is not the one Node's fetch accepts. Use `MemoryRouter` in
  tests instead — patching the globals does not work.
- `~/Documents/GitHub/geller-admin` is an unrelated 2017 React 16 app. Not a
  predecessor. Leave it alone.
