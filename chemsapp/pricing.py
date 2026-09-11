"""Resolve the price a customer pays for a product variant.

The price chain has three levels. The customer price wins over the group
price. The group price wins over the recommended retail price.

1. The customer's own PricingVariant for the variant.
2. The GroupPricingVariant for the variant and the customer's group.
3. The variant's recommended retail price.

Any level can be missing. If no level has a price, there is no price to
suggest and the caller must ask for one — resolve_price never invents a
number.
"""


def resolve_price(product_variant, customer):
    """The price to suggest for one variant and one customer.

    Returns (price, source): price is a Decimal or None. source is the
    PricingVariant or GroupPricingVariant that set the price, or None when
    the price came from the variant's recommended retail price (or when
    there is no price at all — check `price is not None` to tell the two
    apart).
    """
    if product_variant is None:
        return None, None

    if customer is not None:
        customer_price = product_variant.pricing_variants.filter(
            customers=customer).first()
        if customer_price is not None:
            return customer_price.price, customer_price

        if customer.group_id is not None:
            group_price = product_variant.group_pricing_variants.filter(
                customer_group_id=customer.group_id).first()
            if group_price is not None:
                return group_price.price, group_price

    return product_variant.recommended_retail_price, None
