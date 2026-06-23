import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from courses.models import CourseDetail

class CourseConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.course_id = self.scope['url_route']['kwargs']['course_id']
        self.room_group_name = f'course_{self.course_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        event = data.get('event')
        event_data = data.get('data', {})

        if event == 'toggle_lock':
            day_number = event_data.get('day_number')
            sequence = event_data.get('sequence')
            is_locked = event_data.get('is_locked')

            # Update database record asynchronously
            await self.update_slot_lock(day_number, sequence, is_locked)

            # Broadcast toggle to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'course_update_message',
                    'event': 'toggle_lock',
                    'data': {
                        'day_number': day_number,
                        'sequence': sequence,
                        'is_locked': is_locked
                    }
                }
            )

    @database_sync_to_async
    def update_slot_lock(self, day, seq, is_locked):
        detail = CourseDetail.objects.filter(
            course_id=self.course_id,
            day_number=day,
            sequence=seq
        ).first()
        if detail:
            detail.is_locked = is_locked
            detail.save()

    # Receive message from room group
    async def course_update_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'event': event['event'],
            'data': event['data']
        }))
