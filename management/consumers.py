# management/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from .models import ChatMessage # Import ChatMessage

CustomUser = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.other_username = self.scope['url_route']['kwargs']['other_username']

        # ... (existing connection logic: authentication, other_user retrieval, can_chat_with) ...
        # Ensure self.user and self.other_user are correctly set before this point

        if not self.user.is_authenticated: # Basic check, should be more robust earlier
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
        # ... end of existing connection logic checks


        user_ids = sorted([self.user.id, self.other_user.id])
        self.room_group_name = f'chat_{user_ids[0]}_{user_ids[1]}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Mark messages as read when entering the chat room
        # These are messages sent BY other_user TO self.user
        await self.mark_messages_as_read_in_conversation(sender=self.other_user, receiver=self.user)

        print(f"DEBUG: WebSocket connected for User '{self.user.username}' to chat with '{self.other_username}' in room '{self.room_group_name}'")


    async def disconnect(self, close_code):
        # ... (existing disconnect logic) ...
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

        # Sender is self.user, Receiver is self.other_user
        chat_message_obj = await self.save_message(self.user, self.other_user, message_content)

        # Send message to the chat room group
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

        # --- BEGIN NEW: Send notification to the receiver's personal notification group ---
        receiver_notification_group_name = f'notifications_user_{self.other_user.id}'
        notification_payload = {
            'type': 'new_message', # Can be used by client to identify notification type
            'sender_username': self.user.username,
            'message_preview': message_content[:50] + '...' if len(message_content) > 50 else message_content,
            'chat_with_url': f'/app/chat/with/{self.user.username}/' # URL to open the chat
            # You can add more data like sender's avatar, etc.
        }

        await self.channel_layer.group_send(
            receiver_notification_group_name,
            {
                'type': 'send_notification', # This matches the method name in NotificationConsumer
                'message_data': notification_payload
            }
        )
        print(f"Sent new message notification to group {receiver_notification_group_name} for user {self.other_user.username}")
        # --- END NEW ---

    # Renamed from chat_message to avoid confusion with a type name
    async def chat_message_handler(self, event):
        message_id = event['message_id']
        message_content = event['message']
        sender_username = event['sender_username']
        # receiver_username = event['receiver_username'] # Could be used if needed

        # If the current user of THIS consumer instance is the INTENDED RECIPIENT
        # of the message, and the message came from the other_user they are chatting with,
        # mark it as read.
        if self.user.username != sender_username and self.other_user.username == sender_username:
            # This means self.user is the receiver of this message
            # And self.other_user (who this chat is with) is the sender
            await self.mark_specific_message_as_read(message_id)

        # Send message to WebSocket client
        await self.send(text_data=json.dumps({
            'message': message_content,
            'sender_username': sender_username,
            'message_id': message_id # Send message_id to client
        }))

    # --- Helper methods for database operations ---
    @sync_to_async
    def save_message(self, sender, receiver, content):
        return ChatMessage.objects.create(
            sender=sender,
            receiver=receiver,
            content=content
            # is_read defaults to False
        )

    @sync_to_async
    def mark_messages_as_read_in_conversation(self, sender, receiver):
        # Marks all unread messages from 'sender' to 'receiver' as read
        updated_count = ChatMessage.objects.filter(
            sender=sender,
            receiver=receiver,
            is_read=False
        ).update(is_read=True)
        if updated_count > 0:
            print(f"DEBUG: Marked {updated_count} messages from {sender.username} to {receiver.username} as read.")


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
        # ... (your existing can_chat_with logic) ...
        role1 = user1.role
        role2 = user2.role
        can_chat = False
        if role1 == 'Company_Head': can_chat = True
        elif role1 == 'Company_Employee': can_chat = role2 in ['Company_Head', 'Company_Employee']
        elif role1 == 'Government': can_chat = role2 in ['Company_Head', 'Public']
        elif role1 == 'Public': can_chat = role2 == 'Government'
        return can_chat
    
    
    
    


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
        else:
            # Each user joins a group named after their user ID for personal notifications
            self.user_notification_group_name = f'notifications_user_{self.user.id}'
            await self.channel_layer.group_add(
                self.user_notification_group_name,
                self.channel_name
            )
            await self.accept()
            print(f"User {self.user.username} connected to notifications group: {self.user_notification_group_name}")

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.user_notification_group_name,
                self.channel_name
            )
            print(f"User {self.user.username} disconnected from notifications group: {self.user_notification_group_name}")

    # This method is called when we send a message to the user's group
    async def send_notification(self, event):
        message_data = event["message_data"]
        # Send message to WebSocket
        await self.send(text_data=json.dumps(message_data))
        print(f"Sent notification to user {self.user.username}: {message_data}")