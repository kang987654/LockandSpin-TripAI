from django.db import models

class Place(models.Model):
    CATEGORY_CHOICES = [
        ('restaurant', 'Restaurant'),
        ('cafe', 'Cafe'),
        ('spot', 'Tourist Spot'),
        ('activity', 'Activity'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    themes = models.CharField(max_length=255, blank=True, help_text="쉼표로 구분된 테마 목록 (예: nature, healing, food)")
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    image_url = models.CharField(max_length=1000, blank=True, default="")

    def __str__(self):
        return f"[{self.get_category_display()}] {self.name}"
