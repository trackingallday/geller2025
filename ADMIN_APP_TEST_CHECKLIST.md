# Geller Admin App — test checklist

Use this checklist to test the new admin app before the old staff pages
are turned off. Each screen has short steps. Tick each box when the step
works.

The old pages stay on until you approve the app. You can use the old
pages and the app at the same time.

## Before you start

1. Sign in to the admin app with your staff username and password.
2. Make test records with a name that starts with `TEST`. For example,
   `TEST Customer` or `TEST Product`. Then you can find and remove them
   easily after the test.
3. Keep a note of each problem that you find (see "How to report a
   problem" at the end).

CAUTION: Some buttons send real email. Send test emails only to your own
email address.

CAUTION: A delete in the app is permanent. Delete only your `TEST`
records.

## Things to try on every screen

- [ ] Type two words in the search box, in any order. The list shows the
      records that contain both words.
- [ ] Press Escape in the search box. The search clears.
- [ ] Open a record, then refresh the browser. The same record stays open.
- [ ] Copy the address from the browser and open it in a new tab. The
      same screen and record open.
- [ ] Use the browser Back button. The previous screen opens.

## Products

- [ ] Open a product. Change a field on the Product tab and save. Refresh.
      The change stays.
- [ ] Add and remove a category, a subcategory and a safety-wear chip.
- [ ] Upload a product image.
- [ ] On the Compliance tab, open "Documents with versions". Upload a new
      SDS to a `TEST` product, with a version and an issue date. The new
      file shows as the current version.
- [ ] Click "Show older versions". The previous SDS shows in the list.
- [ ] Edit the version and the date of a version. Refresh. The change
      stays.
- [ ] Delete an old version. The current version has no Delete button.
- [ ] Upload a label for one size of the product.
- [ ] Download the SDS from the website. You get the current version.
- [ ] Edit the MPI, application and procedure fields, and save.
- [ ] Add an equivalent product. Edit it. Delete it.
- [ ] On the Customers tab, add two customers. Remove one.
- [ ] Add a variant to a `TEST` product. Give it an image and a label.
      Edit it. Delete it.
- [ ] Add a dilution. Edit it. Delete it.
- [ ] Add a customer price. Edit it. Delete it.
- [ ] Add a group price. Edit it. Delete it.
- [ ] Sync one product to Geller AI. The result shows on the screen.

CAUTION: Do not start "Sync all" during working hours. It sends every
product to Geller AI and takes a long time.

## Customers

- [ ] Open a customer. Change the details and save. Refresh. The change
      stays.
- [ ] Add a contact. Set "receive report" on, then off. Delete the contact.
- [ ] Put a customer in a group. Then remove the group from the customer.
- [ ] Make a `TEST` group. Rename it and change its note.
- [ ] Add two customers to the `TEST` group. If a customer was in a
      different group, the screen tells you that it moved.
- [ ] Remove a customer from the group.
- [ ] Add a group price for some variants. The screen shows which prices
      it added and which it skipped. Remove one price.
- [ ] Delete the `TEST` group. The app asks you before it deletes.
- [ ] Download the wall chart PDF for a customer. Open it.
- [ ] Import customers from an `.xlsx` file. Do the check first. Read the
      result. Then do the real import only with test data.

## Users

- [ ] Open a user. Change the name or email and save.
- [ ] Turn a flag on and off for a `TEST` user.
- [ ] Make a `TEST` user and link it to a distributor. The user gets a
      password reset email. Use your own email address.
- [ ] Open the Distributors view. Open a distributor.
- [ ] Link a user and a customer to the distributor. Then unlink them.
- [ ] Use "Email everyone" only on a `TEST` distributor that holds your own
      email address.

## Reports

### Report types (the builder)

- [ ] Open the report types. Change between the standard and the site
      assessment tabs. The count in the header changes.
- [ ] Search the report types.
- [ ] Make a `TEST` report type. Set its name, description, category and
      prefix. Make it active.
- [ ] Add two sections. Rename one. Duplicate one. Drag them into a
      different order.
- [ ] Add one question of each type. Make one question required.
- [ ] Drag a question to a different place, and to a different section.
- [ ] Add options to a select question. Give an option a flag, a badge and
      a PDF. Drag the options into a different order.
- [ ] Make a question show only when a different question has an answer.
      Edit it again. The ticked values stay ticked.
- [ ] Open the Preview tab. The form looks as it does in the mobile app.
- [ ] On the Assign tab, assign the type to a customer and a distributor.
- [ ] Open the assignment grid (all customers and all types). Filter it.
      Turn an assignment on and off.
- [ ] Duplicate the `TEST` type. Delete the copy. The app tells you how
      many reports it will delete.

### Completed reports

- [ ] Filter by distributor, by customer and by date.
- [ ] Open a report. The flagged items, the address, the phone and the map
      link show.
- [ ] Regenerate the PDF of a report. Open the PDF.
- [ ] Select some reports and make their PDFs in one action.
- [ ] Email a report PDF to your own email address.
- [ ] Open the Browse PDFs view. Filter it by customer.

## Orders

- [ ] Make a `TEST` order. Add line items with a variant, a quantity, the
      stock on hand and a maximum.
- [ ] Change the fulfilment status and the notes.
- [ ] Submit the order. The PDF is made. After the submit, you cannot
      change the line items.
- [ ] Email the order PDF to your own email address.
- [ ] Filter the orders by customer.
- [ ] Delete the `TEST` order.

## Proposals

- [ ] Start a new proposal. Select a customer. The company, address and
      contact fill in.
- [ ] Add a line: select a product, a variant and a dilution. If there is
      only one choice, the app selects it.
- [ ] The suggested price shows where it comes from. Type a different
      price. The line shows that it is a custom price.
- [ ] The cost in use shows and changes when you change the price.
- [ ] Add a second line. Remove it.
- [ ] Save the proposal. The new proposal opens.
- [ ] Click the customer name on the proposal. The customer opens.
- [ ] Regenerate the PDF. Open it.
- [ ] Send the PDF to your own email address.
- [ ] Filter the proposals by customer.
- [ ] Delete the test proposal.

## Tickets

- [ ] Filter the tickets by distributor, customer, type and assignee.
- [ ] Open a ticket. Change its status.
- [ ] Assign the ticket: select a distributor, then a user. Then unassign
      it.
- [ ] Write a reply. The status changes.
- [ ] Upload an image to the ticket.
- [ ] Make a `TEST` ticket: select a customer, a distributor and a user.
      Add a subject and a message.
- [ ] Keep a ticket open. Reply to it from the mobile app. The reply shows
      in the admin app in about 5 seconds.
- [ ] If a ticket comes from a flagged report, click the report link. The
      report opens.

## Send documents

CAUTION: This screen sends real email. Send only to your own email
address.

- [ ] Type your email address and press Enter. The address shows as a
      chip.
- [ ] Type a bad address, for example `abc`. An error shows and the
      address stays in the box.
- [ ] Add a customer and a user with "Add a customer" and "Add a user".
      Then remove both chips.
- [ ] Add a product. The SDS and Info ticks show the current version and
      date. A document with no file shows "No file".
- [ ] Untick the Info sheet. Type a message. Open the preview. The
      preview shows the message and only the SDS link.
- [ ] Click Send and confirm. The email arrives with a link to the SDS.
- [ ] The send shows at the top of "Recent sends".
- [ ] Search "Recent sends" for your email address. Refresh. The search
      stays.

## Website contacts

This screen shows who downloaded an SDS or sent an enquiry on the website.

- [ ] Download an SDS from the website. The download shows at the top of
      the list, with the product name.
- [ ] Send an enquiry from the website. The enquiry shows at the top of
      the list.
- [ ] Filter by "SDS downloads", then by "Enquiries".
- [ ] Filter by "Not replied" and by "Replied".
- [ ] Search for a name, a company or a product.
- [ ] Click an enquiry. The full message shows in the panel.
- [ ] Tick "Replied" on a contact. Refresh the page. The tick stays.
- [ ] Click a product name. The product opens.

Old SDS downloads show the product name as text, not as a link.

## Application types

Dilution rates and proposals use these types.

CAUTION: Delete removes the type at once. You cannot undo a delete.

- [ ] Click "New type". Fill in the fields and click "Make the type". The
      type shows in the list and the count goes up.
- [ ] Search for a name, a category or a unit. Press Escape to clear the
      search.
- [ ] Change the sort order in the list and press Enter. Refresh the page.
      The new number stays.
- [ ] Untick "Active" in the list. Refresh the page. The tick stays off.
- [ ] Click a type. Change the unit label and click "Save". The list
      shows the new label.
- [ ] Open a type that has dilution rates. "Delete" is disabled. Set the
      type to inactive instead.
- [ ] Open a type with no dilution rates. Click "Delete", then "Cancel".
      The type stays. Delete only a test type that you made.

## What is not in the app

These items stay in the old Django admin (`/admin/`) for now:

- The variants `.xlsx` import.
- The dilutions `.xlsx` import.
- Approve or reject of a report.

Tell us if you need any of these in the app.

## How to report a problem

For each problem, write down:

1. The screen and the record (for example, "Products, TEST Product").
2. What you did, step by step.
3. What you saw.
4. What you expected to see.
5. A screenshot, if you can.

## When you finish

Remove your `TEST` records. Then tell us which screens are approved. We
turn off an old page only after you approve its screen in the app.
