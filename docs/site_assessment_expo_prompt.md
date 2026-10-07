# Prompt for the Expo app session (geller-report-app)

Copy everything below the line into a fresh Claude Code session opened in the
`geller-report-app` repo.

---

We've added a "Site Assessment" feature to the Geller backend
(geller.website, Django) and need the Expo field-rep app updated to use it.
Backend work is done and deployed to this branch's backend; nothing on your
side needs to touch the backend repo.

## Context: what Site Assessment is

Reps currently use this app to fill out "reports" (audits/inspections) for
existing Geller customers. The client now wants a second kind of report:
a **Site Assessment**, done on a visit to a **prospective** business (a
Restaurant, Café, Motel, Rest Home, B2B, etc.) that usually is NOT yet a
Geller customer. The flow:

1. Rep picks a site category (Restaurant / Café / Motel / Rest Home / B2B /
   etc.) from a list.
2. Rep searches for the business by name (Google-style autocomplete) — this
   fills in the address and a link to view the business on Google Maps. If
   no match, the rep can enter the business details manually.
3. Rep answers a preset set of questions for that category and attaches
   photos — this part reuses the exact same dynamic report-filling UI you
   already have for normal reports (same question types: text, textarea,
   select, radio, checkbox, yesno, file, signature, date, number; same
   conditional show/hide logic; same photo capture).
4. On submit, the backend automatically pushes the lead into OnePageCRM and
   emails sales — you don't need to do anything for this, it's entirely
   server-side.

## What's reused vs. new

Everything about rendering/answering questions, photo capture, and
submitting a report is **unchanged** — a Site Assessment is still just a
`Report` against a `ReportType`, built from the same `sections`/`questions`
structure your app already renders. The only new things are:

1. **`ReportType.category`** — every report type now has a `category` field,
   either `"standard"` (existing audit/inspection types, keep working
   exactly as today) or `"site_assessment"` (new). Use this to show
   Site Assessment types in their own picker rather than mixed in with
   the normal report-type list.
2. **A `Prospect`** — a lightweight object (business_name, address, phone,
   google_place_id, maps_link, notes) that a Site Assessment report links
   to, in place of (or alongside) a `Customer`.
3. Google Places Autocomplete search for the business name, to fill the
   Prospect fields. The project already has a Google API key configured
   for Maps/Places — `GOOGLE_API_KEY` in the Django backend's settings
   (ask the user, Rimu, for this key's actual value to put in the Expo
   app's env/config; don't invent one).

## API contract (already live on the backend)

Base path: `/reports/api/...`. Auth: DRF Token auth, same as everything else
you already call — `Authorization: Token <token>` header.

### List report types by category

`GET /reports/api/report-types/`

Each report type object now includes a `category` field: `"standard"` or
`"site_assessment"`. Filter client-side (or ask the backend to add a
`?category=` query param if you'd rather filter server-side — it doesn't
exist yet, so flag this back to Rimu if you want it added) to build the
"choose a Site Assessment type" screen (Restaurant / Café / Motel / Rest
Home / B2B / etc. — each of these is just a `ReportType` row with
`category: "site_assessment"`).

### Get a report type's questions (identical to existing reports)

`GET /reports/api/report-types/{id}/questions/`

No changes — same shape you already consume for normal reports.

### Create + submit a Site Assessment report

`POST /reports/api/report-types/{report_type_id}/create/`

This is the same endpoint you already use to create+submit any report. The
only new thing is an optional nested `prospect` object in the body instead
of (or alongside) `customer`:

```json
{
  "prospect": {
    "business_name": "Tony's Pizza",
    "address": "123 Main St, Auckland",
    "phone": "021 555 1234",
    "google_place_id": "ChIJ...",
    "maps_link": "https://www.google.com/maps/place/?q=place_id:ChIJ..."
  },
  "inspection_date": "2026-10-03",
  "answers": [
    { "question_id": 101, "text_answer": "yes" },
    { "question_id": 102, "selected_option_ids": [5, 6] },
    { "question_id": 103, "attachment": "data:image/jpeg;base64,/9j/4AAQ..." }
  ]
}
```

Notes:
- `prospect` is a plain object, not an ID — the backend creates (or reuses,
  by `google_place_id` if you send one) the Prospect row for you.
- `google_place_id` and `maps_link` are optional — if the rep enters the
  business manually (no Place match), just omit them and fill in
  `business_name`/`address`/`phone` from what the rep typed; put any extra
  free text in `notes`.
- Everything else about this call — `inspection_date`, `answers` (including
  base64 photo uploads via `attachment`/`attachments`), `compliance_manager`,
  `store_compliance_manager` — is identical to how you already call this
  endpoint for standard reports.
- You still get back the full created `Report` object in the response,
  including a `prospect` field now instead of (or alongside) `customer`.

### Reading back a report's prospect

`GET /reports/api/reports/{id}/` and `GET /reports/api/reports/` both now
include a `prospect` field on each report (same shape as what you sent to
create it, when present), alongside the existing `customer`/`distributor`
fields.

## Google Places Autocomplete

This is entirely client-side — Places Autocomplete + Place Details calls
straight from the Expo app to Google's API using the `GOOGLE_API_KEY`
mentioned above (ask Rimu for the actual key value). The backend does not
proxy this; there's no new backend endpoint for business search. On
selecting a place, pull `name` → `business_name`, `formatted_address` →
`address`, `formatted_phone_number` → `phone` (if available), `place_id` →
`google_place_id`, and build `maps_link` as
`https://www.google.com/maps/place/?q=place_id:<place_id>`.

If no match is found (or the rep prefers), fall back to a manual entry form
for the same four fields (business_name, address, phone, notes) — the
`create` API call doesn't care which path was used.

## Navigation changes (requested alongside this feature)

1. Rename the **"Training"** tab to **"Toolkit"**.
2. Move the existing **"Proposal"** button onto the Toolkit tab, renamed
   **"Create Proposal"**.
3. Add a new **"Site Assessment"** button on the Toolkit tab. Tapping it
   opens the site-category picker (the list of `ReportType` rows where
   `category === "site_assessment"`, per the API section above), which then
   flows into: business search/manual entry → dynamic question form (reuse
   existing) → photo capture (reuse existing) → submit.

## What to figure out / ask about

- Where in the existing codebase report types are fetched/cached and report
  forms are rendered, so Site Assessment reuses that code path rather than
  duplicating it.
- Whether to filter `category` client-side or ask the Django backend to add
  a `?category=` query param to `GET /reports/api/report-types/` — either
  is fine, flag back to Rimu if you want the backend changed.
- The actual Google API key value (ask Rimu directly — it already exists
  in the Django project's settings for Maps/Places use, scoped correctly,
  no new Google Cloud setup needed).
- Whether "manual entry" should be its own distinct screen/step or just an
  always-visible fallback form under the search box.

Please start by exploring the existing report-type list, report-filling,
and photo-capture screens/components in this repo so you can reuse them,
then come back with a short plan before writing code.
