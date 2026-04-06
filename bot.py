#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЦТ-Бот 2026 — Подготовка к ЦТ (Беларусь)
Предметы: Русский язык, Математика, Английский язык
"""

import asyncio
import logging
import sys
import json

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)

import config
from database import init_db, get_or_create_user, get_user, save_test_result, \
    get_user_stats, get_all_user_ids, count_users, get_all_results
from data.scores import SUBJECTS, primary_to_test, format_score_result, get_grade
from data.theory_russian import THEORY as RUS_THEORY, CATEGORIES as RUS_CATS
from data.theory_english import THEORY as ENG_THEORY, CATEGORIES as ENG_CATS
from data.theory_math import THEORY as MATH_THEORY, CATEGORIES as MATH_CATS
from data.collections import COLLECTIONS
from data.questions import TESTS_CATALOG
from keyboards import (
    main_menu_kb, subjects_kb, subject_menu_kb, rt_2026_kb, rt_past_years_kb,
    rt_year_files_kb, theory_categories_kb, theory_topics_kb, theory_back_kb,
    calc_subject_kb, calc_done_kb, collections_kb, collections_back_kb,
    cabinet_kb, admin_kb, admin_cancel_kb, main_menu_btn
)

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# ─── FSM States ───────────────────────────────────────────────
class TestState(StatesGroup):
    in_test = State()

class CalcState(StatesGroup):
    waiting_score = State()

class AdminState(StatesGroup):
    waiting_broadcast = State()

# ─── Theory map ───────────────────────────────────────────────
THEORY_MAP = {
    "russian": RUS_THEORY,
    "math":    MATH_THEORY,
    "english": ENG_THEORY,
}
CATS_MAP = {
    "russian": RUS_CATS,
    "math":    MATH_CATS,
    "english": ENG_CATS,
}

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher(storage=MemoryStorage())

# ══════════════════════════════════════════════════════════════
# UTILS
# ══════════════════════════════════════════════════════════════
def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS

def subj_name(key: str) -> str:
    return SUBJECTS.get(key, {}).get("name", key)

def subj_emoji(key: str) -> str:
    return SUBJECTS.get(key, {}).get("emoji", "")

async def safe_edit(query: CallbackQuery, text: str, kb=None):
    try:
        await query.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    except Exception:
        await query.message.answer(text, reply_markup=kb, parse_mode="Markdown")

# ══════════════════════════════════════════════════════════════
# /START
# ══════════════════════════════════════════════════════════════
@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await get_or_create_user(msg.from_user.id,
                              msg.from_user.username,
                              msg.from_user.full_name)
    name = msg.from_user.first_name or "друг"
    text = (
        f"👋 Привет, *{name}*!\n\n"
        "Я помогу тебе подготовиться к *ЦТ 2026* по:\n"
        "📝 Русскому языку\n"
        "📐 Математике\n"
        "🇬🇧 Английскому языку\n\n"
        "Выбери раздел:"
    )
    await msg.answer(text, reply_markup=main_menu_kb())

@dp.message(Command("menu"))
async def cmd_menu(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("🏠 *Главное меню*", reply_markup=main_menu_kb())

@dp.message(Command("admin"))
async def cmd_admin(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    cnt = await count_users()
    await msg.answer(f"🛠 *Админ-панель*\n\n👥 Пользователей: *{cnt}*",
                     reply_markup=admin_kb())

# ══════════════════════════════════════════════════════════════
# MAIN NAVIGATION
# ══════════════════════════════════════════════════════════════
@dp.callback_query(F.data == "main")
async def cb_main(q: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(q, "🏠 *Главное меню*\n\nВыбери раздел:", main_menu_kb())

@dp.callback_query(F.data == "subjects")
async def cb_subjects(q: CallbackQuery):
    await safe_edit(q, "📚 *Выберите предмет:*", subjects_kb())

@dp.callback_query(F.data.startswith("subj_"))
async def cb_subject_menu(q: CallbackQuery, state: FSMContext):
    await state.clear()
    subj = q.data.split("_", 1)[1]
    e = subj_emoji(subj)
    name = subj_name(subj)
    text = f"{e} *{name}*\n\nВыберите действие:"
    await safe_edit(q, text, subject_menu_kb(subj))

# ══════════════════════════════════════════════════════════════
# РТ 2026
# ══════════════════════════════════════════════════════════════
@dp.callback_query(F.data.startswith("rt_") & F.data.endswith("_2026"))
async def cb_rt_2026(q: CallbackQuery):
    subj = q.data.replace("rt_", "").replace("_2026", "")
    variants = list(TESTS_CATALOG.get(subj, {}).keys())
    if not variants:
        await q.answer("Тесты не найдены", show_alert=True)
        return
    buttons = []
    for v in variants:
        info = TESTS_CATALOG[subj][v]
        buttons.append([InlineKeyboardButton(
            text=f"📝 {info['title']}", callback_data=f"starttest_{subj}_{v}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"subj_{subj}")])
    await safe_edit(q, f"📋 *РТ 2026 — {subj_name(subj)}*\n\nВыберите вариант:",
                    InlineKeyboardMarkup(inline_keyboard=buttons))

# ══════════════════════════════════════════════════════════════
# РТ ПРОШЛЫХ ЛЕТ
# ══════════════════════════════════════════════════════════════
@dp.callback_query(F.data.startswith("rt_") & F.data.endswith("_past"))
async def cb_rt_past(q: CallbackQuery):
    subj = q.data.replace("rt_", "").replace("_past", "")
    # Build years list from catalog (past year PDFs)
    past_links = {
        "russian": [
            ("2024–2025", "https://rikc.by/ru/rt/"),
            ("2023–2024", "https://rikc.by/ru/rt/"),
            ("2022–2023", "https://rikc.by/ru/rt/"),
            ("2021–2022", "https://rikc.by/ru/rt/"),
            ("2020–2021", "https://rikc.by/ru/rt/"),
        ],
        "math": [
            ("2024–2025", "https://rikc.by/ru/rt/"),
            ("2023–2024", "https://rikc.by/ru/rt/"),
            ("2022–2023", "https://rikc.by/ru/rt/"),
            ("2020–2021", "https://rikc.by/ru/rt/"),
        ],
        "english": [
            ("2024–2025", "https://rikc.by/ru/rt/"),
            ("2023–2024", "https://rikc.by/ru/rt/"),
            ("2022–2023", "https://rikc.by/ru/rt/"),
        ],
    }
    links = past_links.get(subj, [])
    text = f"📂 *РТ прошлых лет — {subj_name(subj)}*\n\n"
    text += "Архив репетиционных тестов РИКЗ:\n"
    for year, url in links:
        text += f"▪️ [{year}]({url})\n"
    text += "\n[📥 Все РТ на сайте РИКЗ](https://rikc.by/ru/rt/)"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"subj_{subj}")]
    ])
    await safe_edit(q, text, kb)

# ══════════════════════════════════════════════════════════════
# TEST ENGINE
# ══════════════════════════════════════════════════════════════
@dp.callback_query(F.data.startswith("starttest_"))
async def cb_start_test(q: CallbackQuery, state: FSMContext):
    _, subj, variant = q.data.split("_", 2)
    test_info = TESTS_CATALOG.get(subj, {}).get(variant)
    if not test_info:
        await q.answer("Тест не найден", show_alert=True)
        return
    # Init test state
    await state.set_state(TestState.in_test)
    await state.update_data(
        subj=subj,
        variant=variant,
        title=test_info["title"],
        questions=test_info["questions"],
        current_idx=0,
        answers={},        # idx -> answer (list for A_multi, str for B)
        selected=[],       # temp selected for A_multi current question
        skipped=[],        # indices of skipped questions
    )
    cnt = len(test_info["questions"])
    await safe_edit(q,
        f"🚀 *{test_info['title']}*\n\n"
        f"📊 Заданий: {cnt}\n"
        f"⏱ Рекомендуемое время: {cnt * 3} мин\n\n"
        "Навигация:\n"
        "✅ *Ответить* — выбери варианты и нажми «Подтвердить»\n"
        "⏭ *Пропустить* — вернёшься позже\n"
        "📖 *Теория* — изучи тему, потом вернись к тесту\n\n"
        "Удачи! 🍀",
        build_start_kb(subj, variant)
    )

def build_start_kb(subj, variant):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать тест", callback_data="test_next")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=f"subj_{subj}")],
    ])

async def show_question(target, state: FSMContext, edit=True):
    """Render current question"""
    data = await state.get_data()
    questions = data["questions"]
    idx = data["current_idx"]
    selected = data.get("selected", [])
    answers = data.get("answers", {})
    skipped = data.get("skipped", [])
    subj = data["subj"]

    if idx >= len(questions):
        await finish_test(target, state)
        return

    q = questions[idx]
    q_id = q["id"]
    q_text = q["text"]
    q_type = q["type"]
    total = len(questions)
    answered = len(answers)
    n_skipped = len(skipped)

    # Progress line
    progress = f"*{q_id}* | Задание {idx+1}/{total}"
    if n_skipped:
        progress += f" | ⏭ пропущено: {n_skipped}"
    if str(idx) in answers:
        progress += " | ✏️ отвечено"

    # Build text
    full_text = f"{progress}\n{'─'*30}\n\n{q_text}"

    # Build keyboard
    kb_rows = []

    if q_type == "A_single":
        for i in range(1, 6):
            mark = "✅ " if i in selected else ""
            kb_rows.append([InlineKeyboardButton(
                text=f"{mark}{i}", callback_data=f"test_sel_{i}"
            )])
        kb_rows = [kb_rows[0:3], kb_rows[3:5]]  # 3+2 layout
        # Flat
        flat = []
        row3 = []
        for i, btn in enumerate([
            InlineKeyboardButton(text=f"{'✅ ' if 1 in selected else ''}1", callback_data="test_sel_1"),
            InlineKeyboardButton(text=f"{'✅ ' if 2 in selected else ''}2", callback_data="test_sel_2"),
            InlineKeyboardButton(text=f"{'✅ ' if 3 in selected else ''}3", callback_data="test_sel_3"),
        ]):
            row3.append(btn)
        row2 = [
            InlineKeyboardButton(text=f"{'✅ ' if 4 in selected else ''}4", callback_data="test_sel_4"),
            InlineKeyboardButton(text=f"{'✅ ' if 5 in selected else ''}5", callback_data="test_sel_5"),
        ]
        kb_rows = [row3, row2]

    elif q_type == "A_multi":
        row3 = [
            InlineKeyboardButton(text=f"{'✅' if 1 in selected else '1'}", callback_data="test_sel_1"),
            InlineKeyboardButton(text=f"{'✅' if 2 in selected else '2'}", callback_data="test_sel_2"),
            InlineKeyboardButton(text=f"{'✅' if 3 in selected else '3'}", callback_data="test_sel_3"),
        ]
        row2 = [
            InlineKeyboardButton(text=f"{'✅' if 4 in selected else '4'}", callback_data="test_sel_4"),
            InlineKeyboardButton(text=f"{'✅' if 5 in selected else '5'}", callback_data="test_sel_5"),
        ]
        kb_rows = [row3, row2]
        full_text += "\n\n_Выбери все верные варианты, затем нажми «Подтвердить»_"

    elif q_type in ("B_text", "B_multi", "B_match"):
        full_text += "\n\n✏️ _Напишите ответ в чат_"
        kb_rows = []

    # Action buttons
    confirm_row = []
    if q_type in ("A_single", "A_multi"):
        confirm_row.append(InlineKeyboardButton(
            text="✅ Подтвердить", callback_data="test_confirm"
        ))
    skip_btn = InlineKeyboardButton(text="⏭ Пропустить", callback_data="test_skip")
    confirm_row.append(skip_btn)
    kb_rows.append(confirm_row)

    # Theory button
    theory_key = q.get("theory_key")
    theory_hint = q.get("theory_hint", "Теория")
    if theory_key:
        kb_rows.append([InlineKeyboardButton(
            text=f"📖 {theory_hint}", callback_data=f"test_theory_{idx}"
        )])

    # Nav: if skipped items exist and we're not at end
    nav_row = []
    if skipped:
        nav_row.append(InlineKeyboardButton(text="📋 Пропущенные", callback_data="test_skipped"))
    if answered > 0:
        nav_row.append(InlineKeyboardButton(text="🏁 Завершить тест", callback_data="test_finish"))
    if nav_row:
        kb_rows.append(nav_row)

    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)

    if edit and hasattr(target, 'message'):
        await safe_edit(target, full_text, kb)
    else:
        msg = target.message if hasattr(target, 'message') else target
        try:
            await msg.edit_text(full_text, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            await msg.answer(full_text, reply_markup=kb, parse_mode="Markdown")

# Navigate to next unanswered question
async def advance_question(state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    current = data["current_idx"]
    answers = data.get("answers", {})
    skipped = data.get("skipped", [])

    # Find next unanswered (not in answers and not skipped)
    for i in range(current + 1, len(questions)):
        if str(i) not in answers and i not in skipped:
            await state.update_data(current_idx=i, selected=[])
            return True
    # Try skipped
    for i in skipped:
        if str(i) not in answers:
            new_skipped = [x for x in skipped if x != i]
            await state.update_data(current_idx=i, selected=[], skipped=new_skipped)
            return True
    # All done
    return False

@dp.callback_query(F.data == "test_next", TestState.in_test)
async def cb_test_next(q: CallbackQuery, state: FSMContext):
    await q.answer()
    await show_question(q, state)

@dp.callback_query(F.data.startswith("test_sel_"), TestState.in_test)
async def cb_test_select(q: CallbackQuery, state: FSMContext):
    """Toggle selection for A questions"""
    num = int(q.data.replace("test_sel_", ""))
    data = await state.get_data()
    selected = list(data.get("selected", []))
    q_type = data["questions"][data["current_idx"]]["type"]

    if q_type == "A_single":
        selected = [num]  # Only one
    else:
        if num in selected:
            selected.remove(num)
        else:
            selected.append(num)
    await state.update_data(selected=selected)
    await q.answer(f"Выбрано: {sorted(selected)}")
    await show_question(q, state)

@dp.callback_query(F.data == "test_confirm", TestState.in_test)
async def cb_test_confirm(q: CallbackQuery, state: FSMContext):
    """Confirm answer for part A"""
    data = await state.get_data()
    selected = data.get("selected", [])
    if not selected:
        await q.answer("⚠️ Выберите хотя бы один вариант!", show_alert=True)
        return
    idx = data["current_idx"]
    answers = dict(data.get("answers", {}))
    answers[str(idx)] = sorted(selected)
    await state.update_data(answers=answers, selected=[])

    has_next = await advance_question(state)
    if not has_next:
        await q.answer("✅ Ответ принят! Все вопросы пройдены.")
        await finish_test(q, state)
    else:
        await q.answer("✅ Ответ принят!")
        await show_question(q, state)

@dp.message(TestState.in_test)
async def handle_b_answer(msg: Message, state: FSMContext):
    """Handle typed answer for part B"""
    data = await state.get_data()
    idx = data["current_idx"]
    q = data["questions"][idx]

    if q["type"] not in ("B_text", "B_multi", "B_match"):
        return  # Ignore for A questions

    user_ans = msg.text.strip()
    answers = dict(data.get("answers", {}))
    answers[str(idx)] = user_ans
    await state.update_data(answers=answers, selected=[])

    has_next = await advance_question(state)
    if not has_next:
        # Need to show finish through edit of last bot message
        # Send a message with finish button
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏁 Посмотреть результаты", callback_data="test_finish")]
        ])
        await msg.answer("✅ Ответ принят! Все вопросы пройдены. Нажми кнопку для результатов.", reply_markup=kb)
    else:
        # Send confirmation and show next question
        await msg.answer("✅ Ответ принят!")
        # Send new question message
        await show_question_msg(msg, state)

async def show_question_msg(msg: Message, state: FSMContext):
    """Show question as new message"""
    data = await state.get_data()
    questions = data["questions"]
    idx = data["current_idx"]
    selected = data.get("selected", [])
    answers = data.get("answers", {})
    skipped = data.get("skipped", [])
    subj = data["subj"]

    q = questions[idx]
    q_type = q["type"]
    total = len(questions)
    answered = len(answers)
    n_skipped = len(skipped)

    progress = f"*{q['id']}* | Задание {idx+1}/{total}"
    if n_skipped:
        progress += f" | ⏭ пропущено: {n_skipped}"

    full_text = f"{progress}\n{'─'*30}\n\n{q['text']}"

    kb_rows = []
    if q_type in ("A_single", "A_multi"):
        row3 = [
            InlineKeyboardButton(text=f"{'✅' if 1 in selected else '1'}", callback_data="test_sel_1"),
            InlineKeyboardButton(text=f"{'✅' if 2 in selected else '2'}", callback_data="test_sel_2"),
            InlineKeyboardButton(text=f"{'✅' if 3 in selected else '3'}", callback_data="test_sel_3"),
        ]
        row2 = [
            InlineKeyboardButton(text=f"{'✅' if 4 in selected else '4'}", callback_data="test_sel_4"),
            InlineKeyboardButton(text=f"{'✅' if 5 in selected else '5'}", callback_data="test_sel_5"),
        ]
        kb_rows = [row3, row2]
        if q_type == "A_multi":
            full_text += "\n\n_Выбери все верные варианты, затем нажми «Подтвердить»_"
        confirm_row = [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="test_confirm"),
            InlineKeyboardButton(text="⏭ Пропустить", callback_data="test_skip"),
        ]
        kb_rows.append(confirm_row)
    else:
        full_text += "\n\n✏️ _Напишите ответ в чат_"
        kb_rows.append([InlineKeyboardButton(text="⏭ Пропустить", callback_data="test_skip")])

    theory_key = q.get("theory_key")
    theory_hint = q.get("theory_hint", "Теория")
    if theory_key:
        kb_rows.append([InlineKeyboardButton(
            text=f"📖 {theory_hint}", callback_data=f"test_theory_{idx}"
        )])

    nav_row = []
    if skipped:
        nav_row.append(InlineKeyboardButton(text="📋 Пропущенные", callback_data="test_skipped"))
    if answered > 0:
        nav_row.append(InlineKeyboardButton(text="🏁 Завершить тест", callback_data="test_finish"))
    if nav_row:
        kb_rows.append(nav_row)

    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)
    await msg.answer(full_text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "test_skip", TestState.in_test)
async def cb_test_skip(q: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx = data["current_idx"]
    skipped = list(data.get("skipped", []))
    if idx not in skipped:
        skipped.append(idx)
    await state.update_data(skipped=skipped, selected=[])

    has_next = await advance_question(state)
    if not has_next:
        await q.answer("Все вопросы пропущены или отвечены")
        await finish_test(q, state)
    else:
        await q.answer("⏭ Пропущено, продолжаем...")
        await show_question(q, state)

@dp.callback_query(F.data == "test_skipped", TestState.in_test)
async def cb_test_skipped_list(q: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    skipped = data.get("skipped", [])
    answers = data.get("answers", {})

    # Unanswered skipped
    unanswered_skipped = [i for i in skipped if str(i) not in answers]
    if not unanswered_skipped:
        await q.answer("Нет пропущенных вопросов!", show_alert=True)
        return

    buttons = []
    for i in unanswered_skipped:
        q_id = questions[i]["id"]
        buttons.append([InlineKeyboardButton(
            text=f"📝 {q_id}", callback_data=f"test_goto_{i}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="test_next")])
    await safe_edit(q, f"📋 *Пропущенные задания ({len(unanswered_skipped)}):*",
                    InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("test_goto_"), TestState.in_test)
async def cb_test_goto(q: CallbackQuery, state: FSMContext):
    idx = int(q.data.replace("test_goto_", ""))
    data = await state.get_data()
    skipped = list(data.get("skipped", []))
    if idx in skipped:
        skipped.remove(idx)
    await state.update_data(current_idx=idx, selected=[], skipped=skipped)
    await q.answer()
    await show_question(q, state)

# ─── Theory from test ─────────────────────────────────────────
@dp.callback_query(F.data.startswith("test_theory_"), TestState.in_test)
async def cb_test_theory(q: CallbackQuery, state: FSMContext):
    idx = int(q.data.replace("test_theory_", ""))
    data = await state.get_data()
    subj = data["subj"]
    questions = data["questions"]
    question = questions[idx]
    theory_key = question.get("theory_key")

    theory = THEORY_MAP.get(subj, {}).get(theory_key)
    if not theory:
        await q.answer("Теория не найдена", show_alert=True)
        return

    # Save return point
    await state.update_data(theory_return_idx=idx, current_idx=idx)

    # Return button goes back to that exact question
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"▶️ Вернуться к {question['id']}",
            callback_data=f"test_return_{idx}"
        )],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")],
    ])
    await safe_edit(q, theory, kb)

@dp.callback_query(F.data.startswith("test_return_"), TestState.in_test)
async def cb_test_return(q: CallbackQuery, state: FSMContext):
    idx = int(q.data.replace("test_return_", ""))
    await state.update_data(current_idx=idx, selected=[])
    await q.answer()
    await show_question(q, state)

# ─── Finish test ──────────────────────────────────────────────
@dp.callback_query(F.data == "test_finish", TestState.in_test)
async def cb_test_finish(q: CallbackQuery, state: FSMContext):
    await q.answer()
    await finish_test(q, state)

async def finish_test(target, state: FSMContext):
    data = await state.get_data()
    questions = data["questions"]
    answers = data.get("answers", {})
    subj = data["subj"]
    variant = data["variant"]
    title = data["title"]

    # Calculate score
    primary = 0
    results_lines = []

    for i, q in enumerate(questions):
        user_ans = answers.get(str(i))
        correct = q["answer"]
        q_id = q["id"]
        q_type = q["type"]
        pts = q.get("points", 2)
        partial = q.get("partial", False)

        earned = 0
        status = "⬜️"

        if user_ans is None:
            status = "⬜️"
            earned = 0
        elif q_type in ("A_single", "A_multi"):
            user_set = set(user_ans) if isinstance(user_ans, list) else set()
            correct_set = set(correct)
            if user_set == correct_set:
                earned = pts
                status = "✅"
            elif partial and user_set.issubset(correct_set) and len(user_set) > 0:
                earned = max(0, pts - 1)
                status = "🔶"
            else:
                earned = 0
                status = "❌"
        elif q_type in ("B_text", "B_multi", "B_match"):
            # Case-insensitive comparison, strip spaces
            ua = str(user_ans).strip().lower().replace(" ", "")
            ca = str(correct).strip().lower().replace(" ", "")
            if ua == ca:
                earned = pts
                status = "✅"
            else:
                earned = 0
                status = "❌"

        primary += earned
        correct_str = str(correct) if isinstance(correct, str) else str(sorted(correct))
        results_lines.append(
            f"{status} *{q_id}*: {earned}/{pts}п. (верно: {correct_str})"
        )

    test_score = primary_to_test(subj, primary)
    max_primary = SUBJECTS[subj]["max_primary"]
    grade = get_grade(test_score)

    # Save to DB
    user_id = None
    if hasattr(target, 'from_user'):
        user_id = target.from_user.id
    elif hasattr(target, 'message') and target.message:
        user_id = target.from_user.id
    if user_id:
        await save_test_result(user_id, subj, variant, primary, test_score, max_primary)

    header = (
        f"🏁 *Результаты: {title}*\n\n"
        f"▪️ Первичный балл: *{primary}* из {max_primary}\n"
        f"▪️ Тестовый балл: *{test_score}* из 100\n"
        f"▪️ Оценка: {grade}\n\n"
    )

    # Split results into chunks (Telegram limit)
    chunk = header
    messages = []
    for line in results_lines:
        if len(chunk) + len(line) > 3500:
            messages.append(chunk)
            chunk = ""
        chunk += line + "\n"
    messages.append(chunk)

    await state.clear()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Пройти ещё", callback_data=f"subj_{subj}")],
        [InlineKeyboardButton(text="📖 Изучить теорию", callback_data=f"theory_{subj}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")],
    ])

    msg_obj = target.message if hasattr(target, 'message') else target
    for i, m in enumerate(messages):
        if i == len(messages) - 1:
            try:
                await msg_obj.edit_text(m, reply_markup=kb, parse_mode="Markdown")
            except Exception:
                await msg_obj.answer(m, reply_markup=kb, parse_mode="Markdown")
        else:
            try:
                await msg_obj.edit_text(m, parse_mode="Markdown")
            except Exception:
                await msg_obj.answer(m, parse_mode="Markdown")

# ══════════════════════════════════════════════════════════════
# ТЕОРИЯ
# ══════════════════════════════════════════════════════════════
@dp.callback_query(F.data.startswith("theory_"))
async def cb_theory_menu(q: CallbackQuery):
    subj = q.data.replace("theory_", "")
    if subj not in CATS_MAP:
        return
    cats = CATS_MAP[subj]
    name = subj_name(subj)
    await safe_edit(q, f"📖 *Теория — {name}*\n\nВыберите раздел:",
                    theory_categories_kb(subj, cats))

@dp.callback_query(F.data.startswith("tcat_"))
async def cb_theory_cat(q: CallbackQuery):
    parts = q.data.split("_", 2)
    subj = parts[1]
    cat_name_short = parts[2]
    cats = CATS_MAP.get(subj, {})

    # Find full cat name
    full_cat = None
    for cat in cats:
        if cat[:30] == cat_name_short:
            full_cat = cat
            break
    if not full_cat:
        await q.answer("Раздел не найден", show_alert=True)
        return

    topics = cats[full_cat]
    await safe_edit(q, f"📚 *{full_cat}*\n\nВыберите тему:",
                    theory_topics_kb(subj, full_cat, topics))

@dp.callback_query(F.data.startswith("topic_"))
async def cb_theory_topic(q: CallbackQuery):
    parts = q.data.split("_", 2)
    subj = parts[1]
    key = parts[2]

    theory = THEORY_MAP.get(subj, {}).get(key)
    if not theory:
        await q.answer("Теория не найдена", show_alert=True)
        return

    # Find category for back button
    cats = CATS_MAP.get(subj, {})
    cat_name = "Теория"
    for cname, topics in cats.items():
        for _, tkey in topics:
            if tkey == key:
                cat_name = cname
                break

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"◀️ Назад к разделу", callback_data=f"tcat_{subj}_{cat_name[:30]}")],
        [InlineKeyboardButton(text="📚 Все разделы", callback_data=f"theory_{subj}")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main")],
    ])

    # Split long theory
    if len(theory) > 4000:
        parts_text = [theory[i:i+4000] for i in range(0, len(theory), 4000)]
        try:
            await q.message.edit_text(parts_text[0], reply_markup=None, parse_mode="Markdown")
        except Exception:
            await q.message.answer(parts_text[0], parse_mode="Markdown")
        for part in parts_text[1:-1]:
            await q.message.answer(part, parse_mode="Markdown")
        await q.message.answer(parts_text[-1], reply_markup=kb, parse_mode="Markdown")
    else:
        await safe_edit(q, theory, kb)

# ══════════════════════════════════════════════════════════════
# КАЛЬКУЛЯТОР БАЛЛОВ
# ══════════════════════════════════════════════════════════════
@dp.callback_query(F.data == "calc_menu")
async def cb_calc_menu(q: CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_edit(q, "🧮 *Калькулятор баллов*\n\nВыберите предмет:", calc_subject_kb())

@dp.callback_query(F.data.startswith("calc_"))
async def cb_calc_subject(q: CallbackQuery, state: FSMContext):
    subj = q.data.replace("calc_", "")
    if subj not in SUBJECTS:
        return
    info = SUBJECTS[subj]
    await state.set_state(CalcState.waiting_score)
    await state.update_data(calc_subj=subj)
    await safe_edit(q,
        f"🧮 *{info['name']}*\n\n"
        f"Максимальный первичный балл: *{info['max_primary']}*\n\n"
        f"📝 Формула начисления:\n{info['calc_hint']}\n\n"
        f"Введите ваш первичный балл (от 0 до {info['max_primary']}):",
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Отмена", callback_data="calc_menu")]
        ])
    )

@dp.message(CalcState.waiting_score)
async def handle_calc_score(msg: Message, state: FSMContext):
    data = await state.get_data()
    subj = data.get("calc_subj")
    if not subj:
        await state.clear()
        return
    try:
        score = int(msg.text.strip())
    except ValueError:
        await msg.answer("⚠️ Введите целое число!")
        return
    max_p = SUBJECTS[subj]["max_primary"]
    if score < 0 or score > max_p:
        await msg.answer(f"⚠️ Балл должен быть от 0 до {max_p}")
        return

    result = format_score_result(subj, score)
    await state.clear()
    await msg.answer(result, reply_markup=calc_done_kb(subj))

# ══════════════════════════════════════════════════════════════
# СБОРНИКИ
# ══════════════════════════════════════════════════════════════
@dp.callback_query(F.data == "collections")
async def cb_collections(q: CallbackQuery):
    await safe_edit(q, "📚 *Сборники и ресурсы*\n\nВыберите предмет:", collections_kb())

@dp.callback_query(F.data.startswith("col_"))
async def cb_collection_subject(q: CallbackQuery):
    subj = q.data.replace("col_", "")
    col = COLLECTIONS.get(subj)
    if not col:
        await q.answer("Не найдено", show_alert=True)
        return
    text = f"📚 *{col['name']}*\n\n"
    for title, url in col["links"]:
        text += f"▪️ [{title}]({url})\n"
    await safe_edit(q, text, collections_back_kb())

# ══════════════════════════════════════════════════════════════
# ЛИЧНЫЙ КАБИНЕТ
# ══════════════════════════════════════════════════════════════
@dp.callback_query(F.data == "cabinet")
async def cb_cabinet(q: CallbackQuery):
    user = await get_user(q.from_user.id)
    if not user:
        await q.answer("Пользователь не найден", show_alert=True)
        return
    stats = await get_user_stats(q.from_user.id)
    name = q.from_user.first_name or "Пользователь"
    text = (
        f"👤 *Личный кабинет*\n\n"
        f"Привет, *{name}*!\n\n"
        f"📊 *Статистика:*\n"
        f"▪️ Тестов решено: *{user['tests_done']}*\n"
        f"▪️ Лучший балл: *{user['best_score']}*\n"
        f"▪️ Последний предмет: {user.get('last_subject') or '—'}\n\n"
    )
    if stats:
        text += "📈 *По предметам:*\n"
        for s in stats:
            subj_n = subj_name(s["subject"])
            text += f"▪️ {subj_n}: {s['cnt']} тестов, макс. *{s['best']}* балл\n"
    text += f"\n📅 В боте с: {user.get('joined_at', '—')[:10]}"
    await safe_edit(q, text, cabinet_kb())

@dp.callback_query(F.data == "cabinet_stats")
async def cb_cabinet_stats(q: CallbackQuery):
    await cb_cabinet(q)

# ══════════════════════════════════════════════════════════════
# АДМИН ПАНЕЛЬ
# ══════════════════════════════════════════════════════════════
@dp.callback_query(F.data == "admin_stats")
async def cb_admin_stats(q: CallbackQuery):
    if not is_admin(q.from_user.id):
        return
    cnt = await count_users()
    results = await get_all_results()
    text = f"📊 *Статистика бота*\n\n👥 Пользователей: *{cnt}*\n\n📝 *Тесты:*\n"
    for r in results:
        text += f"▪️ {subj_name(r['subject'])}: {r['cnt']} сдач, средний балл: {r['avg']:.1f}\n"
    await safe_edit(q, text, admin_kb())

@dp.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(q: CallbackQuery, state: FSMContext):
    if not is_admin(q.from_user.id):
        return
    await state.set_state(AdminState.waiting_broadcast)
    await safe_edit(q,
        "📣 *Рассылка*\n\nНапишите сообщение для рассылки всем пользователям.\n"
        "_Поддерживается Markdown форматирование_",
        admin_cancel_kb()
    )

@dp.callback_query(F.data == "admin_cancel_broadcast")
async def cb_admin_cancel(q: CallbackQuery, state: FSMContext):
    if not is_admin(q.from_user.id):
        return
    await state.clear()
    await safe_edit(q, "❌ Рассылка отменена.", admin_kb())

@dp.message(AdminState.waiting_broadcast)
async def handle_broadcast(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    text = msg.text
    user_ids = await get_all_user_ids()
    sent = 0
    failed = 0
    await msg.answer(f"📤 Начинаю рассылку {len(user_ids)} пользователям...")
    for uid in user_ids:
        try:
            await bot.send_message(uid, text, parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await msg.answer(
        f"✅ *Рассылка завершена*\n\n"
        f"✅ Отправлено: {sent}\n❌ Не доставлено: {failed}",
        reply_markup=admin_kb()
    )

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
async def main():
    await init_db()
    logger.info("Database initialized")

    if config.WEBHOOK_URL:
        from aiohttp import web
        from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

        webhook_path = "/webhook"
        webhook_url = f"{config.WEBHOOK_URL}{webhook_path}"
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook set: {webhook_url}")

        app = web.Application()
        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=webhook_path)
        setup_application(app, dp, bot=bot)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", config.PORT)
        await site.start()
        logger.info(f"Server started on port {config.PORT}")
        await asyncio.Event().wait()
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Starting polling...")
        await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
