# Apple Guideline 2.1 response — Geller Reports

Apple wants a screen recording plus six points of written context before
this build moves forward. This file has the exact steps and the exact
words to use.

## Part 1: What you must do yourself

Claude cannot record your screen or submit to App Store Connect. These
steps need you, on your Mac and your iPhone.

### Step A: Record the screen

1. Build the latest version and install it on a physical iPhone. Use
   TestFlight or `eas build` and a direct install, not the simulator.
   Apple rejects simulator recordings.
2. On the iPhone, open Control Center and press Record.
3. Record this flow, in order, with no cuts:
   - Launch the app from the home screen.
   - On the login screen, tap "Register Here".
   - Complete signup: name, business name, email, password.
   - Enter the 6-digit code from the verification email.
   - Show the Products tab (the main AppLead screen).
   - Open a product and tap through to its detail page.
   - Tap "Contact us" and show the contact form.
   - Tap the profile icon in the header.
   - In the Account dialog, show the name edit fields.
   - Tap "Delete account", type "DELETE ME", and tap "Delete account"
     to confirm. Show the app return to the login screen.
4. Stop the recording. Trim the start and end in the Photos app if you
   need to, but keep the full flow above in one take.
5. Export the video as an MP4 file.

> **CAUTION:** Do not use a test account that you still need. The
> delete step on camera actually erases that account.

### Step B: Submit the information to Apple

1. Sign in to App Store Connect.
2. Open your app, then open the version that is in review.
3. Find the resolution thread for this message (App Review usually
   opens one under the "Messages" or "Resolution Center" section of
   that version). Reply there with the written answers below, and
   attach the MP4 file to the reply.
4. Scroll to the **App Review Information** section of the same
   version page.
5. Find the **Notes** field in that section.
6. Paste the same written answers into the Notes field. Apple asks
   for this so future reviewers see the context without you having to
   explain it again.
7. Add a login for the reviewer in the **Sign-In Information** part of
   App Review Information:
   - Username: a working staff/distributor test account that already
     exists.
   - Password: the account's password.
   - **CAUTION:** App Review must be able to complete login without
     needing an emailed code. Give them an existing account (not a
     fresh signup), since they cannot receive your verification
     email.
8. Submit the reply.

## Part 2: The written answers

Copy each numbered block below into both the resolution thread and the
Notes field. They are separate App Store Connect fields in places, so
paste one answer at a time where the form is structured, or all seven
together into the free-text Notes field.

---

### 1. App purpose and audience

Geller Reports serves two groups of users.

The main audience is Geller's own staff and distributors in New
Zealand, who use the app for their daily work: site reports and
checklists, placing and tracking orders, safety data sheets, an AI
product-knowledge assistant, and customer messaging.

The second audience is potential new customers ("AppLeads"): people
who want to browse Geller's cleaning and chemical products, read
product information, and contact Geller's sales team. This group can
self-register in the app.

The problem the app solves: before this app, Geller's field staff and
customers depended on paper reports, email, and phone calls to find
product information and report site issues. The app puts this
information and these workflows on the phone the user already
carries.

### 2. Setup and main features

**New customers (AppLeads):**

1. Open the app and tap "Register Here" on the login screen.
2. Enter a name, business name, email, and password.
3. Enter the 6-digit code sent by email to finish signup.
4. Browse products, view details, and send a message with the
   "Contact us" form.
5. Manage the account from the profile icon: edit the name, or delete
   the account.

No login credentials are needed for App Review to see this flow — a
reviewer can self-register a new AppLead account in the app.

**Geller staff and distributors:**

