from django.contrib import admin
from recommendations.models import AICache, Tag, FixedPlace, TemporaryEvent

admin.site.register(AICache)
admin.site.register(Tag)
admin.site.register(FixedPlace)
admin.site.register(TemporaryEvent)
