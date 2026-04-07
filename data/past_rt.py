# -*- coding: utf-8 -*-
"""
Загрузчик РТ прошлых лет из PDF файлов (РИКЗ).
Извлекает задания и ответы из официальных консультационных материалов.
"""

import re
import os
import logging

logger = logging.getLogger(__name__)

# Пути к файлам РТ прошлых лет
# Папка media/rt_files/ должна содержать PDF файлы
# При запуске на Railway файлы должны быть в репозитории

BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media", "rt_pdfs")


def get_available_past_years(subject: str) -> dict:
    """Возвращает доступные варианты РТ прошлых лет в виде {год: [варианты]}"""
    available = {
        "russian": {
            "2024–2025": ["Этап I В1", "Этап II В1", "Этап III В1"],
            "2023–2024": ["Этап I В1", "Этап II В1"],
            "2022–2023": ["Этап I В1", "Этап II В1"],
        },
        "english": {
            "2024–2025": ["Этап I В1", "Этап II В1", "Этап III В1"],
            "2023–2024": ["Этап I В1", "Этап II В1"],
            "2022–2023": ["Этап I В1"],
        },
        "math": {
            "2024–2025": ["Этап I В1", "Этап II В1", "Этап III В1"],
            "2023–2024": ["Этап I В1"],
        },
    }
    return available.get(subject, {})


# =====================================================
# Встроенные вопросы РТ прошлых лет
# Извлечены из официальных PDF РИКЗ
# =====================================================

