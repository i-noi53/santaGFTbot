# quest.py
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import aiofiles
from aiogram import types

PROGRESS_FILE = Path("quest_progress.json")
LOCK = asyncio.Lock()

DEFAULT_DATA = {
    "active": False,
    "current_stage": 0,
    "discovered": [],
    "full_key": None,
    "winner": None,
    "winner_id": None,
    "winner_name": None,
    "winner_time": None,
    "group_chat_id": None,
    "stages": {}
}

class QuestManager:
    def __init__(self):
        self.data: Dict[str, Any] = None

    async def _load(self):
        async with LOCK:
            if not PROGRESS_FILE.exists():
                self.data = DEFAULT_DATA.copy()
                # Сохраняем дефолт сразу
                async with aiofiles.open(PROGRESS_FILE, mode="w", encoding="utf-8") as f:
                    await f.write(json.dumps(self.data, ensure_ascii=False, indent=2))
            else:
                async with aiofiles.open(PROGRESS_FILE, mode="r", encoding="utf-8") as f:
                    content = await f.read()
                    if content.strip():
                        self.data = json.loads(content)
                    else:
                        self.data = DEFAULT_DATA.copy()
                        # Если файл пустой — перезаписываем дефолт
                        async with aiofiles.open(PROGRESS_FILE, mode="w", encoding="utf-8") as f:
                            await f.write(json.dumps(self.data, ensure_ascii=False, indent=2))

    async def _save(self):
        if self.data is None:
            await self._load()  # на всякий случай
        async with LOCK:
            async with aiofiles.open(PROGRESS_FILE, mode="w", encoding="utf-8") as f:
                await f.write(json.dumps(self.data, ensure_ascii=False, indent=2))

    async def ensure_loaded(self):
        if self.data is None:
            await self._load()

    async def start(self, chat_id: int):
        await self.ensure_loaded()
        self.data.update({
            "active": True,
            "current_stage": 0,
            "discovered": [],
            "stages": {},
            "winner": None,
            "group_chat_id": chat_id
        })
        await self._save()

    async def stop(self):
        await self.ensure_loaded()
        self.data["active"] = False
        await self._save()

    async def set_key(self, key: str):
        if len(key) != 12:
            raise ValueError("Ключ ровно 12 символов!")
        await self.ensure_loaded()
        self.data["full_key"] = key.upper()
        await self._save()

    async def is_active(self) -> bool:
        await self.ensure_loaded()
        return self.data.get("active", False)

    async def get_current_stage(self) -> int:
        await self.ensure_loaded()
        return self.data["current_stage"]

    async def get_next_riddle_text(self, stage: int) -> str:
        if stage == 2:
            return """🔓 Загадка №2

    В тишине иногда появляются сигналы.
Не слова. Не звук.
Лишь короткие вспышки смысла, разбитые на точки и тире.

Кто-то оставил один из таких сигналов.

--. --- --- -..   .-.. .. ... - . -. . .-.

Те, кто умеют слушать, знают —
даже тишина может говорить.

Когда ты услышишь то, что скрыто внутри,
увидишь два слова.

Смотри не на всё сразу.
Иногда достаточно самого первого шага.

Именно он укажет следующий символ.

Напиши в чат:
Riddleбуква
    """

        if stage == 3:
            return """🔓 Загадка №3

    Иногда смысл скрывается внутри оболочки.
Как будто сообщение запечатали,
чтобы его смог открыть только тот,
кто знает, где искать.

Вот такая оболочка:

ZWRl

Но даже после того как она откроется —
не спеши.

Иногда правда смотрит на тебя
только тогда, когда ты переворачиваешь всё наоборот.

Когда увидишь строку в её истинном виде,
присмотрись к третьему знаку.

Он продолжит ключ.

Напиши в чат:
BASE64буква
    """
        if stage == 4:
            return """🔓 Загадка №4

В мире игр есть инструменты,
которые позволяют увидеть то,
что обычным игрокам недоступно.

Сквозь стены.
Сквозь границы.
Сквозь саму игру.

Ты наверняка слышал об этом.

Иногда достаточно одного короткого слова,
которое знают все,
кто хоть раз хотел заглянуть чуть дальше, чем разрешено.

Думай на русском.
Но ответ напиши на английском.

И возьми лишь одну букву.
В игровых мирах с ней ты постоянно, в жизни же только на смартфоне.
Думая о ней, думай на русском языке, когда найдешь ее 4 символ, переверни mind.

Напиши в чат:
GAMEбуква
      
    """
        if stage == 5:
            return """🔓 Загадка №5

        Иногда ответ лежит прямо перед глазами,
но буквы стоят не на своих местах.

Как будто кто-то взял простую вещь
и слегка перемешал её,
чтобы проверить, заметишь ли ты.

Перед тобой всего лишь буквы.

О Д И Н

Они знают, чем хотят стать.
Им просто нужно вернуться на своё место.

Когда порядок восстановится,
ты увидишь число.

И именно оно продолжит ключ.

Напиши в чат:
ANAGRAMбуква
        """
        if stage == 6:
            return """🔓 Загадка №6

        Иногда ответы не прячутся в тексте.
Иногда они ждут тебя на карте.

Есть точка, которую знает почти каждый.

55.7558, 37.6173

Открой карту.
Посмотри, что находится там.

Но не ищи одиночество.

Смотри туда, где много.
Где чем больше — тем лучше.

Название этого места подскажет путь.



Напиши в чат:
MAPбуква
        """
        if stage == 7:
            return """🔓 Загадка №7

       Некоторые сообщения не пишут словами.
Их рисуют.

Чёрно-белая матрица.
Квадраты, которые на первый взгляд ничего не значат.

Но стоит лишь посмотреть на них правильным взглядом —
и изображение начинает говорить.

И этого будет достаточно.

Напиши в чат:
SCANбуква
        """
        if stage == 8:
            return """🔓 Загадка №8

Иногда слово исчезает,
оставляя после себя лишь след.

Отпечаток.
Цифровую тень.

Вот такой след:

0d107d09f5bbe40cade3de5c71e9e9b7

Это не случайный набор символов.
Это имя, спрятанное внутри хеша.

Найди его.

Когда увидишь слово —
посмотри на его первую букву.
Войди в него. Слейся с ним воедино.

Она и продолжит ключ.

Напиши в чат:
HASHбуква 
        """
        if stage == 9:
            return """🔓 Загадка №9

Некоторые сообщения выглядят обрез.
Как будто кто-то остав лишь ча фра.

Вот одна из таких стр:

dGhpcyBpcyBi

Она всё ещё хран смысл,
но тол для тех, кто знает яз код.

Отк её.

Когда сооб станет чит —
посмо на послед бук.

Она вед дал.

Напиши в чат:
BASEбуква
        """
        if stage == 10:
            return """🔓 Загадка №10
Иногда справедливость приходит быстро. Возмездие настигает.

Без лишних слов.
Без лишних движений.

Как стрелка на циферблате,
которая идёт только вперёд…
но иногда всё решает обратное направление.
Римляне были правы, они не просто так изобрели часы.
Сейчас часы судного дня запущены во всю, время тикает. 
Стрелки всегда укажут правильную дорогу, нужно лишь читать их знаки.
Открой в себе знание времени, пропусти через себя ключи.
Посмотри внимательно.

Ответ уже рядом —
его просто нужно развернуть.

Напиши в чат:
REVERбуква
        """


        if stage == 11:
            return """🔓 Загадка №11

 Иногда сообщение прячется не в словах,
а в том, как они начинаются.

Прочитай это внимательно:

****удь ****дителен, ****рат. ****удущее уже здесь.

Некоторые буквы исчезли.
Но они оставили после себя след.

Посмотри на начало.

Иногда именно первые знаки
говорят больше, чем всё предложение.

Одна буква ждёт тебя здесь.

Напиши в чат:
ACROбуква"""
        if stage == 12:
            return """
            У всего есть начало... и конец.
Это не просто фраза.
Это закон, который правит всем, что ты видел в этой цепочке.
Ты начал с нуля — с первого символа, который был спрятан в самом первом файле, в самом первом вздохе этой игры.
Ты прошёл через шифры, перевернутые слова, скрытые изображения, звуки, которые шептали правду только тем, кто умел слушать.
Ты собрал осколки.
И теперь, на самом краю, ты стоишь перед последней дверью.
Всё возвращается туда, откуда пришло.
Начало было 0 — пустотой, тишиной, точкой, из которой родилось всё остальное.
Конец тоже будет той же пустотой, но уже наполненной смыслом, тем, что ты сам в неё вложил.
Это не случайность.
Это круг.
Ты не просто нашёл ключ.
Ты замкнул цикл.
Теперь напиши его полностью — ровно 12 символов, без пробелов, без лишних знаков, без сомнений.
Вводи его в чат.
И когда бот ответит — знай: ты не просто прошёл игру.
Ты завершил круг.
Ты доказал, что способен увидеть начало в конце и конец в начале.
Победа не в ключе.
Победа в том, что ты дошёл до этого момента.
Введи ключ.
Замкни круг.
И пусть тишина после этого будет громче всего, что было до.
            """

        # Для остальных этапов пока заглушка
        return f"""🔎 Загадка №{stage}
        

    [Здесь будет текст загадки {stage}]

    Напиши: Riddle + символ
    (или другой префикс, если изменишь шаблон)"""

    async def try_solve(self, stage: int, symbol: str, user: types.User) -> tuple[bool, str]:
        await self.ensure_loaded()
        if not self.data["active"]:
            return False, "Квест не активен"

        current = self.data["current_stage"]
        if stage != current + 1:
            return False, f"Сейчас этап {current + 1}"

        expected = self.data["full_key"][stage - 1]
        symbol_clean = symbol.strip().upper()

        stage_key = str(stage)
        if stage_key not in self.data["stages"]:
            self.data["stages"][stage_key] = {"symbol": expected, "solved_by": None, "time": None, "attempts": []}

        self.data["stages"][stage_key]["attempts"].append({
            "uid": user.id, "name": user.username or user.full_name,
            "attempt": symbol_clean, "ts": datetime.utcnow().isoformat()
        })

        if symbol_clean == expected:
            if not self.data["stages"][stage_key]["solved_by"]:
                self.data["stages"][stage_key]["solved_by"] = user.id
                self.data["stages"][stage_key]["time"] = datetime.utcnow().isoformat()

            if expected not in self.data["discovered"]:
                self.data["discovered"].append(expected)

            self.data["current_stage"] = stage

            if stage == 12:
                self.data["winner"] = user.username or user.full_name
                self.data["winner_id"] = user.id
                self.data["winner_name"] = user.username
                self.data["winner_time"] = datetime.utcnow().isoformat()
                self.data["active"] = False
                await self._save()
                return True, f"🎉 КВЕСТ ПРОЙДЕН! Победитель @{self.data['winner']}\nКлюч: {''.join(self.data['discovered'])}"

            await self._save()
            return True, f"✅ Верно! Символ {stage}: {expected} "

        await self._save()
        return False, "❌ Неправильно"


quest_manager = QuestManager()
