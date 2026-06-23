from rest_framework import serializers
from places.models import Place

class PlaceSerializer(serializers.ModelSerializer):
    themes = serializers.SerializerMethodField()

    class Meta:
        model = Place
        fields = ('id', 'name', 'category', 'themes', 'latitude', 'longitude', 'address', 'description', 'image_url', 'place_url', 'region')

    def get_themes(self, obj):
        if not obj.themes:
            return []
        return [t.strip() for t in obj.themes.split(',') if t.strip()]
