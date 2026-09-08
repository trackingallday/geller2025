"""Resolve the price a customer pays for a product variant.

A customer with a negotiated PricingVariant for the variant pays that price.
Every other customer pays the variant's recommended retail price. Either can
be missing, in which case there is no price to suggest and the caller must
ask for one — resolve_price never invents a number.
"""


def resolve_price(product_variant, customer):
    """The price to suggest for one variant and one customer.

    Returns (price, source): price is a Decimal or None, and source is the
    PricingVariant that set it, or None when the price came from the
    variant's own recommended retail price (or when there is no price at
    all — check `price is not None` to tell the two apart).
    """
    if product_variant is None:
        return None, None

    if customer is not None:
        pricing = product_variant.pricing_variants.filter(customers=customer).first()
        if pricing is not None:
            return pricing.price, pricing

    return product_variant.recommended_retail_price, None
