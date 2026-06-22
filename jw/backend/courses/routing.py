from django.urls import re_path
from courses import consumers

websocket_urlpatterns = [
    re_path(r'ws/courses/(?P<course_id>\d+)/$', consumers.CourseConsumer.as_asgi()),
]
