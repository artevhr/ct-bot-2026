from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ─── Главное меню ─────────────────────────────────────────
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Предметы", callback_data="subjects")],
        [InlineKeyboardButton(text="🧮 Калькулятор баллов", callback_data="calc_menu"),
         InlineKeyboardButton(text="📖 Сборники", callback_data="collections")],
        [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="cabinet")],
    ])

def main_menu_btn():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
    ])

# ─── Предметы ─────────────────────────────────────────────
def subjects_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Русский язык", callback_data="subj_russian")],
        [InlineKeyboardButton(text="📐 Математика", callback_data="subj_math")],
        [InlineKeyboardButton(text="🇬🇧 Английский язык", callback_data="subj_english")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main")],
    ])

def subject_menu_kb(subj: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Пройти РТ 2026", callback_data=f"rt_{subj}_2026")],
        [InlineKeyboardButton(text="📂 РТ прошлых лет", callback_data=f"rt_{subj}_past")],
        [InlineKeyboardButton(text="📖 Теория", callback_data=f"theory_{subj}")],
        [InlineKeyboardButton(text="🧮 Рассчитать балл", callback_data=f"calc_{subj}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="subjects")],
    ])

# ─── РТ ───────────────────────────────────────────────────
def rt_2026_kb(subj: str, variants: list):
    buttons = []
    for key in variants:
        buttons.append([InlineKeyboardButton(text=f"📄 {key}", callback_data=f"rtfile_{subj}_2026_{key}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"subj_{subj}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def rt_past_years_kb(subj: str, years: list):
    buttons = []
    row = []
    for i, y in enumerate(years):
        row.append(InlineKeyboardButton(text=y, callback_data=f"rtyear_{subj}_{y}"))
        if len(row) == 3 or i == len(years) - 1:
            buttons.append(row)
            row = []
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"subj_{subj}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def rt_year_files_kb(subj: str, year: str, files: list):
    buttons = []
    for f in files:
        import os
        name = os.path.basename(f).replace(".pdf", "")
        buttons.append([InlineKeyboardButton(text=f"📄 {name}", callback_data=f"rtf_{subj}_{year}_{name[:30]}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"rt_{subj}_past")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ─── Теория ──────────────────────────────────────────────
def theory_categories_kb(subj: str, categories: dict):
    buttons = []
    for cat_name in categories:
        buttons.append([InlineKeyboardButton(text=cat_name, callback_data=f"tcat_{subj}_{cat_name[:30]}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"subj_{subj}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def theory_topics_kb(subj: str, cat_name: str, topics: list):
    buttons = []
    for title, key in topics:
        buttons.append([InlineKeyboardButton(text=title, callback_data=f"topic_{subj}_{key}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"theory_{subj}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def theory_back_kb(subj: str, cat_name: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к теме", callback_data=f"tcat_{subj}_{cat_name[:30]}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")],
    ])

def theory_back_from_rt_kb(subj: str, return_cb: str):
    """Кнопка возврата к выполнению теста из теории"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Продолжить тест", callback_data=return_cb)],
        [InlineKeyboardButton(text="📖 Теория", callback_data=f"theory_{subj}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")],
    ])

# ─── Калькулятор ─────────────────────────────────────────
def calc_subject_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Русский язык", callback_data="calc_russian")],
        [InlineKeyboardButton(text="📐 Математика", callback_data="calc_math")],
        [InlineKeyboardButton(text="🇬🇧 Английский язык", callback_data="calc_english")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main")],
    ])

def calc_done_kb(subj: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Ещё раз", callback_data=f"calc_{subj}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")],
    ])

# ─── Сборники ─────────────────────────────────────────────
def collections_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Русский язык", callback_data="col_russian")],
        [InlineKeyboardButton(text="📐 Математика", callback_data="col_math")],
        [InlineKeyboardButton(text="🇬🇧 Английский язык", callback_data="col_english")],
        [InlineKeyboardButton(text="🏛 Общие ресурсы", callback_data="col_general")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main")],
    ])

def collections_back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к сборникам", callback_data="collections")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")],
    ])

# ─── Личный кабинет ───────────────────────────────────────
def cabinet_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Моя статистика", callback_data="cabinet_stats")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main")],
    ])

# ─── Админ панель ─────────────────────────────────────────
def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📣 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main")],
    ])

def admin_cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="admin_cancel_broadcast")]
    ])
