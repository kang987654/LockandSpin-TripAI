import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from recommendations.models import FixedPlace

class Command(BaseCommand):
    help = '현재 수집된 추천(AI 추천) 관련 데이터베이스를 fixture 파일로 덤프합니다.'

    def handle(self, *args, **options):
        # fixtures 디렉토리 생성
        fixture_dir = 'recommendations/fixtures'
        if not os.path.exists(fixture_dir):
            os.makedirs(fixture_dir)
            self.stdout.write(self.style.SUCCESS(f"Created directory: {fixture_dir}"))

        output_file = os.path.join(fixture_dir, 'ai_recommendation_data.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            call_command('dumpdata', 'recommendations', format='json', indent=4, stdout=f)

        count = FixedPlace.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Successfully dumped data into {output_file}"))
        self.stdout.write(self.style.SUCCESS(f"Total FixedPlaces saved: {count}"))
