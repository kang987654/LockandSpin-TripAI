from django.db import models

class AICache(models.Model):
    query_key = models.CharField(max_length=500, unique=True, db_index=True)
    parsed_result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.query_key

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)

    def __str__(self):
        return self.name

class FixedPlace(models.Model):
    id = models.CharField(max_length=100, primary_key=True) # 카카오 장소 ID
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    region = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=100, db_index=True)
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    place_url = models.URLField(max_length=1000)
    tags = models.ManyToManyField(Tag, related_name="places", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.region}] {self.name}"

class TemporaryEvent(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True, null=True)
    region = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=100, db_index=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    link = models.URLField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.region}] {self.name}"
