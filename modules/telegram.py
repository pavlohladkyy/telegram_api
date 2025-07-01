# Імпорт необхідних бібліотек
from telethon import TelegramClient
from telethon.tl.types import User
from datetime import datetime, timedelta
import asyncio

class TelegramAnalyzer:
    """
    Клас для аналізу повідомлень у Telegram.
    """

    def __init__(self, api_id, api_hash, phone):
        self.client = TelegramClient('session', api_id, api_hash)
        self.phone = phone
        self.dialogs = []

    async def connect(self):
        await self.client.start(phone=self.phone)
        print("Підключено до Telegram")

    async def get_recent_chats(self, limit=10):
        self.dialogs = []
        async for dialog in self.client.iter_dialogs(limit=limit):
            if isinstance(dialog.entity, User):
                self.dialogs.append({
                    'id': dialog.entity.id,
                    'name': dialog.entity.first_name or dialog.entity.username,
                    'username': dialog.entity.username,
                    'dialog': dialog
                })
        return self.dialogs

    async def get_chat_history(self, chat_id, days_back=30):
        start_date = datetime.now() - timedelta(days=days_back)
        messages = []

        async for message in self.client.iter_messages(chat_id, offset_date=start_date, reverse=True):
            if message.text:
                messages.append({
                    'id': message.id,
                    'date': message.date,
                    'text': message.text,
                    'from_me': message.out,
                    'chat_id': chat_id
                })
        return messages

    async def print_chat_history(self):
        if not self.dialogs:
            print("Історія чатів порожня.")
            return

        print("Історія останніх чатів:")
        for chat in self.dialogs:
            print(f"Чат: {chat['name']} (ID: {chat['id']})")

    async def print_messages(self, messages):
        if not messages:
            print("Повідомлення відсутні.")
            return

        print("Повідомлення:")
        for message in messages:
            date = message['date'].strftime('%Y-%m-%d %H:%M:%S')
            sender = "Менеджер" if message['from_me'] else "Клієнт"
            print(f"{date} - {sender}: {message['text']}")

    def analyze_messages(self, messages):
        if not messages:
            return {
                'total_messages': 0,
                'manager_messages': 0,
                'client_messages': 0,
                'start_date': None,
                'end_date': None
            }

        total_messages = len(messages)
        manager_messages = sum(1 for msg in messages if msg['from_me'])
        client_messages = total_messages - manager_messages
        dates = [msg['date'] for msg in messages]
        start_date = min(dates)
        end_date = max(dates)

        return {
            'total_messages': total_messages,
            'manager_messages': manager_messages,
            'client_messages': client_messages,
            'start_date': start_date,
            'end_date': end_date
        }

    def print_messages_analysis(self, messages):
        analysis = self.analyze_messages(messages)

        print(f"\n📊 Аналіз розмови:")
        print(f"   Загальна кількість повідомлень: {analysis['total_messages']}")
        print(f"   Повідомлення менеджера: {analysis['manager_messages']}")
        print(f"   Повідомлення клієнта: {analysis['client_messages']}")

        if analysis['start_date'] and analysis['end_date']:
            start_formatted = analysis['start_date'].strftime('%Y-%m-%d')
            end_formatted = analysis['end_date'].strftime('%Y-%m-%d')
            print(f"   Період розмови: {start_formatted} - {end_formatted}")

        if analysis['total_messages'] > 0:
            manager_ratio = (analysis['manager_messages'] / analysis['total_messages']) * 100
            print(f"   Активність менеджера: {manager_ratio:.1f}%")

    async def disconnect(self):
        await self.client.disconnect()
        print("Від'єднано від Telegram")