Reviewer login: 
  - Username: apptest
  - Password: gellertest123`

After login, the app shows:

- Site reports: select a report type, answer the questions, and add
  photos or a signature as evidence.
- Orders: select a customer, scan or search for products, and place
  an order.
- GellerIQ: an AI assistant that answers product questions.
- Safety data sheets and product information sheets.
- Messages: a ticket-style thread with Geller's office.
- Proposals: build a quote for a customer from the product catalogue.

### 3. Account registration, login, and deletion

AppLead accounts support full self-service registration, login, and
deletion inside the app.

Registration needs an emailed 6-digit verification code before the
account is created, so no account exists for an email until the owner
of that inbox confirms it.

Deletion is in the app: tap the profile icon, then "Delete account",
type the confirmation phrase, and confirm. The account and its
personal data are removed immediately and the user returns to the
login screen. The screen recording shows this flow in full.

Geller staff and distributor accounts are created directly by Geller,
not through self-service signup, because they are tied to an existing
commercial account and employment relationship. A staff member who
wants an account removed contacts Geller directly, the same way they
would ask IT to remove email or other company system access.

### 4. User-generated content

The app does not have user-generated content that other users see.
Site reports, photos, signatures, and messages are private between
the user (or their business) and Geller, so there is no public feed,
no other-user content to view, and no content reporting or blocking
mechanism to build.

### 5. External services

- **Postmark** — sends the signup verification code email and other
  transactional email.
- **A Geller-operated AI service** (built on the Mastra framework) —
  powers the GellerIQ product-knowledge assistant. This service is
  run by Geller, not a public third-party AI product.
- **No payment processor.** The app does not sell anything and has no
  in-app purchases. Orders and proposals are created against a
  customer's existing commercial account with Geller and are settled
  outside the app, the same way a phone or email order is.
- **No third-party authentication provider.** Accounts and passwords
  are stored and checked by Geller's own backend.

### 6. Regional differences

The app works the same way in every region: no feature is turned off
or changed by country.

The product catalogue, safety data sheets, and distributor network
are specific to New Zealand, because Geller is a New Zealand company
that sells and distributes cleaning and chemical products only in New
Zealand. A user outside New Zealand can still install the app,
register as an AppLead, and browse the catalogue.

### 7. Regulated content

Geller is a registered manufacturer and distributor of commercial
cleaning and chemical products in New Zealand. The safety data sheets
and product information sheets in the app are Geller's own documents
for Geller's own products, published to meet New Zealand's
information requirements for hazardous substances (overseen by
WorkSafe New Zealand under the Hazardous Substances and New Organisms
Act). `[If you hold a specific registration number or certificate you
want to cite, add it here — otherwise delete this sentence.]`

---

## Gaps to fill before you send this

- Section 7 ends with an optional line for a certificate or
  registration number. Add it if you have one on hand; otherwise
  delete that bracketed sentence before sending.

## Plain text version for App Review Notes field

1. App purpose and audience

Geller Reports serves two groups of users.

The main audience is Geller's own staff and distributors in New Zealand, who use the app for their daily work: site reports and checklists, placing and tracking orders, safety data sheets, an AI product-knowledge assistant, and customer messaging.

The second audience is potential new customers ("AppLeads"): people who want to browse Geller's cleaning and chemical products, read product information, and contact Geller's sales team. This group can self-register in the app.

The problem the app solves: before this app, Geller's field staff and customers depended on paper reports, email, and phone calls to find product information and report site issues. The app puts this information and these workflows on the phone the user already carries.

2. Setup and main features

New customers (AppLeads):

1. Open the app and tap "Register Here" on the login screen.
2. Enter a name, business name, email, and password.
3. Enter the 6-digit code sent by email to finish signup.
4. Browse products, view details, and send a message with the "Contact us" form.
5. Manage the account from the profile icon: edit the name, or delete the account.

No login credentials are needed for App Review to see this flow — a reviewer can self-register a new AppLead account in the app.

Geller staff and distributors:

Reviewer login: username apptest, password gellertest123

After login, the app shows:

Site reports: select a report type, answer the questions, and add photos or a signature as evidence.
Orders: select a customer, scan or search for products, and place an order.
GellerIQ: an AI assistant that answers product questions.
Safety data sheets and product information sheets.
Messages: a ticket-style thread with Geller's office.
Proposals: build a quote for a customer from the product catalogue.

3. Account registration, login, and deletion

AppLead accounts support full self-service registration, login, and deletion inside the app.

Registration needs an emailed 6-digit verification code before the account is created, so no account exists for an email until the owner of that inbox confirms it.

Deletion is in the app: tap the profile icon, then "Delete account", type the confirmation phrase, and confirm. The account and its personal data are removed immediately and the user returns to the login screen. The screen recording shows this flow in full.

Geller staff and distributor accounts are created directly by Geller, not through self-service signup, because they are tied to an existing commercial account and employment relationship. A staff member who wants an account removed contacts Geller directly, the same way they would ask IT to remove email or other company system access.

4. User-generated content

The app does not have user-generated content that other users see. Site reports, photos, signatures, and messages are private between the user (or their business) and Geller, so there is no public feed, no other-user content to view, and no content reporting or blocking mechanism to build.

5. External services

Postmark — sends the signup verification code email and other transactional email.
A Geller-operated AI service (built on the Mastra framework) — powers the GellerIQ product-knowledge assistant. This service is run by Geller, not a public third-party AI product.
No payment processor. The app does not sell anything and has no in-app purchases. Orders and proposals are created against a customer's existing commercial account with Geller and are settled outside the app, the same way a phone or email order is.
No third-party authentication provider. Accounts and passwords are stored and checked by Geller's own backend.

6. Regional differences

The app works the same way in every region: no feature is turned off or changed by country.

The product catalogue, safety data sheets, and distributor network are specific to New Zealand, because Geller is a New Zealand company that sells and distributes cleaning and chemical products only in New Zealand. A user outside New Zealand can still install the app, register as an AppLead, and browse the catalogue.

7. Regulated content

Geller is a registered manufacturer and distributor of commercial cleaning and chemical products in New Zealand. The safety data sheets and product information sheets in the app are Geller's own documents for Geller's own products, published to meet New Zealand's information requirements for hazardous substances (overseen by WorkSafe New Zealand under the Hazardous Substances and New Organisms Act).
