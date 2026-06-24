from django.db import models
from django.conf import settings

class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preference')
    preferred_themes = models.CharField(max_length=255, blank=True, help_text="쉼표로 구분된 선호 테마 목록 (예: healing, activity)")
    preferred_pace = models.CharField(max_length=20, default='medium', choices=[
        ('slow', 'Slow'),
        ('medium', 'Medium'),
        ('fast', 'Fast')
    ])

    def __str__(self):
        return f"{self.user.username}'s preference"


class UserVetoCategory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='veto_categories')
    category_code = models.CharField(max_length=50, help_text="기피하는 카테고리 코드 (예: museum, shopping)")

    class Meta:
        unique_together = ('user', 'category_code')

    def __str__(self):
        return f"{self.user.username} avoids {self.category_code}"
