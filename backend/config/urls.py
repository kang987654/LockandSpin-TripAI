"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import RegisterView, UserPreferenceView, ConfigView, UserSearchView, FriendshipView, FriendRequestView, FriendAcceptView, FriendRejectView
from courses.views import TravelCourseViewSet, CourseMemberViewSet

router = DefaultRouter()
router.register(r'courses', TravelCourseViewSet, basename='course')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Config
    path('api/config/', ConfigView.as_view(), name='config'),
    
    # Auth
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Preferences
    path('api/user/preference/', UserPreferenceView.as_view(), name='user_preference'),
    
    # Friends & Search
    path('api/users/search/', UserSearchView.as_view(), name='user_search'),
    path('api/users/friends/', FriendshipView.as_view(), name='friends_list'),
    path('api/users/friends/request/', FriendRequestView.as_view(), name='friends_request'),
    path('api/users/friends/accept/', FriendAcceptView.as_view(), name='friends_accept'),
    path('api/users/friends/reject/', FriendRejectView.as_view(), name='friends_reject'),
    
    # Courses (Router)
    path('api/', include(router.urls)),
    
    # Community
    path('api/community/', include('community.urls')),
    
    # Course Members (Manual Nested Routes)
    path('api/courses/<int:course_pk>/members/', CourseMemberViewSet.as_view({'get': 'list', 'post': 'create'}), name='course_members'),
    path('api/courses/<int:course_pk>/members/<int:pk>/', CourseMemberViewSet.as_view({'delete': 'destroy'}), name='course_member_detail'),
]
