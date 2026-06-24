from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import UserPreference, UserVetoCategory

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        # Create default preference
        UserPreference.objects.create(user=user)
        return user


class UserPreferenceSerializer(serializers.ModelSerializer):
    preferred_themes = serializers.SerializerMethodField()
    veto_categories = serializers.SerializerMethodField()
    id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = UserPreference
        fields = ('id', 'username', 'email', 'preferred_themes', 'preferred_pace', 'veto_categories')

    def get_preferred_themes(self, obj):
        if not obj.preferred_themes:
            return []
        return [t.strip() for t in obj.preferred_themes.split(',') if t.strip()]

    def get_veto_categories(self, obj):
        # Retrieve veto categories from UserVetoCategory
        vetos = UserVetoCategory.objects.filter(user=obj.user)
        return [v.category_code for v in vetos]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

from users.models import Friendship

class FriendshipSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = ('id', 'from_user', 'to_user', 'status', 'created_at')
