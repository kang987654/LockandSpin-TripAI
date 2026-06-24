from django.db import models


class AICache(models.Model):
    """Gemini API 응답 캐시 — 동일 쿼리 중복 호출 방지"""
    query_key = models.CharField(max_length=500, unique=True, db_index=True)
    parsed_result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.query_key


class Tag(models.Model):
    """분위기/특성 키워드 태그 (예: 조용한, 가성비, 데이트)"""
    name = models.CharField(max_length=50, unique=True, db_index=True)

    def __str__(self):
        return self.name


class FixedPlace(models.Model):
    """카카오 로컬 API로 수집한 고정 장소 캐시 (AI 추천용)"""
    id = models.CharField(max_length=100, primary_key=True)  # 카카오 장소 ID
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    region = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=100, db_index=True)
    latitude = models.FloatField(default=0.0)   # 카카오 API y 좌표
    longitude = models.FloatField(default=0.0)  # 카카오 API x 좌표
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    place_url = models.URLField(max_length=1000)
    tags = models.ManyToManyField(Tag, related_name='fixed_places', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.region}] {self.name}"


class TemporaryEvent(models.Model):
    """네이버 검색 API로 수집한 일시적 행사 (팝업, 전시, 공연 등)"""
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True, null=True)
    region = models.CharField(max_length=100, db_index=True)
    category = models.CharField(max_length=100, db_index=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    image_url = models.URLField(max_length=1000, blank=True, null=True)
    link = models.URLField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.region}] {self.name} ({self.start_date}~{self.end_date})"
