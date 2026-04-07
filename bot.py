#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЦТ-Бот 2026 — Беларусь
Подготовка к централизованному тестированию
Предметы: Русский язык · Математика · Английский язык
"""

import asyncio
import logging
import sys
import os

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile
)

import config
from database import (
    init_db, get_or_create_user, get_user,
    save_test_result, get_user_stats,
    get_all_user_ids, count_users, get_all_results
)
from data.scores import SUBJECTS, primary_to_test, format_score_result, get_grade
from data.theory_russian import THEORY as RUS_TH, CATEGORIES as RUS_CATS
from data.theory_english import THEORY as ENG_TH, CATEGORIES as ENG_CATS
from data.theory_math    import THEORY as MAT_TH, CATEGORIES as MAT_CATS
from data.extra_exercises import EXTRA, CATEGORIES_EXTRA
from data.collections import BOOKS, get_book_path
from data.questions import TESTS_CATALOG
from keyboards import (
    main_menu_kb, subjects_kb, subject_menu_kb,
    tests_list_kb, past_years_kb, year_variants_kb,
    question_a_multi_kb, question_b_kb, skipped_list_kb,
    theory_from_test_kb, test_result_kb, start_test_kb,
    theory_cats_kb, theory_topics_kb, topic_back_kb,
    extra_list_kb, extra_back_kb,
    calc_menu_kb, calc_done_kb,
    collections_menu_kb, collection_files_kb,
    cabinet_kb, admin_kb, admin_cancel_kb, back_to_main_kb
)

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

# ─── States ───────────────────────────────────────────────────────────────────
class TestSt(StatesGroup):
    active = State()

class CalcSt(StatesGroup):
    waiting = State()

class AdminSt(StatesGroup):
    broadcast = State()

# ─── Maps ─────────────────────────────────────────────────────────────────────
THEORY_MAP = {"russian": RUS_TH, "math": MAT_TH, "english": ENG_TH}
CATS_MAP   = {"russian": RUS_CATS, "math": MAT_CATS, "english": ENG_CATS}
SUBJ_NAME  = {k: v["name"]  for k, v in SUBJECTS.items()}
SUBJ_EMOJI = {k: v["emoji"] for k, v in SUBJECTS.items()}

bot = Bot(token=config.BOT_TOKEN,
          default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp  = Dispatcher(storage=MemoryStorage())

# ─── Helpers ──────────────────────────────────────────────────────────────────
def is_admin(uid: int) -> bool:
    return uid in config.ADMIN_IDS

async def safe_edit(q: CallbackQuery, text: str, kb=None):
    try:
        await q.message.edit_text(text, reply_markup=kb)
    except Exception:
        await q.message.answer(text, reply_markup=kb)

async def send_long(target, text: str, kb=None):
    """Отправить длинный текст чанками по 4000 символов"""
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    msg = target.message if isinstance(target, CallbackQuery) else target
    for i, chunk in enumerate(chunks):
        reply_kb = kb if i == len(chunks) - 1 else None
        try:
            if i == 0 and isinstance(target, CallbackQuery):
                await msg.edit_text(chunk, reply_markup=reply_kb)
            else:
                await msg.answer(chunk, reply_markup=reply_kb)
        except Exception:
            await msg.answer(chunk, reply_markup=reply_kb)

def get_past_tests_by_year(subj: str) -> dict:
    """Группирует тесты прошлых лет по годам"""
    catalog = TESTS_CATALOG.get(subj, {})
    by_year = {}
    for key, info in catalog.items():
        if not info.get("is_2026"):
            # Extract year from title
            import re
            m = re.search(r'20\d\d[/–-]20\d\d', info["title"])
            year = m.group(0) if m else "Другие"
            by_year.setdefault(year, []).append((key, info["title"]))
    return by_year

# ─── /start ───────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await get_or_create_user(msg.from_user.id,
                             msg.from_user.username,
                             msg.from_user.full_name)
    name = msg.from_user.first_name or "друг"
    await msg.answer(
        f"👋 Привет, *{name}*!\n\n"
        "Я помогу тебе подготовиться к *ЦТ 2026*:\n\n"
        "📝 Русский язык\n"
        "📐 Математика\n"
        "🇬🇧 Английский язык\n\n"
        "Здесь есть теория из сборников РИКЗ, репетиционные тесты, "
        "доп. задания и калькулятор баллов.\n\n"
        "Выбери раздел:",
        reply_markup=main_menu_kb()
    )

@dp.message(Command("menu"))
async def cmd_menu(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("🏠 *Главное меню*", reply_markup=main_menu_kb())

@dp.message(Command("admin"))
async def cmd_admin(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    cnt = await count_users()
    await msg.answer(
        f"🛠 *Админ-панель*\n\n👥 Пользователей: *{cnt}*",
        reply_markup=admin_kb()
    )

# ─── Главное меню ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "main")
async def cb_main(q: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(q, "🏠 *Главное меню*\n\nВыбери раздел:", main_menu_kb())

@dp.callback_query(F.data == "subjects")
async def cb_subjects(q: CallbackQuery):
    await safe_edit(q, "📚 *Выберите предмет:*", subjects_kb())

@dp.callback_query(F.data.startswith("subj_"))
async def cb_subject(q: CallbackQuery, state: FSMContext):
    await state.clear()
    subj = q.data[5:]
    if subj not in SUBJECTS:
        return
    e = SUBJ_EMOJI[subj]
    n = SUBJ_NAME[subj]
    await safe_edit(q, f"{e} *{n}*\n\nЧто будем делать?",
                    subject_menu_kb(subj))

# ─── РТ 2026 ──────────────────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("rt2026_"))
async def cb_rt2026(q: CallbackQuery):
    subj = q.data[7:]
    tests_2026 = {k: v for k, v in TESTS_CATALOG.get(subj, {}).items()
                  if v.get("is_2026")}
    if not tests_2026:
        await q.answer("Тесты РТ 2026 пока добавляются!", show_alert=True)
        return
    await safe_edit(q,
        f"📋 *РТ 2026 — {SUBJ_NAME[subj]}*\n\nВыберите вариант:",
        tests_list_kb(subj, tests_2026, f"subj_{subj}")
    )

# ─── РТ прошлых лет ───────────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("rtpast_"))
async def cb_rtpast(q: CallbackQuery):
    subj = q.data[7:]
    by_year = get_past_tests_by_year(subj)
    if not by_year:
        await q.answer("Тесты прошлых лет загружаются...", show_alert=True)
        return
    await safe_edit(q,
        f"📂 *РТ прошлых лет — {SUBJ_NAME[subj]}*\n\nВыберите год:",
        past_years_kb(subj, by_year)
    )

@dp.callback_query(F.data.startswith("rtyear_"))
async def cb_rtyear(q: CallbackQuery):
    parts = q.data.split("_", 2)  # rtyear_{subj}_{year}
    subj = parts[1]
    year = parts[2]
    by_year = get_past_tests_by_year(subj)
    variants = by_year.get(year, [])
    if not variants:
        await q.answer("Нет доступных вариантов", show_alert=True)
        return
    await safe_edit(q,
        f"📅 *{year} — {SUBJ_NAME[subj]}*\n\nВыберите вариант:",
        year_variants_kb(subj, year, variants)
    )

# ─── Запуск теста ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("starttest_"))
async def cb_start_test(q: CallbackQuery, state: FSMContext):
    parts = q.data.split("_", 2)  # starttest_{subj}_{key}
    subj = parts[1]
    key  = parts[2]
    info = TESTS_CATALOG.get(subj, {}).get(key)
    if not info or not info.get("questions"):
        await q.answer("Тест не найден", show_alert=True)
        return

    questions = info["questions"]
    await state.set_state(TestSt.active)
    await state.update_data(
        subj=subj, test_key=key, title=info["title"],
        questions=questions,
        current=0,
        selected=[],
        answers={},
        skipped=[],
    )
    cnt = len(questions)
    await safe_edit(q,
        f"🚀 *{info['title']}*\n\n"
        f"Заданий: {cnt}\n"
        f"Рекомендуемое время: {cnt * 3} мин\n\n"
        f"Как работать:\n"
        f"Жми цифры чтобы выбрать ответ → *Подтвердить*\n"
        f"*Пропустить* — вернёшься позже\n"
        f"*Теория* — изучи тему, прогресс не сбрасывается\n\n"
        f"Удачи! 🍀",
        start_test_kb(subj)
    )

# ─── Показ вопроса ────────────────────────────────────────────────────────────
async def render_question(target, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    idx       = data["current"]
    selected  = data.get("selected", [])
    answers   = data.get("answers", {})
    skipped   = data.get("skipped", [])

    if idx >= len(questions):
        await finish_test(target, state)
        return

    q      = questions[idx]
    total  = len(questions)
    done   = len(answers)
    n_skip = len([i for i in skipped if str(i) not in answers])

    status = ""
    if str(idx) in answers:
        status = " ✏️"

    progress = f"*{q['id']}* | {idx+1} из {total}"
    if n_skip:
        progress += f" | ⏭ {n_skip} пропущено"
    progress += status

    text = f"{progress}\n{'━'*28}\n\n{q['text']}"
    if q["type"] in ("A_multi",):
        text += "\n\n_Выбери все верные варианты → Подтвердить_"
    elif q["type"] == "A_single":
        text += "\n\n_Выбери один вариант → Подтвердить_"
    elif q["type"] in ("B_text", "B_match"):
        text += "\n\n✏️ _Напиши ответ в чат_"

    th_key  = q.get("theory_key", "")
    th_hint = q.get("theory_hint", "Теория")

    if q["type"] in ("A_multi", "A_single"):
        kb = question_a_multi_kb(
            selected, idx, total,
            th_key, th_hint,
            n_skip > 0, done
        )
    else:
        kb = question_b_kb(idx, th_hint, n_skip > 0, done)

    msg = target.message if isinstance(target, CallbackQuery) else target
    try:
        if isinstance(target, CallbackQuery):
            await msg.edit_text(text, reply_markup=kb)
        else:
            await msg.answer(text, reply_markup=kb)
    except Exception:
        await msg.answer(text, reply_markup=kb)

async def advance(state: FSMContext) -> bool:
    """Перейти к следующему неотвеченному вопросу. True если нашли."""
    data = await state.get_data()
    questions = data["questions"]
    current   = data["current"]
    answers   = data.get("answers", {})
    skipped   = data.get("skipped", [])

    for i in range(current + 1, len(questions)):
        if str(i) not in answers and i not in skipped:
            await state.update_data(current=i, selected=[])
            return True
    for i in skipped:
        if str(i) not in answers:
            new_sk = [x for x in skipped if x != i]
            await state.update_data(current=i, selected=[], skipped=new_sk)
            return True
    return False

# ─── Навигация теста ──────────────────────────────────────────────────────────
@dp.callback_query(F.data == "qnext", TestSt.active)
async def cb_qnext(q: CallbackQuery, state: FSMContext):
    await q.answer()
    await render_question(q, state)

@dp.callback_query(F.data.startswith("qsel_"), TestSt.active)
async def cb_qsel(q: CallbackQuery, state: FSMContext):
    n = int(q.data[5:])
    data = await state.get_data()
    questions = data["questions"]
    idx = data["current"]
    qtype = questions[idx]["type"]
    selected = list(data.get("selected", []))

    if qtype == "A_single":
        selected = [n]
    else:
        if n in selected:
            selected.remove(n)
        else:
            selected.append(n)

    await state.update_data(selected=selected)
    await q.answer(f"Выбрано: {sorted(selected)}")
    await render_question(q, state)

@dp.callback_query(F.data == "qconfirm", TestSt.active)
async def cb_qconfirm(q: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", [])
    if not selected:
        await q.answer("⚠️ Выбери хотя бы один вариант!", show_alert=True)
        return
    idx = data["current"]
    answers = dict(data.get("answers", {}))
    answers[str(idx)] = sorted(selected)
    await state.update_data(answers=answers, selected=[])

    has_next = await advance(state)
    if not has_next:
        await q.answer("✅ Ответ принят! Все вопросы пройдены.")
        await finish_test(q, state)
    else:
        await q.answer("✅ Ответ принят!")
        await render_question(q, state)

@dp.message(TestSt.active)
async def handle_b_answer(msg: Message, state: FSMContext):
    """Обработка текстового ответа для части В"""
    data = await state.get_data()
    idx = data["current"]
    questions = data["questions"]
    if idx >= len(questions):
        return
    q = questions[idx]
    if q["type"] not in ("B_text", "B_match", "B_multi"):
        return

    answers = dict(data.get("answers", {}))
    answers[str(idx)] = msg.text.strip()
    await state.update_data(answers=answers, selected=[])

    has_next = await advance(state)
    if not has_next:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🏁 Посмотреть результаты", callback_data="qfinish")
        ]])
        await msg.answer("✅ Ответ принят! Все вопросы пройдены.", reply_markup=kb)
    else:
        await msg.answer("✅ Принято!")
        await render_question(msg, state)

@dp.callback_query(F.data == "qskip", TestSt.active)
async def cb_qskip(q: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx = data["current"]
    skipped = list(data.get("skipped", []))
    if idx not in skipped:
        skipped.append(idx)
    await state.update_data(skipped=skipped, selected=[])

    has_next = await advance(state)
    if not has_next:
        await q.answer("⏭ Пропущено")
        await finish_test(q, state)
    else:
        await q.answer("⏭ Пропущено, идём дальше")
        await render_question(q, state)

@dp.callback_query(F.data == "qskipped", TestSt.active)
async def cb_qskipped_list(q: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    skipped = data.get("skipped", [])
    answers = data.get("answers", {})
    unanswered = [i for i in skipped if str(i) not in answers]
    if not unanswered:
        await q.answer("Нет пропущенных вопросов!", show_alert=True)
        return
    await safe_edit(q,
        f"📋 *Пропущенные задания ({len(unanswered)}):*\n\nНажми на задание чтобы перейти к нему:",
        skipped_list_kb(questions, unanswered)
    )

@dp.callback_query(F.data.startswith("qgoto_"), TestSt.active)
async def cb_qgoto(q: CallbackQuery, state: FSMContext):
    idx = int(q.data[6:])
    data = await state.get_data()
    skipped = list(data.get("skipped", []))
    if idx in skipped:
        skipped.remove(idx)
    await state.update_data(current=idx, selected=[], skipped=skipped)
    await q.answer()
    await render_question(q, state)

@dp.callback_query(F.data == "qfinish", TestSt.active)
async def cb_qfinish(q: CallbackQuery, state: FSMContext):
    await q.answer()
    await finish_test(q, state)

# ─── Теория из теста ──────────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("qtheory_"), TestSt.active)
async def cb_qtheory(q: CallbackQuery, state: FSMContext):
    idx = int(q.data[8:])
    data = await state.get_data()
    subj = data["subj"]
    questions = data["questions"]
    if idx >= len(questions):
        return
    qobj = questions[idx]
    theory_key = qobj.get("theory_key", "")
    theory = THEORY_MAP.get(subj, {}).get(theory_key)
    if not theory:
        await q.answer("Теория по этой теме в разработке", show_alert=True)
        return

    await state.update_data(current=idx)
    kb = theory_from_test_kb(qobj["id"], idx)
    await send_long(q, theory, kb)

@dp.callback_query(F.data.startswith("qreturn_"), TestSt.active)
async def cb_qreturn(q: CallbackQuery, state: FSMContext):
    idx = int(q.data[8:])
    await state.update_data(current=idx, selected=[])
    await q.answer()
    await render_question(q, state)

# ─── Завершение теста ─────────────────────────────────────────────────────────
async def finish_test(target, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    answers   = data.get("answers", {})
    subj      = data["subj"]
    title     = data["title"]

    primary = 0
    lines = []

    for i, q in enumerate(questions):
        user_ans = answers.get(str(i))
        correct  = q["answer"]
        qtype    = q["type"]
        pts      = q.get("points", 2)
        partial  = q.get("partial", False)
        earned   = 0
        icon     = "⬜"

        if user_ans is None:
            icon = "⬜"
        elif qtype in ("A_single", "A_multi"):
            user_set    = set(user_ans) if isinstance(user_ans, list) else set()
            correct_set = set(correct.split(",") if isinstance(correct, str) else
                              [str(x) for x in correct])
            user_set_s  = {str(x) for x in user_set}
            if user_set_s == correct_set:
                earned = pts;  icon = "✅"
            elif partial and user_set_s.issubset(correct_set) and user_set_s:
                earned = pts - 1;  icon = "🔶"
            else:
                earned = 0;  icon = "❌"
        else:
            ua = str(user_ans).strip().lower().replace(" ", "")
            ca = str(correct).strip().lower().replace(" ", "")
            if ua == ca:
                earned = pts;  icon = "✅"
            else:
                earned = 0;   icon = "❌"

        primary += earned
        ans_show = correct if isinstance(correct, str) else str(sorted(correct))
        lines.append(f"{icon} *{q['id']}*: {earned}/{pts} (верно: {ans_show})")

    test_score = primary_to_test(subj, primary)
    max_p = SUBJECTS[subj]["max_primary"]
    grade = get_grade(test_score)

    uid = None
    if hasattr(target, "from_user"):
        uid = target.from_user.id
    if uid:
        await save_test_result(uid, subj, data["test_key"], primary, test_score, max_p)

    header = (
        f"🏁 *Результаты: {title}*\n\n"
        f"Первичный балл: *{primary}* из {max_p}\n"
        f"Тестовый балл: *{test_score}* из 100\n"
        f"{grade}\n\n"
        f"Разбор по заданиям:\n"
    )

    await state.clear()

    # Отправить по чанкам
    full_text = header + "\n".join(lines)
    kb = test_result_kb(subj)

    msg = target.message if isinstance(target, CallbackQuery) else target
    chunks = [full_text[i:i+4000] for i in range(0, len(full_text), 4000)]
    for i, chunk in enumerate(chunks):
        rkb = kb if i == len(chunks)-1 else None
        try:
            if i == 0 and isinstance(target, CallbackQuery):
                await msg.edit_text(chunk, reply_markup=rkb)
            else:
                await msg.answer(chunk, reply_markup=rkb)
        except Exception:
            await msg.answer(chunk, reply_markup=rkb)

# ─── Теория ───────────────────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("theory_"))
async def cb_theory(q: CallbackQuery):
    subj = q.data[7:]
    if subj not in CATS_MAP:
        return
    await safe_edit(q,
        f"📖 *Теория — {SUBJ_NAME[subj]}*\n\nВыбери раздел:",
        theory_cats_kb(subj, CATS_MAP[subj])
    )

@dp.callback_query(F.data.startswith("tcat_"))
async def cb_tcat(q: CallbackQuery):
    # tcat_{subj}_{cat_short}
    parts = q.data.split("_", 2)
    subj      = parts[1]
    cat_short = parts[2]
    cats = CATS_MAP.get(subj, {})
    full_cat = next((c for c in cats if c[:28] == cat_short), None)
    if not full_cat:
        await q.answer("Раздел не найден", show_alert=True)
        return
    topics = cats[full_cat]
    await safe_edit(q,
        f"📚 *{full_cat}*\n\nВыбери тему:",
        theory_topics_kb(subj, cat_short, topics)
    )

@dp.callback_query(F.data.startswith("topic_"))
async def cb_topic(q: CallbackQuery):
    parts = q.data.split("_", 2)
    subj = parts[1]
    key  = parts[2]
    theory = THEORY_MAP.get(subj, {}).get(key)
    if not theory:
        await q.answer("Теория не найдена", show_alert=True)
        return
    cats = CATS_MAP.get(subj, {})
    cat_short = ""
    for cname, topics in cats.items():
        if any(k == key for _, k in topics):
            cat_short = cname[:28]
            break
    await send_long(q, theory, topic_back_kb(subj, cat_short))

# ─── Доп. задания ─────────────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("extra_"))
async def cb_extra(q: CallbackQuery):
    parts = q.data.split("_", 2)
    if len(parts) == 2:
        # Список доп. заданий для предмета
        subj = parts[1]
        items_by_subj = CATEGORIES_EXTRA.get(subj, {})
        if not items_by_subj:
            await q.answer("Доп. задания для этого предмета пока добавляются!", show_alert=True)
            return
        all_items = []
        for cat, lst in items_by_subj.items():
            all_items.extend(lst)
        await safe_edit(q,
            f"✏️ *Дополнительные задания — {SUBJ_NAME[subj]}*\n\nВыбери упражнение:",
            extra_list_kb(subj, all_items)
        )
    elif len(parts) == 3:
        # Конкретное задание
        subj = parts[1]
        key  = parts[2]
        text = EXTRA.get(key)
        if not text:
            await q.answer("Задание не найдено", show_alert=True)
            return
        await send_long(q, text, extra_back_kb(subj))

# ─── Калькулятор ──────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "calc_menu")
async def cb_calc_menu(q: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(q,
        "🧮 *Калькулятор баллов*\n\nВыберите предмет:",
        calc_menu_kb()
    )

@dp.callback_query(F.data.startswith("calc_"))
async def cb_calc_subj(q: CallbackQuery, state: FSMContext):
    subj = q.data[5:]
    if subj not in SUBJECTS:
        return
    info = SUBJECTS[subj]
    await state.set_state(CalcSt.waiting)
    await state.update_data(calc_subj=subj)
    await safe_edit(q,
        f"🧮 *{info['name']}*\n\n"
        f"Максимальный первичный балл: *{info['max_primary']}*\n\n"
        f"Формула начисления:\n{info['calc_hint']}\n\n"
        f"Введи свой первичный балл (0–{info['max_primary']}):",
        InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="◀️ Отмена", callback_data="calc_menu")
        ]])
    )

@dp.message(CalcSt.waiting)
async def handle_calc(msg: Message, state: FSMContext):
    data = await state.get_data()
    subj = data.get("calc_subj")
    if not subj:
        await state.clear()
        return
    try:
        score = int(msg.text.strip())
    except ValueError:
        await msg.answer("⚠️ Введи целое число!")
        return
    max_p = SUBJECTS[subj]["max_primary"]
    if not (0 <= score <= max_p):
        await msg.answer(f"⚠️ Балл должен быть от 0 до {max_p}")
        return
    await state.clear()
    await msg.answer(format_score_result(subj, score), reply_markup=calc_done_kb(subj))

# ─── Сборники ─────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "collections")
async def cb_collections(q: CallbackQuery):
    await safe_edit(q,
        "📚 *Сборники*\n\nВыбери предмет — отправлю файл сборника:",
        collections_menu_kb()
    )

@dp.callback_query(F.data.startswith("col_"))
async def cb_col_subj(q: CallbackQuery):
    subj = q.data[4:]
    books = BOOKS.get(subj)
    if not books:
        await q.answer("Нет сборников для этого предмета", show_alert=True)
        return
    text = f"📚 *{books['name']}*\n\nНажми на сборник — получи PDF:"
    await safe_edit(q, text, collection_files_kb(subj, books["files"]))

@dp.callback_query(F.data.startswith("sendbook_"))
async def cb_sendbook(q: CallbackQuery):
    # sendbook_{subj}_{idx}
    parts = q.data.split("_")
    subj = parts[1]
    idx  = int(parts[2])
    books = BOOKS.get(subj, {}).get("files", [])
    if idx >= len(books):
        await q.answer("Файл не найден", show_alert=True)
        return
    book = books[idx]
    fpath = get_book_path(book["filename"])
    if not fpath:
        await q.answer(
            f"Файл {book['filename']} не найден на сервере.\n"
            "Добавьте PDF файлы в папку media/books/",
            show_alert=True
        )
        return

    await q.answer("📤 Отправляю файл...")
    try:
        doc = FSInputFile(fpath, filename=book["filename"])
        await q.message.answer_document(
            doc,
            caption=f"*{book['title']}*\n\n{book['desc']}"
        )
    except Exception as e:
        logger.error(f"Error sending book: {e}")
        await q.message.answer("❌ Ошибка при отправке файла. Попробуй позже.")

# ─── Личный кабинет ───────────────────────────────────────────────────────────
@dp.callback_query(F.data == "cabinet")
async def cb_cabinet(q: CallbackQuery):
    user = await get_user(q.from_user.id)
    if not user:
        await q.answer("Не найдено", show_alert=True)
        return
    stats = await get_user_stats(q.from_user.id)
    name = q.from_user.first_name or "Пользователь"

    text = (
        f"👤 *Личный кабинет*\n\n"
        f"Привет, *{name}*!\n\n"
        f"Тестов решено: *{user['tests_done']}*\n"
        f"Лучший тестовый балл: *{user['best_score']}*\n"
        f"Последний предмет: {SUBJ_EMOJI.get(user.get('last_subject', ''), '') or '—'} "
        f"{SUBJ_NAME.get(user.get('last_subject', ''), '—')}\n"
        f"В боте с: {str(user.get('joined_at', ''))[:10]}\n\n"
    )

    if stats:
        text += "📈 *По предметам:*\n"
        for s in stats:
            sn = SUBJ_NAME.get(s["subject"], s["subject"])
            se = SUBJ_EMOJI.get(s["subject"], "")
            text += f"{se} {sn}: {s['cnt']} тестов, лучший балл *{s['best']}*\n"

    await safe_edit(q, text, cabinet_kb())

@dp.callback_query(F.data == "cab_stats")
async def cb_cab_stats(q: CallbackQuery):
    await cb_cabinet(q)

# ─── Админ ────────────────────────────────────────────────────────────────────
@dp.callback_query(F.data == "adm_stats")
async def cb_adm_stats(q: CallbackQuery):
    if not is_admin(q.from_user.id):
        return
    cnt = await count_users()
    results = await get_all_results()
    text = f"📊 *Статистика бота*\n\n👥 Пользователей: *{cnt}*\n\nТесты:\n"
    for r in results:
        sn = SUBJ_NAME.get(r["subject"], r["subject"])
        avg = round(r["avg"] or 0, 1)
        text += f"{sn}: {r['cnt']} сдач, средний балл {avg}\n"
    await safe_edit(q, text, admin_kb())

@dp.callback_query(F.data == "adm_broadcast")
async def cb_adm_broadcast(q: CallbackQuery, state: FSMContext):
    if not is_admin(q.from_user.id):
        return
    await state.set_state(AdminSt.broadcast)
    await safe_edit(q,
        "📣 *Рассылка*\n\n"
        "Напиши сообщение для рассылки всем пользователям.\n"
        "Поддерживается Markdown (жирный, курсив).",
        admin_cancel_kb()
    )

@dp.callback_query(F.data == "adm_cancel")
async def cb_adm_cancel(q: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(q, "❌ Рассылка отменена.", admin_kb())

@dp.message(AdminSt.broadcast)
async def handle_broadcast(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    text = msg.text
    ids  = await get_all_user_ids()
    sent = failed = 0
    await msg.answer(f"📤 Рассылка {len(ids)} пользователям...")
    for uid in ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await msg.answer(
        f"✅ *Рассылка завершена*\n\nОтправлено: {sent}\nНе доставлено: {failed}",
        reply_markup=admin_kb()
    )

# ─── Main ─────────────────────────────────────────────────────────────────────
async def main():
    await init_db()
    logger.info("DB initialized")

    # Подготовить папку с книгами
    from data.collections import prepare_books
    copied = prepare_books()
    if copied:
        logger.info(f"Copied {copied} book files to media/books/")

    if config.WEBHOOK_URL:
        from aiohttp import web
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
        webhook_path = "/webhook"
        await bot.set_webhook(f"{config.WEBHOOK_URL}{webhook_path}")
        logger.info(f"Webhook: {config.WEBHOOK_URL}{webhook_path}")
        app = web.Application()
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)
        setup_application(app, dp, bot=bot)
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", config.PORT).start()
        logger.info(f"Server on port {config.PORT}")
        await asyncio.Event().wait()
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Polling...")
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
