from django.db import models
from django.contrib.auth.models import User
from chemsapp.models import Customer


TICKET_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('read', 'Read'),
    ('cancelled', 'Cancelled'),
    ('completed', 'Completed'),
]


class Ticket(models.Model):
    created_by = models.ForeignKey(User, related_name='created_tickets', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, related_name='tickets', on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(
        User, related_name='assigned_tickets', on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    status = models.CharField(max_length=20, choices=TICKET_STATUS_CHOICES, default='pending')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Ticket #{self.pk} — {self.subject}'


class TicketReply(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='replies', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='ticket_replies', on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Reply by {self.author} on Ticket #{self.ticket_id}'


class TicketImage(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='ticket_images/')
    uploaded_by = models.ForeignKey(User, related_name='ticket_images', on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Image for Ticket #{self.ticket_id}'
