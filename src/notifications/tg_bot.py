from src.config import config
from src.db import get_random_no_experience_vacancy, toggle_favorites
from src.filters import format_random_vacancy_message, format_vacancy_message
import asyncio
import re
from src.db import init_db, fetch_favorites, fetch_vacancies
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

user_state = {}

async def start(update, context):
    await update.message.reply_text(
        "Hey bumbum",
        reply_markup=bottom_menu()
    )

def bottom_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("Запустить парсер")],
            [KeyboardButton("Избранные"), KeyboardButton("Все вакансии")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Поиск", callback_data="search")],
        [InlineKeyboardButton("Избранные", callback_data="favorites")],
        [InlineKeyboardButton("Все вакансии", callback_data="all")],
    ])

def vacancy_controls(vacancy_id: int, is_favorite: bool, vacancy_url):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️", callback_data="prev"),
            InlineKeyboardButton("➡️", callback_data="next"),
        ],
        [
            InlineKeyboardButton(
                "⭐ Убрать" if is_favorite else "🤍 В избранное",
                callback_data=f"fav:{vacancy_id}"
            )
        ],
        [
            InlineKeyboardButton("🔗 Открыть", url=vacancy_url)
        ]
    ])

async def show_vacancy(update, context):
    chat_id = update.effective_chat.id
    state = user_state[chat_id]
    if not state: return

    vacancies = state["vacancies"]
    idx = state["index"]
    total = len(vacancies)
    current = idx + 1

    if not vacancies:
        await update.effective_message.reply_text("Ничего не найдено 😕")
        return

    v = vacancies[idx]

    text = (
        f"📄 {current} / {total}\n\n"
        f"{format_vacancy_message(v)}"
    )

    if update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=vacancy_controls(v["id"], v["is_favorite"], v["url"]),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    else:
        # Если это обычное сообщение
        await update.message.reply_text(
            text,
            reply_markup=vacancy_controls(v["id"], v["is_favorite"], v["url"]),
            parse_mode="HTML",
            disable_web_page_preview=True
        )

def load_vacancies(mode="all", query=None):
    conn = init_db()

    if mode == "favorites":
        rows = fetch_favorites(conn)
    elif mode == "search":
        rows = fetch_vacancies(conn, search=query)
    else:
        rows = fetch_vacancies(conn)

    conn.close()
    return rows

async def text_input(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text.strip()


    if "Запустить парсер" in text:
        user_state[chat_id] = {
            "step": "vacancy",
            "params": {}
        }

        await update.message.reply_text(
            "🔎 Какую вакансию ищем?\n\nНапример: <b>Python разработчик</b>",
            parse_mode = "HTML"
        )
        return
    if "Все вакансии" in text:
        state = user_state.setdefault(chat_id, {})
        state["mode"] = "all"
        state["vacancies"] = load_vacancies("all")
        state["index"] = 0
        await show_vacancy(update, context)
        return
    
    if "Избранные" in text:
        state = user_state.setdefault(chat_id, {})
        state["mode"] = "favorites"
        state["vacancies"] = load_vacancies("favorites")
        state["index"] = 0
        await show_vacancy(update, context)
        return
    
    state = user_state.get(chat_id)
    if not state or "step" not in state:
        return
    
    if state["step"] == "vacancy":
        state["params"]["vacancy"] = text
        state["step"] = "region"
        await update.message.reply_text("Укажи регион")
        return
    
    if state["step"] == "region":
        state["params"]["region"] = text
        state["step"] = "min_salary"
        await update.message.reply_text("Укажи минимальную зарплату")
        return

    if state["step"] == "min_salary":
        if not text.isdigit(): 
            await update.message.reply_text("Введите число")
            return
        state["params"]["min_salary"] = text
        state["step"] = "pages_to_parse"
        await update.message.reply_text("Укажи Количество страниц для парсинга")
        return

    if state["step"] == "pages_to_parse":
        state["params"]["pages_to_parse"] = text
        state["step"] = "sites"
        await update.message.reply_text("Укажи сайты(avito, hh) через пробел")
        return
    
    if state["step"] == "sites":
        sites = re.split(r"[,\s]+", text.lower())
        sites = [s for s in sites if s]
        state["params"]["sites"] = sites
        await start_parser(update, context, state["params"])
        return
    
async def start_parser(update, context, state):
    print(state)
    
    #user_state.pop(chat_id, None)

async def callbacks(update, context):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    data = query.data

    state = user_state.setdefault(chat_id, {
        "mode": "all",
        "query": None,
        "index": 0,
        "vacancies": []
    })

    if data == "all":
        state["mode"] = "all"
        state["vacancies"] = load_vacancies("all")
        state["index"] = 0
    elif data == "favorites":
        state["mode"] = "favorites"
        state["vacancies"] = load_vacancies("favorites")
        state["index"] = 0

    elif data == "next":
        old_index = state["index"]
        state["index"] = min(
            state["index"] + 1,
            len(state["vacancies"]) - 1
        )

        if old_index == state["index"]:
            return

    elif data == "prev":
        old_index = state["index"]
        state["index"] = max(state["index"] - 1, 0)

        if old_index == state["index"]:
            return

    elif data.startswith("fav:"):
        vacancy_id = int(data.split(":")[1])
        conn = init_db()
        toggle_favorites(conn, vacancy_id)
        conn.close()
        state["vacancies"] = load_vacancies(state["mode"])

        if not state["vacancies"]:
            await query.message.edit_text(
                "⭐ Список пуст",
                reply_markup=None
            )
            return

        state["index"] = min(
            state["index"],
            len(state["vacancies"]) - 1
        )

    await show_vacancy(update, context)


def main():
    # conn = init_db()
    # try:
    #     await send_random_no_experience_vacancy(conn)
    # finally:
    #     conn.close()
    app = ApplicationBuilder().token(config["TELEGRAM_BOT_TOKEN"]).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_input))

    app.run_polling()

if __name__ == "__main__":
    main()

