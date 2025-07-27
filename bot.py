"""
CVD-Risk Telegram Bot
MVP: 10-year cardiovascular risk (WHO/ISH)
No data stored, no auth, no logs with personal data.
"""
import os
import logging
from typing import Any

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# === 0. Настройки логов: только WARNING и выше без текста сообщений ===
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.WARNING,
)

# === 1. Токен из переменной окружения ===
TOKEN = os.getenv("TOKEN")  # запуск:  TOKEN=ваш_токен python bot.py
if not TOKEN:
    raise RuntimeError("Укажите переменную окружения TOKEN")

# === 2. Таблица риска WHO/ISH (EURO) ===
RISK = {
    30: {
        "M": {
            "SBP<140":   {"TC<5": {"No": 1, "Yes": 2}, "TC>=5": {"No": 1, "Yes": 3}},
            "SBP140-159": {"TC<5": {"No": 1, "Yes": 3}, "TC>=5": {"No": 2, "Yes": 4}},
            "SBP>=160":   {"TC<5": {"No": 2, "Yes": 4}, "TC>=5": {"No": 3, "Yes": 5}},
        },
        "F": {
            "SBP<140":   {"TC<5": {"No": 1, "Yes": 1}, "TC>=5": {"No": 1, "Yes": 2}},
            "SBP140-159": {"TC<5": {"No": 1, "Yes": 2}, "TC>=5": {"No": 1, "Yes": 3}},
            "SBP>=160":   {"TC<5": {"No": 1, "Yes": 2}, "TC>=5": {"No": 2, "Yes": 4}},
        },
    },
    40: {
        "M": {
            "SBP<140":   {"TC<5": {"No": 2, "Yes": 4}, "TC>=5": {"No": 3, "Yes": 6}},
            "SBP140-159": {"TC<5": {"No": 3, "Yes": 6}, "TC>=5": {"No": 5, "Yes": 8}},
            "SBP>=160":   {"TC<5": {"No": 4, "Yes": 7}, "TC>=5": {"No": 6, "Yes": 10}},
        },
        "F": {
            "SBP<140":   {"TC<5": {"No": 1, "Yes": 2}, "TC>=5": {"No": 2, "Yes": 4}},
            "SBP140-159": {"TC<5": {"No": 2, "Yes": 4}, "TC>=5": {"No": 3, "Yes": 6}},
            "SBP>=160":   {"TC<5": {"No": 3, "Yes": 5}, "TC>=5": {"No": 4, "Yes": 8}},
        },
    },
    50: {
        "M": {
            "SBP<140":   {"TC<5": {"No": 5, "Yes": 9}, "TC>=5": {"No": 7, "Yes": 12}},
            "SBP140-159": {"TC<5": {"No": 7, "Yes": 12}, "TC>=5": {"No": 10, "Yes": 16}},
            "SBP>=160":   {"TC<5": {"No": 9, "Yes": 14}, "TC>=5": {"No": 13, "Yes": 20}},
        },
        "F": {
            "SBP<140":   {"TC<5": {"No": 3, "Yes": 5}, "TC>=5": {"No": 4, "Yes": 7}},
            "SBP140-159": {"TC<5": {"No": 4, "Yes": 7}, "TC>=5": {"No": 6, "Yes": 10}},
            "SBP>=160":   {"TC<5": {"No": 6, "Yes": 9}, "TC>=5": {"No": 8, "Yes": 13}},
        },
    },
    60: {
        "M": {
            "SBP<140":   {"TC<5": {"No": 8, "Yes": 14}, "TC>=5": {"No": 12, "Yes": 19}},
            "SBP140-159": {"TC<5": {"No": 12, "Yes": 19}, "TC>=5": {"No": 16, "Yes": 24}},
            "SBP>=160":   {"TC<5": {"No": 15, "Yes": 22}, "TC>=5": {"No": 20, "Yes": 28}},
        },
        "F": {
            "SBP<140":   {"TC<5": {"No": 5, "Yes": 9}, "TC>=5": {"No": 7, "Yes": 11}},
            "SBP140-159": {"TC<5": {"No": 7, "Yes": 11}, "TC>=5": {"No": 10, "Yes": 15}},
            "SBP>=160":   {"TC<5": {"No": 10, "Yes": 14}, "TC>=5": {"No": 13, "Yes": 19}},
        },
    },
    70: {
        "M": {
            "SBP<140":   {"TC<5": {"No": 14, "Yes": 21}, "TC>=5": {"No": 19, "Yes": 27}},
            "SBP140-159": {"TC<5": {"No": 19, "Yes": 27}, "TC>=5": {"No": 24, "Yes": 32}},
            "SBP>=160":   {"TC<5": {"No": 23, "Yes": 31}, "TC>=5": {"No": 28, "Yes": 36}},
        },
        "F": {
            "SBP<140":   {"TC<5": {"No": 9, "Yes": 14}, "TC>=5": {"No": 12, "Yes": 18}},
            "SBP140-159": {"TC<5": {"No": 12, "Yes": 18}, "TC>=5": {"No": 16, "Yes": 23}},
            "SBP>=160":   {"TC<5": {"No": 16, "Yes": 22}, "TC>=5": {"No": 20, "Yes": 27}},
        },
    },
}

