from django.db import models
from django.conf import settings
from places.models import Place

class TravelCourse(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_courses', help_text="생성자/소유자")
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=100)
    start_date = models.DateField()
    duration_days = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.destination})"


class CourseMember(models.Model):
    ROLE_CHOICES = [
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    ]

    course = models.ForeignKey(TravelCourse, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_participations')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='editor')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.course.title} ({self.role})"


class CourseDetail(models.Model):
    course = models.ForeignKey(TravelCourse, on_delete=models.CASCADE, related_name='slots')
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='course_slots')
    day_number = models.IntegerField(default=1, help_text="여행 일차 (1일차, 2일차 등)")
    sequence = models.IntegerField(help_text="하루 일정 내의 순서 (예: 1=오전, 2=점심, 3=오후, 4=저녁)")
    is_locked = models.BooleanField(default=False, help_text="슬롯 고정(Lock) 여부")

    class Meta:
        ordering = ['day_number', 'sequence']
        unique_together = ('course', 'day_number', 'sequence')

    def __str__(self):
        return f"{self.course.title} - Day {self.day_number} Seq {self.sequence}: {self.place.name} ({'Locked' if self.is_locked else 'Unlocked'})"
