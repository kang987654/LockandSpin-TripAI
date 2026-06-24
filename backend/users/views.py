from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from users.models import UserPreference, UserVetoCategory
from users.serializers import UserRegisterSerializer, UserPreferenceSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegisterSerializer


class UserPreferenceView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        pref, created = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(pref)
        return Response(serializer.data)

    def put(self, request):
        pref, created = UserPreference.objects.get_or_create(user=request.user)
        
        # Extract fields
        preferred_themes = request.data.get('preferred_themes', [])
        preferred_pace = request.data.get('preferred_pace', 'medium')
        veto_categories = request.data.get('veto_categories', [])

        # Update preferred_themes as comma-separated string
        pref.preferred_themes = ",".join(preferred_themes)
        pref.preferred_pace = preferred_pace
        pref.save()

        # Update veto categories
        UserVetoCategory.objects.filter(user=request.user).delete()
        for cat in veto_categories:
            UserVetoCategory.objects.create(user=request.user, category_code=cat)

        serializer = UserPreferenceSerializer(pref)
        return Response(serializer.data, status=status.HTTP_200_OK)

import os
class ConfigView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return Response({
            "kakao_javascript_key": os.environ.get('KAKAO_JS_KEY')
        })
