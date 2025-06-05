# management/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from .models import ChatMessage
from django.db.models import Count # For count queries

CustomUser = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.other_username = self.scope['url_route']['kwargs']['other_username']

        if not self.user.is_authenticated:
            await self.close()
            return
        try:
            self.other_user = await sync_to_async(CustomUser.objects.get)(username=self.other_username)
        except CustomUser.DoesNotExist:
            await self.close()
            return
        if not await self.can_chat_with(self.user, self.other_user):
            await self.close()
            return

        user_ids = sorted([self.user.id, self.other_user.id])
        self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Mark messages as read when entering the chat room
        await self.mark_messages_as_read_in_conversation(sender=self.other_user, receiver=self.user)

        # Notify self.user about updated unread counts after marking messages from self.other_user as read
        new_total_unread_for_self_user = await sync_to_async(
            ChatMessage.objects.filter(receiver=self.user, is_read=False).count
        )()
        
        own_notification_group_name = f'notifications_user_{self.user.id}'
        count_update_payload_for_client = {
            'type': 'unread_count_update', # Client-side JS type
            'event_trigger': 'conversation_partner_messages_read',
            'chat_partner_username': self.other_user.username,
            'unread_from_partner_count': 0, # Count from this partner is now 0 for self.user
            'new_total_unread_count': new_total_unread_for_self_user # Updated total for self.user
        }
        await self.channel_layer.group_send(
            own_notification_group_name,
            {
                'type': 'send_notification', # Targets NotificationConsumer.send_notification
                'message_data': count_update_payload_for_client
            }
        )
        print(f"Sent unread count update to {self.user.username} after entering chat with {self.other_user.username}")
        print(f"DEBUG: WebSocket connected for User '{self.user.username}' to chat with '{self.other_username}' in room '{self.room_group_name}'")

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']

        if not message_content.strip():
            return

        chat_message_obj = await self.save_message(self.user, self.other_user, message_content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message_handler',
                'message_id': chat_message_obj.id,
                'message': message_content,
                'sender_username': self.user.username,
                'receiver_username': self.other_user.username
            }
        )

        # Send notification to the receiver's personal notification group
        receiver_notification_group_name = f'notifications_user_{self.other_user.id}'
        
        # Calculate new counts for the RECEIVER (self.other_user)
        # How many unread messages does self.other_user now have from self.user (sender)?
        unread_from_this_sender_for_receiver = await sync_to_async(
            ChatMessage.objects.filter(sender=self.user, receiver=self.other_user, is_read=False).count
        )()
        # Total unread for receiver (self.other_user)
        total_unread_for_receiver = await sync_to_async(
            ChatMessage.objects.filter(receiver=self.other_user, is_read=False).count
        )()

        notification_payload = {
            'type': 'new_message_notification', # Client-side JS type
            'sender_username': self.user.username,
            'message_preview': message_content[:50] + '...' if len(message_content) > 50 else message_content,
            'chat_with_url': f'/app/chat/with/{self.user.username}/', # Adjust URL as needed
            'unread_from_sender_count': unread_from_this_sender_for_receiver,
            'total_unread_count_for_receiver': total_unread_for_receiver
        }

        await self.channel_layer.group_send(
            receiver_notification_group_name,
            {
                'type': 'send_notification', # Targets NotificationConsumer.send_notification
                'message_data': notification_payload
            }
        )
        print(f"Sent new message notification to group {receiver_notification_group_name} for user {self.other_user.username} with counts.")

    async def chat_message_handler(self, event):
        message_id = event['message_id']
        message_content = event['message']
        sender_username = event['sender_username']

        if self.user.username != sender_username and self.other_user.username == sender_username:
            await self.mark_specific_message_as_read(message_id)
            # Note: If you want immediate count updates on other pages when a message is read
            # in an open chat, you'd need to send another 'unread_count_update' notification here.
            # For simplicity, this example relies on the 'conversation_partner_messages_read' event
            # when re-entering a chat or page refresh for counts to fully sync after an in-chat read.

        await self.send(text_data=json.dumps({
            'message': message_content,
            'sender_username': sender_username,
            'message_id': message_id
        }))

    @sync_to_async
    def save_message(self, sender, receiver, content):
        return ChatMessage.objects.create(
            sender=sender,
            receiver=receiver,
            content=content
        )

    @sync_to_async
    def mark_messages_as_read_in_conversation(self, sender, receiver):
        updated_count = ChatMessage.objects.filter(
            sender=sender,
            receiver=receiver,
            is_read=False
        ).update(is_read=True)
        if updated_count > 0:
            print(f"DEBUG: Marked {updated_count} messages from {sender.username} to {receiver.username} as read.")
        return updated_count


    @sync_to_async
    def mark_specific_message_as_read(self, message_id):
        try:
            message = ChatMessage.objects.get(id=message_id)
            if not message.is_read:
                message.is_read = True
                message.save(update_fields=['is_read'])
                print(f"DEBUG: Marked message ID {message_id} as read.")
        except ChatMessage.DoesNotExist:
            print(f"DEBUG: Error: Message ID {message_id} not found to mark as read.")

    @sync_to_async
    def can_chat_with(self, user1, user2):
        role1 = user1.role
        role2 = user2.role
        can_chat = False
        if role1 == 'Company_Head': can_chat = True
        elif role1 == 'Company_Employee': can_chat = role2 in ['Company_Head', 'Company_Employee']
        elif role1 == 'Government': can_chat = role2 in ['Company_Head', 'Public', 'Government'] # Added Gov-Gov
        elif role1 == 'Public': can_chat = role2 == 'Government'
        return can_chat


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
        else:
            self.user_notification_group_name = f'notifications_user_{self.user.id}'
            await self.channel_layer.group_add(
                self.user_notification_group_name,
                self.channel_name
            )
            await self.accept()
            print(f"User {self.user.username} connected to notifications group: {self.user_notification_group_name}")

    async def disconnect(self, close_code):
        if hasattr(self, 'user_notification_group_name') and self.user.is_authenticated :
            await self.channel_layer.group_discard(
                self.user_notification_group_name,
                self.channel_name
            )
            print(f"User {self.user.username} disconnected from notifications group: {self.user_notification_group_name}")

    # This method is called when ChatConsumer sends a message to the user's group
    # with type: 'send_notification'
    async def send_notification(self, event):
        message_data = event["message_data"] # This is the payload constructed by ChatConsumer
        # Send this payload (which includes its own 'type' for client JS) to the WebSocket client
        await self.send(text_data=json.dumps(message_data))
        print(f"Sent notification ({message_data.get('type')}) to user {self.user.username}: {message_data}")