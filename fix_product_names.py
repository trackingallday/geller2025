import csv

original = {}
with open('/Users/rimu/Downloads/Product-2026-05-24.csv', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        original[row['id']] = row['name']

changes = []

with open('/Users/rimu/Downloads/Website_update_22_05_2026_upload_UTF8 (1).csv', encoding='utf-8') as f_in, \
     open('/Users/rimu/Downloads/Website_update_22_05_2026_upload_UTF8_fixed.csv', 'w', encoding='utf-8', newline='') as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
    writer.writeheader()
    for row in reader:
        if row['id'] in original and row['name'] != original[row['id']]:
            changes.append({'id': row['id'], 'original_name': original[row['id']], 'changed_name': row['name']})
            row['name'] = original[row['id']]
        writer.writerow(row)

# Write the changes report CSV
with open('/Users/rimu/Downloads/product_name_changes.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'original_name', 'changed_name'])
    writer.writeheader()
    writer.writerows(changes)

print(f"Fixed {len(changes)} name changes. Report saved to product_name_changes.csv")
