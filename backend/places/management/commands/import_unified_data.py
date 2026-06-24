import json
import os
import uuid
from django.core.management.base import BaseCommand
from places.models import Place
from recommendations.models import FixedPlace, TemporaryEvent
from django.db import transaction

class Command(BaseCommand):
    help = 'Import unified_dataset.json into the database'

    def handle(self, *args, **options):
        file_path = os.path.join(os.path.dirname(__file__), '../../../../data/unified_dataset.json')
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.stdout.write(f"Total items in JSON: {len(data)}")

        fixed_places_to_create = []
        events_to_create = []

        # Delete existing to prevent duplication if re-run (optional)
        # We will use update_or_create or ignore conflicts

        for item in data:
            source = item.get('source')
            cat_raw = item.get('category', '')
            
            # Extract region (first two chars of address usually works for Korea)
            addr = item.get('address') or ''
            region = addr[:2] if len(addr) >= 2 else '기타'

            if source == 'tour_api_festival':
                start_date = item.get('start_date')
                end_date = item.get('end_date')
                
                # If start_date/end_date is missing or invalid, fallback to some default or skip
                if not start_date or not end_date:
                    continue

                events_to_create.append(
                    TemporaryEvent(
                        name=item.get('title')[:200],
                        address=addr[:300],
                        region=region,
                        category=cat_raw[:100],
                        start_date=start_date,
                        end_date=end_date,
                        latitude=float(item.get('location', {}).get('lat', 0.0) or 0.0),
                        longitude=float(item.get('location', {}).get('lng', 0.0) or 0.0),
                        image_url=(item.get('image_url') or '')[:1000],
                        link=(item.get('url') or '')[:1000]
                    )
                )
            else:
                # Map detailed category to basic category expected by KAKAO_TO_JW_CATEGORY
                mapped_cat = '관광명소'
                if '카페' in cat_raw:
                    mapped_cat = '카페'
                elif '펜션' in cat_raw:
                    mapped_cat = '펜션'
                elif '호텔' in cat_raw:
                    mapped_cat = '호텔'
                elif '숙박' in cat_raw:
                    mapped_cat = '숙소'
                elif '음식점' in cat_raw or '식당' in cat_raw:
                    mapped_cat = '음식점'
                elif '공방' in cat_raw:
                    mapped_cat = '공방'
                elif '레포츠' in cat_raw or '스포츠' in cat_raw:
                    mapped_cat = '액티비티'

                # Some fallbacks might not have a proper ID, generate one if needed
                place_id = item.get('id')
                if not place_id or str(place_id).startswith('generated_'):
                    place_id = f"gen_{uuid.uuid4().hex[:10]}"

                fixed_places_to_create.append(
                    FixedPlace(
                        id=str(place_id)[:100],
                        name=item.get('title')[:200],
                        address=addr[:300],
                        region=region,
                        category=mapped_cat,
                        latitude=float(item.get('location', {}).get('lat', 0.0) or 0.0),
                        longitude=float(item.get('location', {}).get('lng', 0.0) or 0.0),
                        image_url=(item.get('image_url') or '')[:1000],
                        place_url=(item.get('url') or '')[:1000]
                    )
                )

        self.stdout.write("Inserting TemporaryEvents...")
        TemporaryEvent.objects.bulk_create(events_to_create, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f"Inserted {len(events_to_create)} TemporaryEvents."))

        self.stdout.write("Inserting FixedPlaces... (This might take a while)")
        # Batch insert to avoid memory issues
        batch_size = 5000
        for i in range(0, len(fixed_places_to_create), batch_size):
            batch = fixed_places_to_create[i:i+batch_size]
            FixedPlace.objects.bulk_create(batch, ignore_conflicts=True)
            self.stdout.write(f"Inserted {i + len(batch)} / {len(fixed_places_to_create)} FixedPlaces")

        self.stdout.write(self.style.SUCCESS('Successfully imported all data.'))