# === 3. Утилиты ===
def classify_sbp(sbp: int) -> str:
    if sbp < 140:
        return "SBP<140"
    elif sbp < 160:
        return "SBP140-159"
    return "SBP>=160"

def classify_tc(tc: float) -> str:
    return "TC<5" if tc < 5 else "TC>=5"

# === 4. Conversation states ===
AGE, SEX, SBP, TC, SMOKE = range(5)

# === 5. Хэндлеры ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Привет! Я рассчитаю 10-летний риск сердечно-сосудистых событий.\n"
        "Сколько вам полных лет? (30–79)"
    )
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        age = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите число от 30 до 79.")
        return AGE

    # ближайший ключ из таблицы
    age = min(RISK.keys(), key=lambda x: abs(x - age))
    context.user_data["age"] = age
    await update.message.reply_text("Пол? М / Ж")
    return SEX

async def sex(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    s = update.message.text.strip().upper()
    if s in {"М", "M", "МУЖ", "MAN", "MALE"}:
        context.user_data["sex"] = "M"
    elif s in {"Ж", "F", "ЖЕН", "WOMAN", "FEMALE"}:
        context.user_data["sex"] = "F"
    else:
        await update.message.reply_text("Напишите М или Ж.")
        return SEX
    await update.message.reply_text("Систолическое давление (мм рт. ст.)?")
    return SBP

async def sbp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        sbp = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Введите целое число.")
        return SBP
    context.user_data["sbp"] = sbp
    await update.message.reply_text("Общий холестерин (ммоль/л)? Например 4.8")
    return TC

async def tc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text.strip().replace(",", ".")
    try:
        tc = float(raw.lstrip("≥><≤"))  # убираем символы
    except ValueError:
        await update.message.reply_text("Введите число, например 4.8 или 6.2")
        return TC
    context.user_data["tc"] = tc
    await update.message.reply_text("Курите? Да / Нет")
    return SMOKE

async def smoke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    smoke_raw = update.message.text.strip().lower()
    smoke = "Yes" if smoke_raw in {"да", "yes", "y", "1"} else "No"

    age = context.user_data["age"]
    sex = context.user_data["sex"]
    sbp = context.user_data["sbp"]
    tc_val = context.user_data["tc"]

    risk = RISK[age][sex][classify_sbp(sbp)][classify_tc(tc_val)][smoke]

    msg = f"Ваш 10-летний риск ССЗ: *{risk}%*\n\n"
    if smoke == "Yes":
        msg += "• Отказ от курения снижает риск на 30–50%.\n"
    if sbp >= 140:
        msg += "• Снижение давления на 10 мм рт. ст. – минус 20% риска.\n"
    if tc_val >= 5:
        msg += "• Снижение холестерина на 1 ммоль/л – минус ~25% риска.\n"
    msg += "\nЕсли риск ≥10 %, обсудите результаты с врачом."

    await update.message.reply_text(msg, parse_mode="Markdown")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("До свидания! Данные удалены.")
    context.user_data.clear()
    return ConversationHandler.END

# === 6. Глобальный обработчик ошибок ===
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.warning(f"Update {update} caused error: {context.error}")

# === 7. Запуск ===
def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            SEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, sex)],
            SBP: [MessageHandler(filters.TEXT & ~filters.COMMAND, sbp)],
            TC: [MessageHandler(filters.TEXT & ~filters.COMMAND, tc)],
            SMOKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, smoke)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    logging.info("Bot started")
    application.run_polling()


if __name__ == "__main__":
    main()