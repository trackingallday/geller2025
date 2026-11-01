"""Order operations shared by the Django admin, the mobile app's API and
the admin app, so a submitted or emailed order is the same whichever
screen did it.
"""
from django.conf import settings
from postmarker.core import PostmarkClient

from .utils import OrderPDFGenerator


def submit_order(order):
    """Mark an order submitted and build its PDF.

    Returns False when it was already submitted, leaving it untouched.
    """
    if order.submitted:
        return False
    order.submitted = True
    order.save()
    OrderPDFGenerator(order).generate_and_save()
    order.refresh_from_db()
    return True


def send_order_pdf_email(order, email_address):
    """Email the order's PDF via Postmark, building it first if missing.

    Raises on failure; RuntimeError when the PDF cannot be built.
    """
    if not order.pdf:
        OrderPDFGenerator(order).generate_and_save()
        order.refresh_from_db()
    if not order.pdf:
        raise RuntimeError('Failed to generate PDF')

    order.pdf.open('rb')
    pdf_content = order.pdf.read()
    order.pdf.close()

    customer = order.customer.businessName
    date = order.date.strftime('%Y-%m-%d')
    status = order.get_fulfilment_status_display()
    postmark = PostmarkClient(server_token=settings.POSTMARK_SERVER_API_TOKEN)
    email = postmark.emails.Email(
        From='noreply@geller.co.nz',
        To=email_address,
        Subject=f'Order {order.order_number} — {customer}',
        HtmlBody=f'''
            <html>
            <body>
                <h2>Your Order PDF</h2>
                <p>Please find attached your order:</p>
                <ul>
                    <li><strong>Order Number:</strong> {order.order_number}</li>
                    <li><strong>Customer:</strong> {customer}</li>
                    <li><strong>Date:</strong> {date}</li>
                    <li><strong>Status:</strong> {status}</li>
                </ul>
            </body>
            </html>
        ''',
        TextBody=f'Order Number: {order.order_number}\nCustomer: {customer}\nDate: {date}\nStatus: {status}',
    )
    email.attach_binary(content=pdf_content, filename=f'order-{order.order_number}.pdf')
    email.send()
