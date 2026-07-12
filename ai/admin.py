from django.contrib import admin
from django.db.models import Count
from django.utils.html import escape, format_html, mark_safe

from ai.models import AIThread, AIMessage


def _bubble(message):
    is_user = message.role == 'user'
    meta_bits = [message.created_at.strftime('%d %b %Y %H:%M:%S')]
    if message.metadata.get('has_image'):
        size = message.metadata.get('image_size_bytes')
        meta_bits.append('photo attached ({} KB)'.format(size // 1024) if size else 'photo attached')
    usage = message.metadata.get('usage') or {}
    if usage.get('input_tokens') or usage.get('output_tokens'):
        meta_bits.append('{}/{} tokens in/out'.format(
            usage.get('input_tokens', '?'), usage.get('output_tokens', '?')))
    status = message.metadata.get('upstream_status')
    if status and not (200 <= status < 300):
        meta_bits.append('upstream error {}'.format(status))

    return (
        '<div style="display:flex; justify-content:{align};">'
        '<div style="max-width:70%; margin:6px 0; padding:10px 14px; border-radius:12px;'
        ' background:{bg}; color:{fg}; white-space:pre-wrap; word-break:break-word;'
        ' font-size:13px; line-height:1.5;">'
        '<div style="font-size:11px; opacity:0.75; margin-bottom:4px;">{who} &middot; {meta}</div>'
        '{content}'
        '</div></div>'
    ).format(
        align='flex-end' if is_user else 'flex-start',
        bg='#1a6b54' if is_user else '#f0f0f0',
        fg='#ffffff' if is_user else '#222222',
        who='User' if is_user else 'GellerIQ',
        meta=escape(' · '.join(meta_bits)),
        content=escape(message.content) or '<em>(no text)</em>',
    )


@admin.register(AIThread)
class AIThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'kind', 'title', 'message_count', 'created_at')
    list_filter = ('kind', 'created_at')
    search_fields = ('title', 'user__username', 'user__email', 'messages__content')
    date_hierarchy = 'created_at'
    fields = ('user', 'kind', 'title', 'created_at', 'updated_at', 'conversation')
    readonly_fields = ('user', 'kind', 'title', 'created_at', 'updated_at', 'conversation')

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_message_count=Count('messages', distinct=True))

    def message_count(self, obj):
        return obj._message_count
    message_count.admin_order_field = '_message_count'

    @admin.display(description='Conversation')
    def conversation(self, obj):
        messages = list(obj.messages.all())
        if not messages:
            return 'No messages captured.'
        return mark_safe(
            '<div style="max-width:900px;">{}</div>'.format(
                ''.join(_bubble(m) for m in messages)))

    def has_add_permission(self, request):
        return False


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread', 'role', 'short_content', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'thread__title', 'thread__user__username')
    readonly_fields = ('thread', 'role', 'content', 'metadata', 'created_at', 'updated_at')

    def short_content(self, obj):
        return obj.content[:80]

    def has_add_permission(self, request):
        return False
