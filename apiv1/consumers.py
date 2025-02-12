import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, DirectMessage

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.conversation_id = self.scope['url_route']['kwargs']['roomId']

        if not await self.check_room_permission(self.conversation_id, self.user):
            await  self.close()
            return
        await self.channel_layer.group_add(self.conversation_id, self.channel_name)
        await self.accept()
        previous_messages = await self.get_previous_messages()
        for message in previous_messages[-21::]:
            await self.send(text_data=json.dumps({
                "id": message.id,
                'action': 'previousTexts',
                "message": message.message,
                "sentBy": message.sentBy,
                "createdAt": str(message.createdAt),
                "reply_message": message.reply_message,
                "reaction": message.reaction,
                "message_type": message.message_type,
                'status': message.status
            }))
        await self.send(text_data=json.dumps({
            "action": "previousLoaded",
        }))

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.conversation_id, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)


        if data['action'] == 'typingStatus':
            await self.channel_layer.group_send(
                self.conversation_id,
                {
                    "type": "chat_message",
                    "userId": self.user.id,
                    "action": data['action'],
                    "status": data['status'],
                }
            )
            return
        message = data['message']
        sentBy = data['sentBy']
        createdAt = data['createdAt']
        reply_message = data['reply_message']
        reaction = data['reaction']
        message_type = data['message_type']
        if data['action'] == 'setSeen':
            await self.set_read(data['id'])
            await self.channel_layer.group_send(
                self.conversation_id,
                {
                    "type": "chat_message",
                    "action": data['action'],
                    "id": data['id'],
                }
            )
        if data['action'] == 'updateReactions':
            await self.update_message(data)
            await self.channel_layer.group_send(
                self.conversation_id,
                {
                    "type": "chat_message",
                    "action": data['action'],
                    "id": data['id'],
                    "message": message,
                    "sentBy": sentBy,
                    "createdAt": createdAt,
                    "reply_message": reply_message,
                    "reaction": reaction,
                    "message_type": message_type,
                    'status': data['status']
                }
            )
        elif data['action'] == 'normalText':
            messageObject = await self.save_message(message, reaction, createdAt, reply_message, message_type)
            await self.channel_layer.group_send(
                self.conversation_id,
                {
                    "type": "chat_message",
                    "action": "normalText",
                    "id": messageObject.id,
                    "message": message,
                    "sentBy": sentBy,
                    "createdAt": createdAt,
                    "reply_message": reply_message,
                    "reaction": reaction,
                    "message_type": message_type,
                    'status': messageObject.status
                }
            )

    async def chat_message(self, event):

        if event['action'] == 'typingStatus':
            await self.send(text_data=json.dumps({
                "action": event["action"],
                "status": event["status"],
                "userId": event["userId"],
            }))

        elif event['action'] == 'setSeen':
            await self.send(text_data=json.dumps({
                "id": event["id"],
                "action": event["action"],
            }))

        else:
            await self.send(text_data=json.dumps({
                "id": event["id"],
                "action": event["action"],
                "message": event["message"],
                "sentBy": event["sentBy"],
                "createdAt": event["createdAt"],
                "reply_message": event["reply_message"],
                "reaction": event["reaction"],
                "message_type": event["message_type"],
                "status": event['status']
            }))

    @database_sync_to_async
    def check_room_permission(self, room_id, user):
        try:
            room = ChatRoom.objects.get(id=room_id)
            return user in [room.user1, room.user2]
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, message, reaction, createdAt, reply_message, message_type):
        room = ChatRoom.objects.get(id=self.conversation_id)
        messageObject = DirectMessage.objects.create(
            room=room,
            message=message,
            createdAt=createdAt,
            sentBy=self.user.id,
            reply_message=reply_message,
            reaction=reaction,
            message_type=message_type
        )
        return messageObject

    @database_sync_to_async
    def update_message(self, data):
        messageObject = DirectMessage.objects.filter(id=int(data['id'])).update(
            reaction=data['reaction'],
        )

        return messageObject

    @database_sync_to_async
    def set_read(self, id):
        return DirectMessage.objects.filter(id=int(id)).update(status='read')


    @database_sync_to_async
    def get_previous_messages(self):
        """Fetch previous messages from the database."""
        messages = DirectMessage.objects.filter(room=self.conversation_id).order_by('-createdAt')
        return list(reversed(messages))
