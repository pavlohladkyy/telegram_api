import requests
import json

class ChatAssistant:
    def __init__(self, api_key, site_url=None, site_name=None):
        self.api_key = api_key
        self.site_url = site_url
        self.site_name = site_name
        self.chat_memory = {}
        # Змінений промпт для аналізу обіцянок та відповідей
        self.system_prompt = (
            "Ти — аналітик переписок між менеджером і клієнтом. "
            "Твоя відповідь має бути чітко структурована за такими пунктами:\n"
            "1. Кількість повідомлень\n"
            "2. Тривалість розмови (дати/час)\n"
            "3. Обіцянки менеджера (для кожної: текст, чи виконано, підтвердження або причина невиконання)\n"
            "4. Ігноровані питання/прохання клієнта\n"
            "5. Негативні моменти (помилки, скарги, низька ініціативність)\n"
            "6. Статистика менеджера:\n"
            "   - Кількість відповідей\n"
            "   - Оцінка швидкості реакції\n"
            "   - Кількість пропущених повідомлень\n"
            "   - Кількість ініційованих діалогів менеджером\n"
            "7. Короткий висновок\n"
            "8. Рекомендації для покращення\n"
            "Якщо деяких даних немає у переписці, проаналізуй і вкажи це у відповідному пункті. "
            "Відповідай лише структуровано за цими пунктами, українською мовою, без додаткових пояснень чи форматування JSON."
        )

    def _get_messages(self, user_id, user_text):
        """
        Формування списку повідомлень для відправки до API
        Включає системний промпт, історію розмови та поточне повідомлення
        """
        memory = self.chat_memory.get(user_id, [])
        messages = [{"role": "system", "content": self.system_prompt}]
        messages += memory
        messages.append({"role": "user", "content": user_text})
        return messages

    def ask(self, user_text: str, user_id: str = "default_user") -> str:
        """
        Відправка запиту до Gemini API для аналізу повідомлень
        
        Args:
            user_text: Текст повідомлень для аналізу
            user_id: Унікальний ідентифікатор користувача
            
        Returns:
            str: Структурований аналіз у форматі пунктів
        """
        # Отримання всіх повідомлень включно з новим
        messages = self._get_messages(user_id, user_text)
        
        # Конвертація формату повідомлень для Gemini API
        gemini_messages = []
        for msg in messages:
            if msg["role"] == "system":
                # Системний промпт передається як повідомлення користувача
                gemini_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "user":
                # Повідомлення користувача
                gemini_messages.append({"role": "user", "parts": [{"text": msg["content"]}]})
            elif msg["role"] == "assistant":
                # Відповіді асистента конвертуються в модель
                gemini_messages.append({"role": "model", "parts": [{"text": msg["content"]}]})

        # Підготовка даних для API запиту
        data = {
            "contents": gemini_messages
        }

        # Налаштування заголовків запиту
        headers = {
            "Content-Type": "application/json",
        }
        # Додаткові заголовки якщо вказані
        if self.site_url:
            headers["Referer"] = self.site_url
        if self.site_name:
            headers["X-Title"] = self.site_name

        # URL для Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"

        try:
            # Відправка POST запиту до API
            response = requests.post(
                url=url,
                headers=headers,
                data=json.dumps(data)
            )
            # Перевірка успішності запиту
            response.raise_for_status()
            
            # Парсинг JSON відповіді
            result = response.json()
            
            # Витягування тексту відповіді з JSON структури
            reply = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # Збереження історії розмови в пам'яті
            self.chat_memory.setdefault(user_id, []).append({"role": "user", "content": user_text})
            self.chat_memory[user_id].append({"role": "assistant", "content": reply})
            
            return reply
            
        except Exception as e:
            # Обробка помилок та повернення стандартного повідомлення
            return "Виникла помилка спробуйте ще раз надіслати запитання."

    def analyze_chat_messages(self, messages_text: str, user_id: str = "analyst") -> str:
        """
        Спеціальний метод для аналізу повідомлень чату
        
        Args:
            messages_text: Текст всіх повідомлень для аналізу
            user_id: Ідентифікатор для аналітичної сесії
            
        Returns:
            str: Детальний аналіз у форматі пунктів 1, 2, 3...
        """
        # Формування запиту для аналізу
        analysis_request = f"Проаналізуй наступні повідомлення між менеджером та клієнтом:\n\n{messages_text}"
        
        # Відправка запиту на аналіз
        return self.ask(analysis_request, user_id)

    def clear_memory(self, user_id: str = None):
        """
        Очищення пам'яті розмов
        
        Args:
            user_id: Ідентифікатор користувача (якщо None - очищає всю пам'ять)
        """
        if user_id:
            # Очищення пам'яті конкретного користувача
            self.chat_memory.pop(user_id, None)
        else:
            # Очищення всієї пам'яті
            self.chat_memory.clear()

    def get_memory_status(self) -> dict:
        """
        Отримання статусу пам'яті розмов
        
        Returns:
            dict: Інформація про збережені розмови
        """
        return {
            "total_users": len(self.chat_memory),
            "users": list(self.chat_memory.keys()),
            "total_messages": sum(len(messages) for messages in self.chat_memory.values())
        }