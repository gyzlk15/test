import telebot
from telebot import types
import time
import re

# Настройки бота
TOKEN = ''  # Замените на токен вашего бота
bot = telebot.TeleBot(TOKEN)

def escape_markdown(text):
    """Экранирует все специальные символы MarkdownV2"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


def safe_mention(user):
    """Создает безопасное упоминание пользователя"""
    name = escape_markdown(user.first_name)
    if user.last_name:
        name += ' ' + escape_markdown(user.last_name)

    if user.username:
        return f"@{user.username}"
    else:
        return f"[{name}](tg://user?id={user.id})"


@bot.message_handler(commands=['call'])
def call_all_members(message):
    if message.chat.type not in ['group', 'supergroup']:
        bot.reply_to(message, "Эта команда работает только в группах!")
        return

    try:
        chat_id = message.chat.id
        admins = bot.get_chat_administrators(chat_id)
        members = [admin.user for admin in admins if not admin.user.is_bot]

        if not members:
            bot.reply_to(message, "Не найдено участников для упоминания.")
            return

        mentions = []
        for member in members:
            try:
                mentions.append(safe_mention(member))
            except Exception as e:
                print(f"Ошибка создания упоминания для {member.id}: {e}")

        if not mentions:
            bot.reply_to(message, "Не удалось создать упоминания.")
            return

        # Отправляем несколькими сообщениями
        max_per_message = 5
        for i in range(0, len(mentions), max_per_message):
            batch = mentions[i:i + max_per_message]
            try:
                # Текст без Markdown, так как упоминания уже правильно оформлены
                mention_text = "📢 Внимание! " + " ".join(batch)
                bot.send_message(
                    chat_id,
                    mention_text,
                    parse_mode=None,  # Отключаем Markdown обработку
                    disable_notification=True
                )
                time.sleep(1)
            except Exception as e:
                print(f"Ошибка отправки: {e}")
                # Попробуем отправить без форматирования
                try:
                    plain_text = "📢 Внимание! " + " ".join(
                        f"@{m[1:]}" if m.startswith('@') else m.split(']')[0][1:]
                        for m in batch
                    )
                    bot.send_message(
                        chat_id,
                        plain_text,
                        disable_notification=True
                    )
                except Exception as e2:
                    print(f"Ошибка при отправке простого текста: {e2}")

    except Exception as e:
        print(f"Общая ошибка: {e}")
        bot.reply_to(message, "Произошла ошибка при выполнении команды")


@bot.message_handler(commands=['help', 'start'])
def send_help(message):
    help_text = """
🤖 Бот для вызова участников группы

Команды:
/call - Вызвать всех участников группы (только для админов)
/help - Показать это сообщение

Бота нужно сделать администратором!
"""
    bot.reply_to(message, help_text, parse_mode=None)


if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()