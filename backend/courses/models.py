from django.db import models
from django.conf import settings
from places.models import Place

class TravelCourse(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_courses', null=True, blank=True, help_text="생성자/소유자")
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=100)
    start_date = models.DateField()
    duration_days = models.IntegerField(default=1)
    departure_time = models.TimeField(null=True, blank=True, help_text="여행 출발 시간 (예: 14:00)")
    transportation = models.CharField(max_length=20, default='public', choices=[('car', '자차'), ('public', '대중교통')], help_text="이동 수단")
    preferences = models.TextField(blank=True, default='', help_text="자연어 여행 선호도 (AI 추천에 활용)")
    status = models.CharField(max_length=20, default='draft', choices=[('draft', '임시저장'), ('saved', '저장됨')], help_text="코스 저장 상태")
    ai_comment = models.TextField(blank=True, default='', help_text="AI가 분석한 코스 한줄평")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.destination})"


class CourseMember(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
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
    slot_name = models.CharField(max_length=50, blank=True, help_text="AI가 지정한 슬롯 이름 (예: 만화카페)")
    is_locked = models.BooleanField(default=False, help_text="슬롯 고정(Lock) 여부")
    reason = models.TextField(blank=True, default='', help_text="AI 추천 이유")
    alternative_option = models.TextField(blank=True, default='', help_text="대체 가능 옵션")

    class Meta:
        ordering = ['day_number', 'sequence']
        unique_together = ('course', 'day_number', 'sequence')

    def __str__(self):
        return f"{self.course.title} - Day {self.day_number} Seq {self.sequence}: {self.place.name} ({'Locked' if self.is_locked else 'Unlocked'})"


class CoursePlaceKeep(models.Model):
    course = models.ForeignKey(TravelCourse, on_delete=models.CASCADE, related_name='kept_places')
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('course', 'place')

    def __str__(self):
        return f"Kept: {self.place.name} in {self.course.title}"


class CoursePlaceExclude(models.Model):
    course = models.ForeignKey(TravelCourse, on_delete=models.CASCADE, related_name='excluded_places')
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('course', 'place')

    def __str__(self):
        return f"Excluded: {self.place.name} in {self.course.title}"
