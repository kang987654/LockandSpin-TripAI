from rest_framework import serializers
from courses.models import TravelCourse, CourseMember, CourseDetail
from places.serializers import PlaceSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class CourseMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = CourseMember
        fields = ('user_id', 'username', 'email', 'role', 'joined_at')


class CourseDetailSerializer(serializers.ModelSerializer):
    place = PlaceSerializer(read_only=True)

    class Meta:
        model = CourseDetail
        fields = ('day_number', 'sequence', 'is_locked', 'place', 'slot_name')


class TravelCourseSerializer(serializers.ModelSerializer):
    slots = CourseDetailSerializer(many=True, read_only=True)
    members = CourseMemberSerializer(many=True, read_only=True)
    kept_places = serializers.SerializerMethodField()
    excluded_places = serializers.SerializerMethodField()

    class Meta:
        model = TravelCourse
        fields = ['id', 'user', 'title', 'destination', 'start_date', 'duration_days', 'preferences', 'status', 'ai_comment', 'created_at', 'slots', 'members', 'kept_places', 'excluded_places']
        read_only_fields = ['user', 'created_at']

    def get_kept_places(self, obj):
        from places.serializers import PlaceSerializer
        return PlaceSerializer([k.place for k in obj.kept_places.all()], many=True).data

    def get_excluded_places(self, obj):
        from places.serializers import PlaceSerializer
        return PlaceSerializer([e.place for e in obj.excluded_places.all()], many=True).data