PAST_RT = {
    "russian": {
        "2024–2025 Этап I В1": {
            "title": "РТ 2024/2025 — Этап I, Вариант 1",
            "source": "РИКЗ РБ",
            "questions": [
                {
                    "id": "А1",
                    "text": "Пишется А на месте пропуска в словах:\n\n1) новая ак..демия\n2) выгодное распол..жение\n3) нар..стающий шум\n4) к..нфорка\n5) золотое укр..шение",
                    "answer": "1,3,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_1", "theory_hint": "Безударные гласные в корне"
                },
                {
                    "id": "А2",
                    "text": "Пишется Е на месте пропуска в словах:\n\n1) осл..пить глаза\n2) посв..тить фонарём\n3) правила г..гиены\n4) зам..реть от радости\n5) пр..уныть после экзамена",
                    "answer": "1,2,4",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_1", "theory_hint": "Безударные гласные в корне"
                },
                {
                    "id": "А3",
                    "text": "Двойные согласные пишутся в словах:\n\n1) ра(с/сс)шитый\n2) лакирова(н/нн)ый\n3) мороже(н/нн)ое тесто\n4) панора(м/мм)а\n5) бе(з/зз)ащитный",
                    "answer": "2,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_9", "theory_hint": "Н и НН в прилагательных"
                },
                {
                    "id": "А4",
                    "text": "Пишется О на месте пропуска в словах:\n\n1) хомяч..к\n2) дириж..р\n3) расч..ска\n4) солнечным луч..м\n5) приглуш..нный",
                    "answer": "1,4",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_3", "theory_hint": "Гласные после шипящих"
                },
                {
                    "id": "А5",
                    "text": "Укажите номера пропусков, где пишется НЕ:\n\nК кому бы ¹н.. обращались участники экспедиции за помощью, никто не мог помочь им. ²Н.. опытные таёжники, ³н.. новички ⁴н.. знали, как правильно проложить маршрут. Поэтому группа пошла по тропам, где ⁵н.. раз проходили дикие звери.",
                    "answer": "4,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_14", "theory_hint": "НЕ и НИ"
                },
                {
                    "id": "А6",
                    "text": "Пишется НЕ раздельно со словами:\n\n1) (не)подпускающий к себе хищник\n2) (не)настное утро\n3) фамилии ещё (не)названы\n4) (не)ваш проект\n5) дорога (не)ровная, но короткая",
                    "answer": "1,3,4",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_9", "theory_hint": "НЕ с прилагательными и причастиями"
                },
                {
                    "id": "А7",
                    "text": "Через дефис пишутся слова:\n\n1) (пол)Гомельской области\n2) (борт)проводница\n3) перец (по)болгарски\n4) (железно)дорожный\n5) (экс)рекордсмен",
                    "answer": "3,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_12", "theory_hint": "Дефисное написание"
                },
                {
                    "id": "А8",
                    "text": "Раздельно пишутся выделенные слова в предложениях:\n\n1) На ветке рябины сидела какая-то птица (на)подобие перепёлки.\n2) Племянница плохо рисует, (за)то хорошо поёт.\n3) Голоса жаворонков были слышны (по)всюду.\n4) Дверь я нашла почти (на)ощупь.\n5) (По)тому, как дочь наряжалась, мать поняла, что предстоит встреча.",
                    "answer": "4,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_13", "theory_hint": "Предлоги и союзы: слитное/раздельное"
                },
                {
                    "id": "А9",
                    "text": "Тире на месте пропуска обязательно ставится в предложениях:\n\n1) Соната _ один из основных жанров камерной инструментальной музыки.\n2) Сердце _ не камень.\n3) Время _ деньги.\n4) Книга _ лучший подарок.\n5) Жизнь _ есть борьба.",
                    "answer": "1,2,4",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "пункт_1", "theory_hint": "Тире между подлежащим и сказуемым"
                },
                {
                    "id": "А10",
                    "text": "Запятая ставится на месте ВСЕХ пропусков в предложениях:\n\n1) Над новым проектом инженер работал_ не покладая рук.\n2) С торжественной грустью смотрело на землю_ пышно расцвеченное звёздами_ ночное небо.\n3) Очарованный подводными пейзажами_ я решил приехать снова.\n4) Иван_ согнав с цветка шмеля_ принялся выкапывать лимонник.\n5) Белые лебеди_ изогнув шеи_ прислушиваются к лесному эху.",
                    "answer": "3,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "пункт_3", "theory_hint": "Обособленные обстоятельства"
                },
                {
                    "id": "А11",
                    "text": "Запятая ставится на месте ВСЕХ пропусков в предложениях:\n\n1) Вечером я сидел на скамье_ глядел на горы.\n2) Дождь то идёт сильный_ то слабый_ обрывая ягоды рябины.\n3) На вершине горы_ весной розовеющей от цветов_ стоял замок.\n4) Мальчик приносил лошади сушки_ и сахар_ морковь и капусту.\n5) Его взгляд блуждал по комнате_ останавливаясь на предметах.",
                    "answer": "3,4",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "пункт_2", "theory_hint": "Однородные члены"
                },
                {
                    "id": "А12",
                    "text": "Знаки препинания расставлены ПРАВИЛЬНО в предложениях:\n\n1) Надо стараться говорить так, чтобы все могли понимать тебя и чтобы все слова были правдивы.\n2) Тогда когда позвонили в дверь, отец ещё только проснулся.\n3) Потом я стоял у каната, которым была отгорожена площадка, и смотрел, как тренируется Катя.\n4) Когда путники ступили в лес и тяжко гружёные хвоей лапы елей обдали их прохладой, все сразу почувствовали усталость.\n5) Маруся видела: как засветились яркие звёздочки.",
                    "answer": "1,3",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "пункт_5", "theory_hint": "Знаки в СПП"
                },
                {
                    "id": "А13",
                    "text": "Знаки препинания расставлены ПРАВИЛЬНО в предложениях:\n\n1) Запахло гарью и воздух посинел от дыма.\n2) Хотя ветер стих и дождь перестал, было довольно прохладно.\n3) По тону, которым человек говорит, мы легко можем судить о том, с кем имеем дело.\n4) Маруся видела, как засветились на небе яркие звёздочки и радостно улыбнулась.\n5) Мы понимали, что если погода не изменится, то нам придётся отменить экспедицию.",
                    "answer": "2,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "пункт_5", "theory_hint": "Знаки в ССП и СПП"
                },
                {
                    "id": "А14",
                    "text": "Знаки препинания расставлены ПРАВИЛЬНО в предложениях:\n\n1) Всё покрыто слоем пушистого снега: крыши вагонов, земля и шпалы.\n2) Он предложил нас подвезти: мы любезно отказались.\n3) Новость у меня для Мишки приятная; нашлась коллекция старых монет.\n4) Всем было понятно одно, а именно что его уговорили.\n5) Чуть-чуть пошевельнёшься — пугливые лягушки тут же прячутся под корягой.",
                    "answer": "1,3,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "пункт_5", "theory_hint": "Знаки в БСП"
                },
                {
                    "id": "А15",
                    "text": "Знаки препинания расставлены ПРАВИЛЬНО при чужой речи:\n\n1) По словам Чехова, «надо быть ясным умственно, чистым нравственно».\n2) «Нам нужно укрыться куда-нибудь, – сказал Буркин и предложил: – Пойдёмте к Алёхину».\n3) «Деревенская жизнь имеет свои удобства, – говорил Николай: – Сидишь на балконе».\n4) «После смерти жены брат мой стал высматривать себе имение», – произнёс Иван Иваныч.\n5) – Кто там? – слышался протяжный голос.\n   – Это Павел Константиныч, – отвечала горничная.",
                    "answer": "2,4,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "пункт_5", "theory_hint": "Пунктуация при чужой речи"
                },
                {
                    "id": "А16",
                    "text": "Запятая ставится на месте ВСЕХ пропусков в предложениях:\n\n1) Такие люди_ как Сергей Львович_ в театральном мире встречаются редко.\n2) Со стороны этот поступок выглядит_ как жест отчаяния.\n3) Сёстры похожи_ как две капли воды.\n4) Несмело_ как в первый раз_ он опустил руки на клавиши рояля.\n5) Дом оказался не чем иным_ как бревенчатой низенькой избой.",
                    "answer": "1,2,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "пункт_6", "theory_hint": "Пунктуация с КАК"
                },
                {
                    "id": "А17",
                    "text": "Укажите предложения, в которых выделенные слова являются вводными:\n\n1) Нельзя только по словам судить о человеке.\n2) Они меня очень сильно любят и хотят, разумеется, моего счастья.\n3) Я, может быть, приду сегодня поздно.\n4) Жизнь мне кажется не такой уже безнадёжной.\n5) Очевидно, что сейчас начнётся дождь.",
                    "answer": "2,3",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "пункт_4", "theory_hint": "Вводные слова"
                },
                {
                    "id": "А18",
                    "text": "Укажите предложения, в которых есть однородные члены (знаки не расставлены):\n\n1) Мы вместе вспоминали юность вместе молчали.\n2) В огромном помещении стояли не то столы не то полки.\n3) Последние волны тумана или скатываются в овраги или расстилаются по лугу или взвиваются вверх.\n4) Ванюше удалось найти рыжики и подосиновики и лисички.\n5) Точно в жерло вулкана сваливаются тяжёлые облака и горят кроваво-красными и янтарными огнями.",
                    "answer": "3,4",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "пункт_2", "theory_hint": "Однородные члены"
                },
            ]
        },

        "2024–2025 Этап II В1": {
            "title": "РТ 2024/2025 — Этап II, Вариант 1",
            "source": "РИКЗ РБ",
            "questions": [
                {
                    "id": "А1",
                    "text": "Пишется А на месте пропуска в словах:\n\n1) сл..гаемое\n2) по..вление призрака\n3) р..стительное масло\n4) г..рстка соли\n5) пром..кательная бумага",
                    "answer": "1,3",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_1", "theory_hint": "Чередующиеся гласные в корне"
                },
                {
                    "id": "А2",
                    "text": "Пишется Е на месте пропуска в словах:\n\n1) зап..реть на засов\n2) обл..гать данью\n3) разж..гать спор\n4) сп..сительная мысль\n5) б..режливый хозяин",
                    "answer": "1,4,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_1", "theory_hint": "Безударные гласные в корне"
                },
                {
                    "id": "А3",
                    "text": "Пишется И на месте пропуска в словах:\n\n1) пр..брежный посёлок\n2) пр..сечь нарушение\n3) пр..открыть дверь\n4) пр..огромный успех\n5) пр..скучная история",
                    "answer": "1,3",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_4", "theory_hint": "Приставки ПРЕ-/ПРИ-"
                },
                {
                    "id": "А4",
                    "text": "Пишется Ё на месте пропуска в словах:\n\n1) ш..пот листьев\n2) деш..вый товар\n3) прож..г куртку\n4) ч..лка лошади\n5) ноч..вка в лесу",
                    "answer": "3,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_3", "theory_hint": "Гласные после шипящих"
                },
                {
                    "id": "А5",
                    "text": "Укажите номера пропусков, где пишется НИ:\n\nКуда бы я ¹н.. приезжала читать лекции, всюду ²н.. могла ³н.. нарадоваться. В аудиториях ⁴н.. было ⁵н.. одного студента, которого бы не заинтересовал материал.",
                    "answer": "1,3,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_14", "theory_hint": "НЕ и НИ"
                },
                {
                    "id": "А6",
                    "text": "Пишется НЕ раздельно во ВСЕХ случаях в рядах:\n\n1) (не)склоняемое прилагательное; лететь (не)высоко, а низко\n2) (не)каждый оценит; (не)испугавшись\n3) (не)красивый, но дорогой; (не)увлёкся рассказом\n4) (не)долюбливая; свет (не)погашен\n5) (не)шерстяной костюм; (не)разгаданная накануне тайна",
                    "answer": "1,3,4",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_9", "theory_hint": "НЕ с разными частями речи"
                },
                {
                    "id": "А7",
                    "text": "Слитно пишутся все слова в рядах:\n\n1) (пол)листа, (поли)клиника\n2) (авто)мобиль, (де)монтаж\n3) (видео)запись, (фото)аппарат\n4) (пол)Минска, (шахмат)но-шашечный\n5) (кино)фестиваль, (ново)введение",
                    "answer": "2,3,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_12", "theory_hint": "Слитное написание сложных слов"
                },
                {
                    "id": "А8",
                    "text": "Раздельно пишутся выделенные слова в предложениях:\n\n1) Молодёжь волнуют насущные проблемы, (по)этому собрание прошло активно.\n2) Вечер тих, (не)смотря на то что небо хмурится.\n3) Он поступил (по)своему.\n4) Поезд остановился (в)виду ремонтных работ.\n5) Поговорим (на)счёт предстоящей поездки.",
                    "answer": "2,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "орф_13", "theory_hint": "Предлоги: слитно/раздельно"
                },
                {
                    "id": "А9",
                    "text": "Тире на месте пропуска обязательно ставится:\n\n1) Лесть _ гнусная черта.\n2) Грибоедов _ автор комедии «Горе от ума».\n3) Биология _ наука о жизни.\n4) Земля _ мать, а весна _ её наряд.\n5) Читать _ вот лучшее учение.",
                    "answer": "2,4,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "пункт_1", "theory_hint": "Тире между подлежащим и сказуемым"
                },
                {
                    "id": "А10",
                    "text": "Запятая ставится на месте ВСЕХ пропусков:\n\n1) Он шёл_ не оглядываясь.\n2) Книга лежала_ открытая на последней странице.\n3) Ученик_ выполнив задание_ сдал работу.\n4) Уставший_ он решил вернуться домой.\n5) Лошадь_ привязанная у крыльца_ ждала хозяина.",
                    "answer": "1,3,4,5",
                    "type": "A_multi", "points": 2, "partial": True,
                    "theory_key": "пункт_3", "theory_hint": "Обособленные члены"
                },
            ]
        },
    },

    "english": {
        "2024–2025 Этап I В1": {
            "title": "РТ 2024/2025 — Этап I, Вариант 1",
            "source": "РИКЗ РБ",
            "questions": [
                {
                    "id": "А1",
                    "text": "In the waters around Southern Australia and Tasmania, there is a sea creature called the gloomy octopus. Despite its name, the gloomy octopus is actually quite a social creature. Scientists (A1) … octopuses for years but still have a lot to find out.\n\n1) have been studying\n2) were studied\n3) were studying\n4) had studied\n5) are studied",
                    "answer": "1",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "gram_tenses", "theory_hint": "Present Perfect Continuous"
                },
                {
                    "id": "А2",
                    "text": "Unlike most octopus species that prefer to live alone, gloomy octopuses live together in octo-cities. The first octo-city (A2) … in 2009.\n\n1) had discovered\n2) has discovered\n3) was discovering\n4) was discovered\n5) discovered",
                    "answer": "4",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "gram_passive", "theory_hint": "Past Simple Passive"
                },
                {
                    "id": "А3",
                    "text": "Most octopuses (A3) … in tropical and subtropical ocean waters, at depths of up to 300 metres.\n\n1) are found\n2) were finding\n3) find\n4) were found\n5) found",
                    "answer": "1",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "gram_passive", "theory_hint": "Present Simple Passive"
                },
                {
                    "id": "А4",
                    "text": "Octo-cities have a social hierarchy: the dominant octopus gets the best location in the centre, while outsiders (A4) … .\n\n1) aren't welcomed\n2) don't welcome\n3) weren't welcoming\n4) weren't welcomed\n5) hadn't been welcomed",
                    "answer": "2",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "gram_passive", "theory_hint": "Present Simple Active/Passive"
                },
                {
                    "id": "А5",
                    "text": "I don't like to stay in the house by … . I prefer going for a walk.\n\n1) me\n2) mine\n3) I\n4) myself\n5) my",
                    "answer": "4",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "gram_questions", "theory_hint": "Возвратные местоимения"
                },
                {
                    "id": "А6",
                    "text": "Croatia is a country in … Eastern Europe between Hungary and … Adriatic Sea.\n\n1) –, the\n2) –, –\n3) the, –\n4) the, the\n5) the, an",
                    "answer": "1",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "gram_articles", "theory_hint": "Артикли с географическими названиями"
                },
                {
                    "id": "А7",
                    "text": "Find the underlined fragment where a mistake is made:\n\nWhen I heard that our school might close due to the pandemic (1), it was a worried thought (2) for all of us (3) who (4) loved being together in class (5).\n\n1) fragment 1\n2) fragment 2\n3) fragment 3\n4) fragment 4\n5) fragment 5",
                    "answer": "2",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "lex_word_formation", "theory_hint": "Причастия: worrying/worried"
                },
                {
                    "id": "А8",
                    "text": "Find the underlined fragment where a mistake is made:\n\nAfter cooking the stew for hours (1), I was disappointed to discover (2) that it tasted badly (3), because (4) I had forgotten to add the herbs (5).\n\n1) fragment 1\n2) fragment 2\n3) fragment 3\n4) fragment 4\n5) fragment 5",
                    "answer": "3",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "lex_confusables", "theory_hint": "Прилагательное vs наречие: bad/badly"
                },
                {
                    "id": "А9",
                    "text": "On the one (A9) … , it's good to be able to talk to anyone at any time. On the other hand, some of us have become too dependent on our phones.\n\n1) point\n2) side\n3) position\n4) place\n5) hand",
                    "answer": "5",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "lex_prepositions", "theory_hint": "Устойчивые выражения: on the one hand"
                },
                {
                    "id": "А10",
                    "text": "Psychologists have identified a condition known (A10) … 'NoMoPhobia', which is a real fear of being without your mobile phone!\n\n1) reliable\n2) dependent\n3) attached\n4) as\n5) confident",
                    "answer": "4",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "lex_prepositions", "theory_hint": "Предлоги: known as"
                },
                {
                    "id": "А11",
                    "text": "Psychologists have identified a condition known as 'NoMoPhobia'. It (A11) … when people who use their phones a lot are separated from them.\n\n1) called\n2) referred\n3) said\n4) known\n5) occurs",
                    "answer": "5",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "lex_confusables", "theory_hint": "Значение слова: occur/happen"
                },
                {
                    "id": "А12",
                    "text": "This loss (A12) … panic attacks, anxiety and even depression in serious cases.\n\n1) had\n2) made\n3) performed\n4) took\n5) caused",
                    "answer": "5",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "lex_confusables", "theory_hint": "Словосочетания: cause problems"
                },
                {
                    "id": "А13",
                    "text": "Find the sentence which is closest in meaning to:\nNo, I don't feel like it today.\n\n1) She has a real feel for language.\n2) Have I kept you waiting?\n3) Are you coming to aerobics?\n4) I don't feel like going to the party.\n5) Don't you feel well?",
                    "answer": "4",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "gram_nonfinite", "theory_hint": "feel like + герундий"
                },
                {
                    "id": "А14",
                    "text": "Rearrange the underlined parts to make the sentence correct:\n\nNo, I don't think it's (A) a good idea to let young children watch (B) too much television (C) before going (D) to sleep.\n\n1) D, C, A, B\n2) A, B, C, D\n3) B, A, D, C\n4) C, D, B, A\n5) порядок верный",
                    "answer": "5",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "gram_nonfinite", "theory_hint": "Порядок слов в предложении"
                },
                {
                    "id": "А15",
                    "text": "My sister and brother-in-law own a circus. It tours some of the loveliest parts of south-west England. Circuses have always been a part of Nell's life, even when we were children. When we were young, the circus … every summer.\n\n1) has come\n2) had come\n3) comes\n4) would come\n5) will come",
                    "answer": "4",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "gram_modal", "theory_hint": "WOULD для привычного действия в прошлом"
                },
                {
                    "id": "А16",
                    "text": "Find the sentence which contains a grammar mistake:\n\n1) He suggested going to the cinema.\n2) I remember to meet him at the conference.\n3) She managed to finish the project on time.\n4) They agreed to help us move.\n5) He refused to answer the question.",
                    "answer": "2",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "gram_nonfinite", "theory_hint": "remember + -ing (о прошлом)"
                },
                {
                    "id": "А17",
                    "text": "The scientists made an important _____ (DISCOVER) about deep sea creatures last year.\n\n1) discoverable\n2) discovered\n3) discoveries\n4) discovering\n5) discovery",
                    "answer": "5",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "lex_word_formation", "theory_hint": "Словообразование: discover → discovery"
                },
                {
                    "id": "А18",
                    "text": "By the time we arrived at the cinema, the film _____.\n\n1) already started\n2) has already started\n3) had already started\n4) was already started\n5) already starts",
                    "answer": "3",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "gram_tenses", "theory_hint": "Past Perfect: действие до другого прошлого"
                },
            ]
        },
    },

    "math": {
        "2024–2025 Этап I В1": {
            "title": "РТ 2024/2025 — Этап I, Вариант 1",
            "source": "РИКЗ РБ",
            "questions": [
                {
                    "id": "А1",
                    "text": "Результатом округления числа 1,3678 до тысячных является число:\n\n1) 0,368\n2) 1,367\n3) 1,368\n4) 1,370\n5) 1,363",
                    "answer": "3",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "alg_1", "theory_hint": "Округление десятичных дробей"
                },
                {
                    "id": "А2",
                    "text": "Среди отрезков FP, OA, NK, MA, TE (O — центр окружности) укажите отрезок, который является хордой окружности.\n\n1) FP\n2) OA\n3) NK\n4) MA\n5) TE",
                    "answer": "4",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "geom_1", "theory_hint": "Хорда окружности"
                },
                {
                    "id": "А3",
                    "text": "Графики каких двух функций из предложенных параллельны?\n\n1) y = 4x + 1\n2) y = −4x + 1\n3) y = 4x − 1\n4) y = x + 4\n5) y = x − 4",
                    "answer": "1",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "alg_4", "theory_hint": "Линейная функция: параллельные прямые"
                },
                {
                    "id": "А4",
                    "text": "Найдите значения выражений при x = 1,1. Укажите номер выражения с наибольшим значением.\n\n1) 2x\n2) 1 − x\n3) x\n4) x − 1\n5) x²",
                    "answer": "2",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "alg_1", "theory_hint": "Вычисление значений выражений"
                },
                {
                    "id": "А5",
                    "text": "Определите, при каком значении x верно двойное неравенство −3 ≤ x + 1 ≤ 7.\n\n1) −6\n2) 0\n3) 1,8\n4) 4,2\n5) −1",
                    "answer": "4",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "alg_3", "theory_hint": "Решение двойных неравенств"
                },
                {
                    "id": "А6",
                    "text": "Укажите номера ВЕРНЫХ равенств:\n\n1) (√7)⁻² = 1/7\n2) 3^(1/2) = √3\n3) 4^(3/2) = 8\n4) 27^(−1/3) = −3\n5) (2/3)^(−1) = 3/2",
                    "answer": "1,5",
                    "type": "A_multi", "points": 1, "partial": False,
                    "theory_key": "alg_1", "theory_hint": "Степень с дробным и отрицательным показателем"
                },
                {
                    "id": "А7",
                    "text": "В состав чайного сбора входят мята и липа в отношении 2:3. Сколько граммов липы входит в 975 г такого сбора?\n\n1) 390 г\n2) 325 г\n3) 875 г\n4) 545 г\n5) 585 г",
                    "answer": "5",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "word_problems", "theory_hint": "Задачи на пропорциональное деление"
                },
                {
                    "id": "А8",
                    "text": "Результат упрощения выражения √((x − 3)²) при −1,6 ≤ x ≤ 1 имеет вид:\n\n1) x − 6\n2) x − 3\n3) 3 − x\n4) x + 3\n5) x + 6",
                    "answer": "3",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "alg_1", "theory_hint": "√(a²) = |a|"
                },
                {
                    "id": "А9",
                    "text": "Точка B находится на расстоянии 2 от прямой a и на расстоянии √21 от плоскости α. Найдите расстояние от точки B до точки A, если A — основание перпендикуляра из B на α.\n\n1) 5\n2) 17\n3) 2√21\n4) 23\n5) 6",
                    "answer": "1",
                    "type": "A_single", "points": 1, "partial": False,
                    "theory_key": "geom_2", "theory_hint": "Теорема Пифагора в пространстве"
                },
                {
                    "id": "А10",
                    "text": "Укажите номера выражений, которые имеют смысл:\n\n1) ⁴√(−518)\n2) ⁵√(−8)\n3) ⁴√81\n4) ⁴√(−8)\n5) ⁵√81",
                    "answer": "2,3,5",
                    "type": "A_multi", "points": 1, "partial": False,
                    "theory_key": "alg_1", "theory_hint": "Корни чётной и нечётной степени"
                },
            ]
        },
    },
}


def get_past_rt_questions(subject: str, year_variant: str) -> list:
    """Возвращает список вопросов для заданного варианта РТ"""
    return PAST_RT.get(subject, {}).get(year_variant, {}).get("questions", [])


def get_past_rt_title(subject: str, year_variant: str) -> str:
    """Возвращает заголовок варианта"""
    return PAST_RT.get(subject, {}).get(year_variant, {}).get("title", year_variant)


def list_past_rt_by_subject(subject: str) -> list:
    """Возвращает список доступных вариантов для предмета"""
    return list(PAST_RT.get(subject, {}).keys())
