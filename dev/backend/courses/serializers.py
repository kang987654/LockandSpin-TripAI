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
        fields = ('day_number', 'sequence', 'is_locked', 'place')


class TravelCourseSerializer(serializers.ModelSerializer):
    slots = CourseDetailSerializer(many=True, read_only=True)

    class Meta:
        model = TravelCourse
        fields = ('id', 'title', 'destination', 'start_date', 'duration_days', 'preferences', 'created_at', 'slots')
