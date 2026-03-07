# ─── Квест-команды ───────────────────────────────────────────────

@dp.message(Command("qstart"))
async def q_start(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await quest_manager.start(message.chat.id)
    await message.reply("Квест запущен! Первая загадка уже в чате 🔥")
    await post_first_riddle(message.chat.id)


@dp.message(Command("qstop"))
async def q_stop(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await quest_manager.stop()
    await message.reply("Квест остановлен.")


@dp.message(Command("qsetkey"))
async def q_setkey(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.reply("Напиши /qsetkey ТВОЙ12СИМВОЛЬНЫЙКЛЮЧ")
        return

    key = parts[1].strip()
    try:
        await quest_manager.set_key(key)
        await message.reply("Ключ установлен ✅")
    except ValueError as e:
        await message.reply(str(e))


@dp.message(Command("qstatus"))
async def q_status(message: Message):
    await quest_manager.ensure_loaded()
    data = quest_manager.data
    stage = data.get("current_stage", 0)
    disc = "".join(data.get("discovered", []))
    winner = data.get("winner")
    if winner:
        await message.reply(f"Квест завершён! Победитель: @{winner}\nКлюч: {disc}")
    else:
        await message.reply(f"Этап: {stage + 1}/12   Открыто: {len(disc)}/12   {disc or '—'}")


# ─── АВТОМАТИЧЕСКАЯ ОТПРАВКА ЗАГАДОК ─────────────────────────────

async def post_first_riddle(chat_id: int):
    await quest_manager.ensure_loaded()

    if not quest_manager.data.get("full_key"):
        await bot.send_message(chat_id, "Сначала выполни /qsetkey [ключ]")
        return

    symbol1 = quest_manager.data["full_key"][0]

    variants = [
        f"""Открывай меня...

Ты нашёл дверь в большую игру.
Многие сдались ещё на первом шаге.
Но ты здесь.

Первый символ уже у тебя.
Когда найдёшь его — напиши ровно так:

Solvering{symbol1}

(без пробелов, без кавычек)

Это только начало цепочки.
Готов идти до конца?""",

        f"""Привет, искатель.

Ты только что открыл портал.
Цепочка ждёт именно тебя.

Первый символ спрятан в этом файле.
Найди его и отправь в чат:

Solvering{symbol1}

Удачи, брат. Не сдавайся на полпути 🔥""",

        f"""Добро пожаловать в квест.

Здесь нет случайностей.
Ты уже на шаг ближе к ключу.

Первый символ — твой.
Напиши в чат:

Solvering{symbol1}

Следующая загадка откроется автоматически.
Погнали!"""
    ]

    text = random.choice(variants)

    document_file = BufferedInputFile(
        file=text.encode("utf-8"),
        filename="open_me.txt"
    )

    await bot.send_document(
        chat_id=chat_id,
        document=document_file,
        caption="📂 Первая загадка открыта! Открывай файл 👀"
    )


async def post_next_riddle(stage: int, chat_id: int):
    text = await quest_manager.get_next_riddle_text(stage)
    if stage == 4:
        # Отправляем локальную картинку + текст загадки в caption
        photo_path = "riddle4.png"  # ← путь к твоей картинке (относительный от bot.py)

        await bot.send_photo(
            chat_id=chat_id,
            photo=FSInputFile(photo_path),
            caption=f"🔓 Загадка №4 открыта!\n\n{text}"
        )
    elif stage == 7:
        qr_path = "symbolS.png"  # ← твой путь к файлу
        await bot.send_photo(
            chat_id=chat_id,

            photo=FSInputFile(qr_path),
            caption=f"🔓 Загадка №7 открыта!\n\n{text}"
        )
    else:
        await bot.send_message(
            chat_id,
            f"🔓 Следующая загадка открыта!\n\n{text}\n\n"
        )


# ─── Хендлер для Solvering (этап 1) и Riddle (этапы 2–12) ───────

@dp.message()
async def solver_handler(message: Message):
    if not await quest_manager.is_active():
        return

    text = message.text.strip()
    lower = text.lower()

    current_stage = await quest_manager.get_current_stage()
    next_stage = current_stage + 1

    symbol = None

    # Этап 1 — только Solvering
    if next_stage == 1:
        match = re.match(r'^solvering\s*([^\s])?$', lower, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper() if match.group(1) else ""
    elif next_stage == 2:
        match = re.match(r'^riddle\s*([^\s])?$', lower, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper() if match.group(1) else ""
    elif next_stage == 3:
        match = re.match(r'^base64\s*([^\s])?$', lower, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper() if match.group(1) else ""
    elif next_stage == 4:
       match = re.match(r'^GAME\s*([^\s])?$', lower, re.IGNORECASE)
       if match:
            symbol = match.group(1).upper() if match.group(1) else ""
    elif next_stage == 5:
       match = re.match(r'^ANAGRAM\s*([^\s])?$', lower, re.IGNORECASE)
       if match:
            symbol = match.group(1).upper() if match.group(1) else ""
    elif next_stage == 6:
        match = re.match(r'^map\s*([^\s])?$', lower, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper() if match.group(1) else ""
            prefix = "MAP"
    elif next_stage == 7:
        # Этап 7 — QR-код
        match = re.match(r'^SCAN\s*([^\s])?$', lower, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper() if match.group(1) else ""
            prefix = "SCAN"
    elif next_stage == 8:
        match = re.match(r'^hash\s*([^\s])?$', lower, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper() if match.group(1) else ""
            prefix = "HASH"
    elif next_stage == 9:
        match = re.match(r'^BASE\s*([^\s])?$', lower, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper() if match.group(1) else ""
            prefix = "BASE"
    elif next_stage == 10:
        match = re.match(r'^reverse\s*([^\s])?$', lower, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper() if match.group(1) else ""
            prefix = "REVER"
    elif next_stage == 11:
        match = re.match(r'^acro\s*([^\s])?$', lower, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper() if match.group(1) else ""
            prefix = "ACRO"
    elif next_stage == 12:
            # Финал — проверка полного ключа целиком
            await quest_manager.ensure_loaded()

            if quest_manager.data is None or quest_manager.data.get("full_key") is None:
                await message.reply("Ключ ещё не установлен (админ должен выполнить /qsetkey)")
                return

            # Очищаем ввод от всего лишнего (пробелы, знаки, регистр)
            clean_input = ''.join(c for c in lower if c.isalnum())
            expected = quest_manager.data["full_key"].lower()

            if clean_input == expected:
                # Засчитываем последний символ (0)
                symbol = expected[-1].upper()  # '0'
                success, reply = await quest_manager.try_solve(next_stage, symbol, message.from_user)
                await message.reply(
                    reply + "\n\n"
                            "🎉 ПОЛНЫЙ КЛЮЧ ПРИНЯТ!\n\n"
                            "У всего есть начало... и конец.\n"
                            "Ты замкнул круг.\n"
                            "Ты победитель этого пути.\n\n"
                            f"Ключ: **{expected.upper()}**\n"
                            "Спасибо, что дошёл до конца. Ты — легенда."
                )
                # Можно добавить: отправить тебе в личку или в админ-группу уведомление о победителе
            else:
                await message.reply(
                    "Ключ не совпадает.\n"
                    "Проверь длину (ровно 12 символов), порядок и отсутствие лишних знаков.\n"

                )
    else:
        match = re.match(r'^riddle\s*([^\s])?$', lower, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper() if match.group(1) else ""

    if symbol is None or not symbol:
        return  # Не подходит под текущий шаблон → передаём в game_handler

    if len(symbol) != 1:
        await message.reply("Нужен ровно один символ после префикса")
        return

    success, reply = await quest_manager.try_solve(next_stage, symbol, message.from_user)
    await message.reply(reply)

    if success and next_stage < 12:
        chat_id = quest_manager.data.get("group_chat_id")
        if chat_id:
            await post_next_riddle(next_stage + 1, chat_id)

