# video/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Room, Attendance, Note
from django.utils import timezone

class VideoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'video_{self.room_name}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'user_join', 'message': {'type': 'join_room', 'username': self.user.username}}
        )

        if not self.user.profile.is_lecturer:
            await self.record_attendance_join()

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'user_leave', 'message': {'type': 'leave_room', 'username': self.user.username}}
        )

        if self.user.is_authenticated and not self.user.profile.is_lecturer:
            await self.record_attendance_leave()

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'present_note':
            note_id = data.get('note_id')
            note_content = await self.get_note_content_if_host(note_id)
            if note_content is not None:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'note_update',
                        'message': {
                            'type': 'note_update',
                            'content': note_content,
                        }
                    }
                )
        else:
            # Handle WebRTC signaling
            data['username'] = self.user.username
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'webrtc_message', 'message': data}
            )

    # Group message handlers
    async def webrtc_message(self, event):
        message = event['message']
        if self.user.username != message.get('username'):
            await self.send(text_data=json.dumps(message))

    async def user_join(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def note_update(self, event):
        await self.send(text_data=json.dumps(event['message']))

    # Database methods
    @sync_to_async
    def get_note_content_if_host(self, note_id):
        try:
            note = Note.objects.select_related('room__host').get(id=note_id)
            if note.room.host == self.user:
                return note.content
        except Note.DoesNotExist:
            return None
        return None

    @sync_to_async
    def record_attendance_join(self):
        room, _ = Room.objects.get_or_create(name=self.room_name)
        Attendance.objects.update_or_create(
            room=room, student=self.user, leave_time=None,
            defaults={'join_time': timezone.now()}
        )

    @sync_to_async
    def record_attendance_leave(self):
        try:
            attendance = Attendance.objects.filter(
                room__name=self.room_name, student=self.user, leave_time=None
            ).latest('join_time')
            attendance.leave_time = timezone.now()
            attendance.save()
        except Attendance.DoesNotExist:
            pass
