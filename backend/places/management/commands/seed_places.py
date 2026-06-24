from django.core.management.base import BaseCommand
from places.models import Place

class Command(BaseCommand):
    help = 'Seeds initial sample place data for Gangneung'

    def handle(self, *args, **options):
        # Sample data for Gangneung
        samples = [
            # spots
            {
                "name": "경포해변",
                "category": "spot",
                "themes": "nature,healing,sea",
                "latitude": 37.7981,
                "longitude": 128.9161,
                "address": "강원특별자치도 강릉시 안현동 산1",
                "description": "강릉을 대표하는 맑고 넓은 동해안의 모래사장과 송림이 우거진 해변입니다."
            },
            {
                "name": "오죽헌",
                "category": "spot",
                "themes": "history,culture,healing",
                "latitude": 37.7792,
                "longitude": 128.8795,
                "address": "강원특별자치도 강릉시 율곡로3139번길 24",
                "description": "신사임당과 율곡 이이가 태어난 역사적 가치가 높은 조선 시대의 목조 건물입니다."
            },
            {
                "name": "정동진역",
                "category": "spot",
                "themes": "nature,sea,view",
                "latitude": 37.6916,
                "longitude": 129.0348,
                "address": "강원특별자치도 강릉시 강동면 정동역길 17",
                "description": "세계에서 바다와 가장 가까운 역으로, 해돋이 명소로 매우 유명합니다."
            },
            # restaurants
            {
                "name": "초당토부두부",
                "category": "restaurant",
                "themes": "food,traditional",
                "latitude": 37.7905,
                "longitude": 128.9145,
                "address": "강원특별자치도 강릉시 초당순두부길 77",
                "description": "맑은 바닷물로 간을 맞춘 고소하고 부드러운 초당 순두부 전문점입니다."
            },
            {
                "name": "강릉짬뽕갈비",
                "category": "restaurant",
                "themes": "food,spicy",
                "latitude": 37.7912,
                "longitude": 128.9150,
                "address": "강원특별자치도 강릉시 초당순두부길 116",
                "description": "얼큰한 짬뽕 국물에 부드러운 갈비와 순두부가 조화를 이룬 이색 맛집입니다."
            },
            {
                "name": "엄지네포장마차",
                "category": "restaurant",
                "themes": "food,seafood",
                "latitude": 37.7612,
                "longitude": 128.9079,
                "address": "강원특별자치도 강릉시 남구길30번길 22",
                "description": "꼬막무침과 꼬막비빔밥으로 전국적인 명성을 얻은 강릉의 대표 실내 포차입니다."
            },
            # cafes
            {
                "name": "보헤미안 박이추 커피",
                "category": "cafe",
                "themes": "coffee,healing,view",
                "latitude": 37.8415,
                "longitude": 128.8710,
                "address": "강원특별자치도 강릉시 사천면 해안로 1107",
                "description": "대한민국 1세대 바리스타 박이추 명장의 깊은 핸드드립 커피를 맛볼 수 있는 곳입니다."
            },
            {
                "name": "안목해변 커피거리 카페",
                "category": "cafe",
                "themes": "coffee,healing,sea",
                "latitude": 37.7718,
                "longitude": 128.9488,
                "address": "강원특별자치도 강릉시 창해로 14",
                "description": "바다를 바라보며 다양한 로스팅 커피를 즐길 수 있는 안목 해안의 명물 거리입니다."
            },
            # activities
            {
                "name": "정동진 레일바이크",
                "category": "activity",
                "themes": "activity,sea,fun",
                "latitude": 37.6908,
                "longitude": 129.0335,
                "address": "강원특별자치도 강릉시 강동면 정동역길 17",
                "description": "정동진역에서 출발해 드넓은 동해바다 바람을 맞으며 선로 위를 달리는 레일바이크 체험입니다."
            },
            {
                "name": "하슬라아트월드",
                "category": "activity",
                "themes": "culture,art,view",
                "latitude": 37.7082,
                "longitude": 129.0118,
                "address": "강원특별자치도 강릉시 강동면 율곡로 1441",
                "description": "자연과 예술품, 그리고 조각 공원이 바다 전망과 조화를 이루는 종합 복합 예술 공간입니다."
            }
        ]

        created_count = 0
        for item in samples:
            place, created = Place.objects.get_or_create(
                name=item["name"],
                defaults={
                    "category": item["category"],
                    "themes": item["themes"],
                    "latitude": item["latitude"],
                    "longitude": item["longitude"],
                    "address": item["address"],
                    "description": item["description"]
                }
            )
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_count} new places in Gangneung!"))
