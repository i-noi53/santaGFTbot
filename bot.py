import asyncio
import re
import os

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv


# ─────────────────────────────────────────────
# Конфигурация
# ─────────────────────────────────────────────

load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN not found in environment variables")

admin_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = set(map(int, admin_raw.split(","))) if admin_raw.strip() else set()


# ─────────────────────────────────────────────
# Регулярка для извлечения слов
# ─────────────────────────────────────────────
# Используем её чтобы достать слова из текста.

WORD_PATTERN = re.compile(r"\b[а-яёa-z]+\b", re.IGNORECASE)


# ─────────────────────────────────────────────
# Состояние игры
# ─────────────────────────────────────────────

class GameState:

    def __init__(self):

        # игра включена / выключена
        self.active = False

        # ждём ввод слов от админа
        self.waiting_admin_input = False

        # ключевые слова
        self.key_words = set()

        # user_id → найденные слова
        self.progress = {}

        # user_id → слова по которым уже давали подсказку
        self.notified = {}

    def reset(self):

        self.progress.clear()
        self.notified.clear()


game = GameState()


# ─────────────────────────────────────────────
# Telegram
# ─────────────────────────────────────────────

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ─────────────────────────────────────────────
# Утилиты
# ─────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def extract_words(text: str):
    """
    Извлекаем слова из сообщения.

    Используем regex чтобы:
    - убрать пунктуацию
    - получить слова строго целиком
    """

    return [w.lower() for w in WORD_PATTERN.findall(text)]


def mention_user(message: Message):

    if message.from_user.username:
        return f"@{message.from_user.username}"

    return message.from_user.full_name


# ─────────────────────────────────────────────
# Команды админа
# ─────────────────────────────────────────────

@dp.message(Command("start_game", "restart_game"))
async def cmd_start(message: Message):

    if not is_admin(message.from_user.id):
        return

    game.active = True
    game.reset()

    await message.reply(
        "Игра запущена / перезапущена.\n"
        "Три слова спрятаны."
    )


@dp.message(Command("stop_game"))
async def cmd_stop(message: Message):

    if not is_admin(message.from_user.id):
        return

    game.active = False

    await message.reply("Игра остановлена.")


@dp.message(Command("add_game"))
async def cmd_add_game(message: Message):

    if not is_admin(message.from_user.id):
        return

    game.waiting_admin_input = True

    await message.reply(
        "Отправь 3 слова через пробел.\n\n"
        "Например:\n"
        "гибель рисового душ"
    )


# ─────────────────────────────────────────────
# Основной обработчик
# ─────────────────────────────────────────────

@dp.message()
async def game_handler(message: Message):

    if not message.text:
        return

    text = message.text.strip()

    # команды дальше не обрабатываем
    if text.startswith("/"):
        return

    words = extract_words(text)

    if not words:
        return

    uid = str(message.from_user.id)

    # ─────────────────────────
    # Ввод слов админом
    # ─────────────────────────

    if game.waiting_admin_input and is_admin(message.from_user.id):

        if len(words) != 3:
            await message.reply("Нужно отправить ровно 3 слова")
            return

        game.key_words = set(words)

        game.reset()
        game.waiting_admin_input = False

        await message.reply(
            "🎮 Новая игра началась!\n\n"
            "В чате спрятаны 3 слова.\n"
            "Попробуйте их найти 😉"
        )

        return

    # ─────────────────────────
    # Игра выключена
    # ─────────────────────────

    if not game.active:
        return

    # ─────────────────────────
    # Проверка победы
    # ─────────────────────────

    if set(words) == game.key_words:

        game.active = False

        await message.reply(
            f"🏆 ПОБЕДИТЕЛЬ!\n"
            f"{mention_user(message)} собрал все ключевые слова!\n\n"
            f"Слова: {' · '.join(game.key_words)}"
        )

        return

    # ─────────────────────────
    # Режим подсказки (>3 слов)
    # ─────────────────────────

    if len(words) > 3:

        found = set(words) & game.key_words

        if found:

            if uid not in game.notified:
                game.notified[uid] = set()

            new_words = found - game.notified[uid]

            if new_words:

                game.notified[uid].update(new_words)

                await message.reply(
                    "Тут есть правильные слова"
                )

        return

    # ─────────────────────────
    # Попытка угадать (≤3 слов)
    # ─────────────────────────

    correct = [w for w in words if w in game.key_words]

    if not correct:
        return

    # часть слов правильная
    if len(correct) != len(words):

        await message.reply(
            "Тут есть правильное слово 😉"
        )

        return

    # ─────────────────────────
    # Засчитываем слова
    # ─────────────────────────

    if uid not in game.progress:
        game.progress[uid] = set()

    new_words = set(correct) - game.progress[uid]

    if not new_words:
        return

    game.progress[uid].update(new_words)

    count = len(game.progress[uid])

    if count == 3:

        game.active = False

        await message.reply(
            f"🏆 ПОБЕДИТЕЛЬ!\n"
            f"{mention_user(message)} собрал все части ключа!\n\n"
            f"Слова: {' · '.join(game.key_words)}"
        )

    else:

        await message.reply(
            f"✅ Часть ключа засчитана ({count}/3)"
        )


# ─────────────────────────────────────────────
# Запуск
# ─────────────────────────────────────────────

async def main():

    print("Бот запущен...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
