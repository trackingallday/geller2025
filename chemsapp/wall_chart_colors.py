"""Row colours derived from Product.wall_chart_color.

The wall chart PDF and the quote/proposal PDF both show a product row as a
full-strength stripe next to a light tint of the same hue. This module holds
that maths so the two documents cannot drift apart.
"""

DEFAULT_STRIPE = '#aaaaaa'
DEFAULT_TINT = '#f5f5f5'


def row_colors(wall_chart_color):
    """Return (stripe_color, tint_color) for one product colour.

    `wall_chart_color` is a '#rrggbb' string. The stripe is the product colour
    at full strength. The tint is the colour mixed with 85% white. A blank or
    invalid value gives the neutral grey defaults.
    """
    color = wall_chart_color or ''
    try:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
    except (ValueError, IndexError):
        return DEFAULT_STRIPE, DEFAULT_TINT

    stripe = '#{:02x}{:02x}{:02x}'.format(r, g, b)
    tint = '#{:02x}{:02x}{:02x}'.format(
        int(255 * 0.85 + r * 0.15),
        int(255 * 0.85 + g * 0.15),
        int(255 * 0.85 + b * 0.15),
    )
    return stripe, tint
