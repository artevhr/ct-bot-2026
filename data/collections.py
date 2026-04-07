# -*- coding: utf-8 -*-
# Сборники и файлы для отправки пользователям
# PDF файлы должны лежать в папке media/books/

import os

BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media", "books")

# Список сборников по предметам — файлы для отправки ботом
BOOKS = {
    "russian": {
        "name": "📝 Русский язык — сборники",
        "files": [
            {
                "title": "📗 ЦТ за 60 уроков (Бычковская и др.)",
                "filename": "rus_60_urokov.pdf",
                "desc": "Полный курс подготовки — орфография, пунктуация, лексика, синтаксис. 445 стр."
            },
            {
                "title": "📘 Русский язык в таблицах и тестах (Ткачёва)",
                "filename": "rus_tablicy.pdf",
                "desc": "Систематизация правил по всем разделам. 576 стр."
            },
            {
                "title": "📙 Лисовская — узелки на память",
                "filename": "rus_lisovskaya.pdf",
                "desc": "Краткие правила-памятки для быстрого повторения"
            },
            {
                "title": "📕 ЦТ/ЦЭ Русский 2025 (сборник)",
                "filename": "rus_ct2025.pdf",
                "desc": "Актуальные задания ЦТ и ЦЭ с ответами"
            },
        ]
    },
    "english": {
        "name": "🇬🇧 Английский язык — сборники",
        "files": [
            {
                "title": "📗 On the Way to Success (Карневская)",
                "filename": "eng_karnevskaya.pdf",
                "desc": "Лексико-грамматический курс подготовки к ЦТ. 288 стр."
            },
            {
                "title": "📘 Progress Tests (сборник тестов)",
                "filename": "eng_progress_tests.pdf",
                "desc": "Сборник тематических тестов по английскому"
            },
            {
                "title": "📙 Полный курс подготовки (Митрошкина)",
                "filename": "eng_mitroshkina.pdf",
                "desc": "Комплексная подготовка к ЦТ по английскому"
            },
            {
                "title": "📕 Тренажёр (Точилина)",
                "filename": "eng_tochilina.pdf",
                "desc": "Тренировочные задания по грамматике и лексике"
            },
        ]
    },
    "math": {
        "name": "📐 Математика — сборники",
        "files": [
            {
                "title": "📗 ЦТ за 60 уроков (Барвенов, Бахтина)",
                "filename": "math_60_urokov.pdf",
                "desc": "22 темы по всему курсу математики, 3220 задач. 305 стр."
            },
            {
                "title": "📘 Теория. Примеры. Тесты (Ларченко)",
                "filename": "math_larchenko.pdf",
                "desc": "Полный теоретический курс + задачи. 671 стр."
            },
            {
                "title": "📙 Шпора по стереометрии",
                "filename": "math_stereom_shpora.pdf",
                "desc": "Краткая шпаргалка по всем формулам стереометрии"
            },
            {
                "title": "📕 Отработка функций",
                "filename": "math_functions.pdf",
                "desc": "Задачи на исследование функций"
            },
            {
                "title": "📗 ДРТ 2015–2024 (демонстрационные варианты)",
                "filename": "math_drt_2015_2024.pdf",
                "desc": "Официальные демонстрационные варианты ЦТ"
            },
        ]
    },
}

