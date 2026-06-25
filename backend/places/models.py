from django.db import models

class Place(models.Model):
    CATEGORY_CHOICES = [
        ('restaurant', 'Restaurant'),
        ('cafe', 'Cafe'),
        ('spot', 'Tourist Spot'),
        ('activity', 'Activity'),
        ('accommodation', 'Accommodation'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    themes = models.CharField(max_length=255, blank=True, help_text="쉼표로 구분된 테마 목록 (예: nature, healing, food)")
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    address = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    image_url = models.CharField(max_length=1000, blank=True, default="")
    # AI 추천 연동 필드 (카카오 API로 수집된 장소에 사용)
    place_url = models.URLField(max_length=1000, blank=True, default="", help_text="카카오맵 장소 URL")
    region = models.CharField(max_length=100, blank=True, default="", db_index=True, help_text="지역명 (예: 홍대, 강남)")

    def __str__(self):
        return f"[{self.get_category_display()}] {self.name}"
