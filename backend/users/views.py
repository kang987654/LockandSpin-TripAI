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

from users.models import Friendship
from users.serializers import FriendshipSerializer, UserSerializer
from django.db.models import Q

class UserSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.GET.get('q', '').strip()
        if not query:
            return Response([])
        users = User.objects.filter(Q(email__icontains=query) | Q(username__icontains=query)).exclude(id=request.user.id)[:10]
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class FriendshipView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # List friends (accepted) and pending requests
        user = request.user
        
        # Accepted friends (can be from_user or to_user)
        accepted = Friendship.objects.filter(
            (Q(from_user=user) | Q(to_user=user)) & Q(status='accepted')
        )
        
        # Pending requests received by me
        pending_received = Friendship.objects.filter(to_user=user, status='pending')
        
        # Pending requests sent by me
        pending_sent = Friendship.objects.filter(from_user=user, status='pending')

        return Response({
            'friends': FriendshipSerializer(accepted, many=True).data,
            'pending_received': FriendshipSerializer(pending_received, many=True).data,
            'pending_sent': FriendshipSerializer(pending_sent, many=True).data,
        })

class FriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        to_user_id = request.data.get('user_id')
        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            
        if to_user == request.user:
            return Response({"error": "Cannot send friend request to yourself."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if friendship already exists
        existing = Friendship.objects.filter(
            Q(from_user=request.user, to_user=to_user) | Q(from_user=to_user, to_user=request.user)
        ).first()

        if existing:
            return Response({"error": "Friendship or request already exists.", "status": existing.status}, status=status.HTTP_400_BAD_REQUEST)

        friendship = Friendship.objects.create(from_user=request.user, to_user=to_user, status='pending')
        return Response(FriendshipSerializer(friendship).data, status=status.HTTP_201_CREATED)

class FriendAcceptView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        friendship_id = request.data.get('friendship_id')
        try:
            friendship = Friendship.objects.get(id=friendship_id, to_user=request.user, status='pending')
        except Friendship.DoesNotExist:
            return Response({"error": "Pending request not found."}, status=status.HTTP_404_NOT_FOUND)
            
        friendship.status = 'accepted'
        friendship.save()
        return Response(FriendshipSerializer(friendship).data)

class FriendRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        friendship_id = request.data.get('friendship_id')
        try:
            # allow rejecting if we are the receiver (pending) OR deleting if accepted
            friendship = Friendship.objects.get(id=friendship_id)
            if friendship.to_user == request.user or friendship.from_user == request.user:
                friendship.delete()
                return Response({"status": "deleted"})
            else:
                return Response({"error": "Unauthorized."}, status=status.HTTP_403_FORBIDDEN)
        except Friendship.DoesNotExist:
            return Response({"error": "Friendship not found."}, status=status.HTTP_404_NOT_FOUND)
