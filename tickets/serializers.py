from rest_framework import serializers
from chemsapp.serializers import UserSerializer
from .models import Ticket, TicketReply, TicketImage


class TicketReplySerializer(serializers.ModelSerializer):
    author = UserSerializer(many=False, read_only=True)

    class Meta:
        model = TicketReply
        fields = ('id', 'author', 'body', 'created_at')


class TicketImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = TicketImage
        fields = ('id', 'image_url', 'uploaded_at')

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class TicketSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(many=False, read_only=True)
    assigned_to = UserSerializer(many=False, read_only=True)
    replies = TicketReplySerializer(many=True, read_only=True)
    images = TicketImageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = (
            'id', 'created_by', 'customer', 'assigned_to', 'status',
            'ticket_type', 'source_report',
            'subject', 'body', 'created_at', 'updated_at', 'replies', 'images',
        )


class TicketCreateSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField()
