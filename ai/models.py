from django.contrib.auth.models import User
from django.db import models

from chemsapp.models import MyBaseModel


THREAD_KIND_CHOICES = [
    ('question', 'Question (workflow)'),
    ('reply', 'Follow-up (replyAgent)'),
    ('competitor', 'Competitor comparison'),
]

ROLE_CHOICES = [
    ('user', 'User'),
    ('assistant', 'Assistant'),
]


class AIThread(MyBaseModel):
    user = models.ForeignKey(User, related_name='ai_threads', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=20, choices=THREAD_KIND_CHOICES, default='question')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return "AIThread #{} ({}) {}".format(self.pk, self.user, self.title[:60])


class AIMessage(MyBaseModel):
    thread = models.ForeignKey(AIThread, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return "{} on thread #{}: {}".format(self.role, self.thread_id, self.content[:50])
