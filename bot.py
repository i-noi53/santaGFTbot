import asyncio
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import os
from dotenv import load_dotenv

TOKEN = os.getenv("TOKEN")
# Кто может управлять игрой
ADMIN_IDS = set(
    map(int, os.getenv("ADMIN_IDS", "").split(","))
)

KEY_WORDS = { }

game_active = True
waiting_admin_word_input = False

# user_id → set найденных частей (только те, что отправлены ОТДЕЛЬНЫМ сообщением)
progress = {}           # str → set[str]

# user_id → bool (уже получил подсказку "Ты очень близок...")
notified = {}        # просто множество id пользователей

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ─── Команды админа ────────────────────────────────────────

@dp.message(Command("start_game", "restart_game"))
async def cmd_start(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    global game_active
    game_active = True
    progress.clear()
    notified.clear()
    await message.reply("Игра запущена / перезапущена. Три слова спрятаны.")


@dp.message(Command("stop_game"))
async def cmd_stop(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    global game_active
    game_active = False
    await message.reply("Игра остановлена.")

@dp.message(Command("add_game"))
async def add_game(message: Message):
    global waiting_admin_word_input

    if message.from_user.id not in ADMIN_IDS:
        return

    waiting_admin_word_input = True
    await message.reply(
        "Отправь 3 слова через пробел.\n"
        "Например:\n"
        "гибель рисового душ"
    )

# ─── Основная логика ───────────────────────────────────────

@dp.message()
async def game_handler(message: Message):
    global waiting_admin_word_input, KEY_WORDS
    if waiting_admin_word_input and message.from_user.id in ADMIN_IDS:

        words = message.text.lower().split()

        if len(words) != 3:
            await message.reply("Нужно отправить ровно 3 слова")
            return

        KEY_WORDS.clear()

        KEY_WORDS[words[0]] = "PART1"
        KEY_WORDS[words[1]] = "PART2"
        KEY_WORDS[words[2]] = "PART3"

        progress.clear()
        notified.clear()

        waiting_admin_word_input = False

        await message.reply(
            "🎮 Новая игра началась!\n\n"
            "В чате спрятаны 3 слова.\n"
            "Попробуйте их найти 😉"
        )

        return
    global game_active
    if not game_active:
        return
    if not message.text:
        return

    text = message.text.strip()
    lower_text = text.lower()
    solution = " ".join(KEY_WORDS.keys())

    if solution and solution == lower_text:
        game_active = False

        uid = str(message.from_user.id)

        username = message.from_user.username or message.from_user.first_name
        mention = f"@{username}" if message.from_user.username else message.from_user.full_name

        await message.reply(
            f"🏆 ПОБЕДИТЕЛЬ!\n"
            f"{mention} собрал все ключевые слова!\n\n"
            f"Слова: {' · '.join(KEY_WORDS.keys())}"
        )

        return

    if lower_text.startswith("/"):
        return

    uid = str(message.from_user.id)
    if uid not in notified:
        notified[uid] = set()

    # ─── Проверяем наличие любого ключевого слова в сообщении ───
    for word in KEY_WORDS:

        if re.search(r'\b' + re.escape(word) + r'\b', lower_text):

            if word not in notified[uid]:
                notified[uid].add(word)

                await message.reply(
                    "Ты очень близок, найди нужное слово! 🔑"
                )
        # ← после этого больше не даём эту фразу

    # ─── Проверяем, является ли сообщение ОДНИМ точным словом ───
    # Убираем знаки препинания по краям (душ. → душ, "душ" → душ и т.д.)
    clean = re.sub(r'^[^\wа-яА-ЯёЁ]+|[^\wа-яА-ЯёЁ]+$', '', text).strip()
    clean_lower = clean.lower()

    part = None
    for word, p in KEY_WORDS.items():
        if clean_lower == word:
            part = p
            break

    if part is None:
        return  # не отдельное правильное слово → дальше не идём

    # ─── Засчитываем ───
    if uid not in progress:
        progress[uid] = set()

    if part in progress[uid]:
        return  # уже было засчитано

    progress[uid].add(part)
    count = len(progress[uid])

    username = message.from_user.username or message.from_user.first_name
    mention = f"@{username}" if message.from_user.username else message.from_user.full_name

    if count == 3:
        game_active = False
        words = " · ".join(KEY_WORDS.keys())
        await message.reply(
            f"🏆 ПОБЕДИТЕЛЬ!\n"
            f"{mention} собрал все 3 части ключа!\n\n"
            f"Слова: {words}"
        )
    else:
        # Вот то, чего не хватало — сообщение при засчитывании части
        await message.reply(f"✅ Часть ключа засчитана! ({count}/3)")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
