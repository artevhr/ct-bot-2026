from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ── Главное меню ──────────────────────────────────────────────────────────────
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Предметы", callback_data="subjects")],
        [
            InlineKeyboardButton(text="🧮 Калькулятор баллов", callback_data="calc_menu"),
            InlineKeyboardButton(text="📖 Сборники", callback_data="collections"),
        ],
        [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="cabinet")],
    ])

def back_to_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
    ])

# ── Предметы ─────────────────────────────────────────────────────────────────
def subjects_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Русский язык", callback_data="subj_russian")],
        [InlineKeyboardButton(text="📐 Математика",   callback_data="subj_math")],
        [InlineKeyboardButton(text="🇬🇧 Английский язык", callback_data="subj_english")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main")],
    ])

def subject_menu_kb(subj: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 РТ 2026 года",    callback_data=f"rt2026_{subj}")],
        [InlineKeyboardButton(text="📂 РТ прошлых лет",  callback_data=f"rtpast_{subj}")],
        [InlineKeyboardButton(text="📖 Теория",          callback_data=f"theory_{subj}")],
        [InlineKeyboardButton(text="✏️ Доп. задания",    callback_data=f"extra_{subj}")],
        [InlineKeyboardButton(text="🧮 Рассчитать балл", callback_data=f"calc_{subj}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="subjects")],
    ])

# ── Тесты — выбор варианта ───────────────────────────────────────────────────
def tests_list_kb(subj: str, tests: dict, back_cb: str, label_prefix=""):
    buttons = []
    for key, info in tests.items():
        buttons.append([InlineKeyboardButton(
            text=f"📄 {info['title']}",
            callback_data=f"starttest_{subj}_{key}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def past_years_kb(subj: str, years_by_group: dict):
    """Кнопки по годам для РТ прошлых лет"""
    buttons = []
    for year in sorted(years_by_group.keys(), reverse=True):
        buttons.append([InlineKeyboardButton(
            text=f"📅 {year}",
            callback_data=f"rtyear_{subj}_{year}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"subj_{subj}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def year_variants_kb(subj: str, year: str, variants: list):
    buttons = []
    for key, title in variants:
        buttons.append([InlineKeyboardButton(
            text=f"📄 {title}",
            callback_data=f"starttest_{subj}_{key}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ К годам", callback_data=f"rtpast_{subj}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ── Тест — вопрос ─────────────────────────────────────────────────────────────
def question_a_multi_kb(selected: list, idx: int, total: int,
                        theory_key: str, theory_hint: str,
                        has_skipped: bool, answers_count: int):
    """Клавиатура для заданий типа A (выбор варианта)"""
    # Кнопки 1-5
    row1 = [
        InlineKeyboardButton(
            text=f"{'✅' if n in selected else str(n)}",
            callback_data=f"qsel_{n}"
        ) for n in range(1, 4)
    ]
    row2 = [
        InlineKeyboardButton(
            text=f"{'✅' if n in selected else str(n)}",
            callback_data=f"qsel_{n}"
        ) for n in range(4, 6)
    ]
    # Управление
    ctrl_row = [
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="qconfirm"),
        InlineKeyboardButton(text="⏭ Пропустить",  callback_data="qskip"),
    ]
    # Теория
    theory_row = [
        InlineKeyboardButton(
            text=f"📖 {theory_hint}",
            callback_data=f"qtheory_{idx}"
        )
    ]
    # Навигация
    nav_row = []
    if has_skipped:
        nav_row.append(InlineKeyboardButton(text="📋 Пропущенные", callback_data="qskipped"))
    if answers_count > 0:
        nav_row.append(InlineKeyboardButton(text="🏁 Завершить", callback_data="qfinish"))

    rows = [row1, row2, ctrl_row, theory_row]
    if nav_row:
        rows.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

def question_b_kb(idx: int, theory_hint: str, has_skipped: bool, answers_count: int):
    """Клавиатура для заданий части B (ввод текстом)"""
    rows = [
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="qskip")],
        [InlineKeyboardButton(text=f"📖 {theory_hint}", callback_data=f"qtheory_{idx}")],
    ]
    nav_row = []
    if has_skipped:
        nav_row.append(InlineKeyboardButton(text="📋 Пропущенные", callback_data="qskipped"))
    if answers_count > 0:
        nav_row.append(InlineKeyboardButton(text="🏁 Завершить", callback_data="qfinish"))
    if nav_row:
        rows.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

def skipped_list_kb(questions: list, skipped_idxs: list):
    buttons = []
    for i in skipped_idxs:
        if i < len(questions):
            q = questions[i]
            buttons.append([InlineKeyboardButton(
                text=f"📝 {q['id']}",
                callback_data=f"qgoto_{i}"
            )])
    buttons.append([InlineKeyboardButton(text="◀️ Продолжить", callback_data="qnext")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def theory_from_test_kb(q_id: str, idx: int):
    """Возврат к тесту из теории"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"▶️ Вернуться к заданию {q_id}",
            callback_data=f"qreturn_{idx}"
        )],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")],
    ])

def test_result_kb(subj: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Пройти ещё тест", callback_data=f"subj_{subj}")],
        [InlineKeyboardButton(text="📖 Изучить теорию",  callback_data=f"theory_{subj}")],
        [InlineKeyboardButton(text="🏠 Главное меню",    callback_data="main")],
    ])

def start_test_kb(subj: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать тест", callback_data="qnext")],
        [InlineKeyboardButton(text="◀️ Назад",       callback_data=f"subj_{subj}")],
    ])

# ── Теория ──────────────────────────────────────────────────────────────────
def theory_cats_kb(subj: str, cats: dict):
    buttons = []
    for cat_name in cats:
        buttons.append([InlineKeyboardButton(
            text=cat_name,
            callback_data=f"tcat_{subj}_{cat_name[:28]}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"subj_{subj}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def theory_topics_kb(subj: str, cat_short: str, topics: list):
    buttons = []
    for title, key in topics:
        buttons.append([InlineKeyboardButton(
            text=title,
            callback_data=f"topic_{subj}_{key}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"theory_{subj}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def topic_back_kb(subj: str, cat_short: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ К разделу", callback_data=f"tcat_{subj}_{cat_short[:28]}")],
        [InlineKeyboardButton(text="📚 Все разделы", callback_data=f"theory_{subj}")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main")],
    ])

# ── Доп. задания ─────────────────────────────────────────────────────────────
def extra_list_kb(subj: str, items: list):
    buttons = []
    for title, key in items:
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"extra_{subj}_{key}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"subj_{subj}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def extra_back_kb(subj: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ К доп. заданиям", callback_data=f"extra_{subj}")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="main")],
    ])

# ── Калькулятор ──────────────────────────────────────────────────────────────
def calc_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Русский язык",    callback_data="calc_russian")],
        [InlineKeyboardButton(text="📐 Математика",      callback_data="calc_math")],
        [InlineKeyboardButton(text="🇬🇧 Английский",    callback_data="calc_english")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main")],
    ])

def calc_done_kb(subj: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Ещё раз",     callback_data=f"calc_{subj}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")],
    ])

# ── Сборники ─────────────────────────────────────────────────────────────────
def collections_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Русский язык",  callback_data="col_russian")],
        [InlineKeyboardButton(text="📐 Математика",    callback_data="col_math")],
        [InlineKeyboardButton(text="🇬🇧 Английский",  callback_data="col_english")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main")],
    ])

def collection_files_kb(subj: str, files: list):
    buttons = []
    for i, f in enumerate(files):
        buttons.append([InlineKeyboardButton(
            text=f["title"],
            callback_data=f"sendbook_{subj}_{i}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="collections")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ── Личный кабинет ──────────────────────────────────────────────────────────
def cabinet_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Подробная статистика", callback_data="cab_stats")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")],
    ])

# ── Админ ────────────────────────────────────────────────────────────────────
def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика",   callback_data="adm_stats")],
        [InlineKeyboardButton(text="📣 Рассылка",     callback_data="adm_broadcast")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main")],
    ])

def admin_cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить рассылку", callback_data="adm_cancel")]
    ])
