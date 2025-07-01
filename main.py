import asyncio
from modules.ai_asistant import ChatAssistant
from private.setting import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE, API_KEY
from modules.telegram import TelegramAnalyzer

from datetime import datetime

def print_ai_analysis(ai_result):
    """
    Виведення результатів AI аналізу у консоль
    """
    if ai_result:
        print(f"\n🤖 AI Аналіз:")
        print(ai_result)
    else:
        print("\n❌ AI аналіз недоступний.")

def format_messages_for_ai(messages):
    """
    Форматування повідомлень для AI аналізу
    
    Args:
        messages: Список повідомлень з чату
        
    Returns:
        str: Відформатований текст для аналізу
    """
    if not messages:
        return "Немає повідомлень для аналізу."
    
    formatted_text = []
    for msg in messages:
        date = msg['date'].strftime('%Y-%m-%d %H:%M:%S')
        sender = "Менеджер" if msg['from_me'] else "Клієнт"
        formatted_text.append(f"{date} - {sender}: {msg['text']}")
    
    return "\n".join(formatted_text)

async def main():
    # Ініціалізація компонентів
    telegram = TelegramAnalyzer(TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE)
    ai_analyzer = ChatAssistant(API_KEY)  
    
    try:
        # Підключення до Telegram
        await telegram.connect()
        
        # Отримання останніх чатів
        # Отримуємо всі чати та фільтруємо за назвою
        all_chats = await telegram.get_recent_chats()
        recent_chats = [chat for chat in all_chats]
        
        if not recent_chats:
            print("Немає доступних чатів для аналізу.")
            return
        
        # Аналіз кожного чату
        for chat in recent_chats:
            print(f"\n--- Аналіз чату: {chat['name']} (ID: {chat['id']}) ---")
            
            # Отримання історії повідомлень за останній день
            messages = await telegram.get_chat_history(chat['id'], days_back=1)
            
            if not messages:
                print("Немає повідомлень для аналізу.")
                continue

            # Виведення повідомлень (використовуємо метод з модуля telegram)
            await telegram.print_messages(messages)
            
            # Виведення статистики повідомлень (використовуємо метод з модуля telegram)
            telegram.print_messages_analysis(messages)
            
            # Форматування повідомлень для AI
            messages_text = format_messages_for_ai(messages)
            
            # AI аналіз розмови (використовуємо спеціальний метод для аналізу чатів)
            try:
                print("\n🔄 Виконується AI аналіз...")
                ai_result = ai_analyzer.analyze_chat_messages(
                    messages_text, 
                    user_id=f"chat_{chat['id']}"
                )
                
                if not ai_result or ai_result.strip() == "":
                    print("AI аналіз не повернув результат.")
                    ai_result = None
                    
            except Exception as e:
                print(f"Помилка AI аналізу: {e}")
                ai_result = None

            # Виведення результатів AI аналізу
            print_ai_analysis(ai_result)

            # Очищення пам'яті AI для наступного чату
            ai_analyzer.clear_memory(f"chat_{chat['id']}")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"Критична помилка: {e}")
        
    finally:
        # Коректне від'єднання від Telegram
        try:
            await telegram.disconnect()
        except Exception as e:
            print(f"Помилка при від'єднанні: {e}")

if __name__ == "__main__":
    asyncio.run(main())