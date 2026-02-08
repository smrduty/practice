from src.config import config
from src.db import get_random_no_experience_vacancy
from src.filters import format_random_vacancy_message, format_vacancy_message
import asyncio
from src.db import init_db, fetch_favorites, fetch_vacancies
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

user_state = {}

async def start(update, context):
    await update.message.reply_text(
        "n",
        reply_markup=main_menu()
    )

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Поиск", callback_data="search")],
        [InlineKeyboardButton("⭐ Избранные", callback_data="favorites")],
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

    vacancies = state["vacancies"]
    idx = state["index"]

    if not vacancies:
        await update.effective_message.reply_text("Ничего не найдено 😕")
        return

    v = vacancies[idx]

    await update.effective_message.edit_text(
        format_vacancy_message(v),
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
        state["index"] = min(
            state["index"] + 1,
            len(state["vacancies"]) - 1
        )

    elif data == "prev":
        state["index"] = max(state["index"] - 1, 0)

    # elif data.startswith("fav:"):
    #     vacancy_id = int(data.split(":")[1])
    #     conn = init_db()
    #     toggle_favorite(conn, vacancy_id)
    #     conn.close()
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

    app.run_polling()

if __name__ == "__main__":
    main()

