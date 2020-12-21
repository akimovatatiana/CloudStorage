from rest_framework import serializers


class FileSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(required=False, allow_blank=True, max_length=100)
    file = serializers.FileField()
    uploaded_at = serializers.DateTimeField()
    size = serializers.CharField(max_length=255)