# Оригинальные пути к файлам (для копирования в media/books при деплое)
ORIGINAL_PATHS = {
    "rus_60_urokov.pdf": "/home/claude/new_files/РУССКИЙ_СБОРНИКИ/РУССКИЙ СБОРНИКИ/60_уроков.pdf",
    "rus_tablicy.pdf": "/home/claude/new_files/РУССКИЙ_СБОРНИКИ/РУССКИЙ СБОРНИКИ/Русский_язык_в_таблицах_и_тестах_by_Ткачева,_Т_Л_z_lib_org.pdf",
    "rus_lisovskaya.pdf": "/home/claude/new_files/РУССКИЙ_СБОРНИКИ/РУССКИЙ СБОРНИКИ/Лисовская узелки на памятьi.pdf",
    "rus_ct2025.pdf": "/home/claude/new_files/РУССКИЙ_ДОП_ЗАДАНИЯ/РУССКИЙ ДОП ЗАДАНИЯ/ЦТЦЭ РУССКИЙ 2025.pdf",
    "eng_karnevskaya.pdf": "/home/claude/new_files/СБОРНИКИ_АНГЛИЙСКИЙ__ТЕОРИЯ_И_ТП_/СБОРНИКИ (ТЕОРИЯ И ТП)/On the way to success Карневская.pdf",
    "eng_progress_tests.pdf": "/home/claude/new_files/СБОРНИКИ_АНГЛИЙСКИЙ__ТЕОРИЯ_И_ТП_/СБОРНИКИ (ТЕОРИЯ И ТП)/progress tests.pdf",
    "eng_mitroshkina.pdf": "/home/claude/new_files/СБОРНИКИ_АНГЛИЙСКИЙ__ТЕОРИЯ_И_ТП_/СБОРНИКИ (ТЕОРИЯ И ТП)/Полный курс подготовки к ЦТ Митрошкина.pdf",
    "eng_tochilina.pdf": "/home/claude/new_files/СБОРНИКИ_АНГЛИЙСКИЙ__ТЕОРИЯ_И_ТП_/СБОРНИКИ (ТЕОРИЯ И ТП)/Тренажер Точилина.pdf",
    "math_60_urokov.pdf": "/home/claude/new_files/МАТЕМАТИКА__СБОРНИКИ__ШПОРЫ_И_ПРИМЕРЫ_РЕШЕНИЙ_/МАТЕМАТИКА (СБОРНИКИ, ШПОРЫ И ПРИМЕРЫ РЕШЕНИЙ)/60 уроков.pdf",
    "math_larchenko.pdf": "/home/claude/new_files/МАТЕМАТИКА__СБОРНИКИ__ШПОРЫ_И_ПРИМЕРЫ_РЕШЕНИЙ_/МАТЕМАТИКА (СБОРНИКИ, ШПОРЫ И ПРИМЕРЫ РЕШЕНИЙ)/Ларченко_2021.pdf",
    "math_stereom_shpora.pdf": "/home/claude/new_files/МАТЕМАТИКА__СБОРНИКИ__ШПОРЫ_И_ПРИМЕРЫ_РЕШЕНИЙ_/МАТЕМАТИКА (СБОРНИКИ, ШПОРЫ И ПРИМЕРЫ РЕШЕНИЙ)/ШПОРА по СТЕОМЕ.pdf",
    "math_functions.pdf": "/home/claude/new_files/МАТЕМАТИКА__СБОРНИКИ__ШПОРЫ_И_ПРИМЕРЫ_РЕШЕНИЙ_/МАТЕМАТИКА (СБОРНИКИ, ШПОРЫ И ПРИМЕРЫ РЕШЕНИЙ)/Отработка функций.pdf",
    "math_drt_2015_2024.pdf": "/home/claude/new_files/МАТЕМАТИКА__СБОРНИКИ__ШПОРЫ_И_ПРИМЕРЫ_РЕШЕНИЙ_/МАТЕМАТИКА (СБОРНИКИ, ШПОРЫ И ПРИМЕРЫ РЕШЕНИЙ)/ДРТ 2015-2023.pdf",
}

def get_book_path(filename: str) -> str:
    """Возвращает путь к файлу сборника"""
    # Сначала пробуем из media/books
    local = os.path.join(BASE, filename)
    if os.path.exists(local):
        return local
    # Потом из оригинального расположения
    orig = ORIGINAL_PATHS.get(filename)
    if orig and os.path.exists(orig):
        return orig
    return None

def prepare_books():
    """Копирует книги в папку media/books (вызывать при старте)"""
    import shutil
    os.makedirs(BASE, exist_ok=True)
    copied = 0
    for fname, src in ORIGINAL_PATHS.items():
        dst = os.path.join(BASE, fname)
        if not os.path.exists(dst) and os.path.exists(src):
            try:
                shutil.copy2(src, dst)
                copied += 1
            except Exception as e:
                pass
    return copied
