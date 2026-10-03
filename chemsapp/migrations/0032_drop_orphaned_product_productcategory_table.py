from django.db import migrations


class Migration(migrations.Migration):
    """Drop a stray, unused join table left over from before Product.productCategory
    was repointed (via through=) at ProductCategory.products' table.

    0001_initial created chemsapp_product_productCategory as a plain M2M table for
    Product.productCategory. 0006 later changed that field to use
    through=ProductCategory.products.through (chemsapp_productcategory_products)
    without ever dropping the original table. The orphaned table has 0 rows (verified
    in both the dev and production databases) and is untracked by Django's ORM and
    by manage.py sqlflush, but Postgres still enforces its old FK constraint — which
    breaks TRUNCATE-based test teardown (TransactionTestCase / LiveServerTestCase)
    with "cannot truncate a table referenced in a foreign key constraint".

    This is a database-only cleanup: no model fields change, so state_operations is
    empty and this migration is a no-op as far as Django's model state is concerned.
    """

    dependencies = [
        ('chemsapp', '0031_gelleraisyncrun'),
    ]

    operations = [
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS "chemsapp_product_productCategory";',
            reverse_sql=migrations.RunSQL.noop,
            state_operations=[],
        ),
    ]
