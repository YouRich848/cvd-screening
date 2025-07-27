import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, MessageHandler, filters, ContextTypes

TOKEN = "8440537378:AAFIBVSCsQl6J2DY3ztTIooj78YlH9-eixY"

# те же функции риска, что и в web-версии
def classify_sbp(sbp: int) -> str:
    if sbp < 140:  return "SBP<140"
    elif sbp < 160: return "SBP140-159"
    else: return "SBP>=160"

def classify_tc(tc: float) -> str:
    return "TC<5" if tc < 5 else "TC>=5"

RISK = {    30: {"M": {"SBP<140": {"TC<5": {"No": 1, "Yes": 2},
                          "TC>=5": {"No": 1, "Yes": 3}},
               "SBP140-159": {"TC<5": {"No": 1, "Yes": 3},
                              "TC>=5": {"No": 2, "Yes": 4}},
               "SBP>=160": {"TC<5": {"No": 2, "Yes": 4},
                            "TC>=5": {"No": 3, "Yes": 5}}},
          "F": {"SBP<140": {"TC<5": {"No": 1, "Yes": 1},
                            "TC>=5": {"No": 1, "Yes": 2}},
                "SBP140-159": {"TC<5": {"No": 1, "Yes": 2},
                               "TC>=5": {"No": 1, "Yes": 3}},
                "SBP>=160": {"TC<5": {"No": 1, "Yes": 2},
                             "TC>=5": {"No": 2, "Yes": 4}}}},
    40: {"M": {"SBP<140": {"TC<5": {"No": 2, "Yes": 4},
                          "TC>=5": {"No": 3, "Yes": 6}},
               "SBP140-159": {"TC<5": {"No": 3, "Yes": 6},
                              "TC>=5": {"No": 5, "Yes": 8}},
               "SBP>=160": {"TC<5": {"No": 4, "Yes": 7},
                            "TC>=5": {"No": 6, "Yes": 10}}},
          "F": {"SBP<140": {"TC<5": {"No": 1, "Yes": 2},
                            "TC>=5": {"No": 2, "Yes": 4}},
                "SBP140-159": {"TC<5": {"No": 2, "Yes": 4},
                               "TC>=5": {"No": 3, "Yes": 6}},
                "SBP>=160": {"TC<5": {"No": 3, "Yes": 5},
                             "TC>=5": {"No": 4, "Yes": 8}}}},
    50: {"M": {"SBP<140": {"TC<5": {"No": 5, "Yes": 9},
                          "TC>=5": {"No": 7, "Yes": 12}},
               "SBP140-159": {"TC<5": {"No": 7, "Yes": 12},
                              "TC>=5": {"No": 10, "Yes": 16}},
               "SBP>=160": {"TC<5": {"No": 9, "Yes": 14},
                            "TC>=5": {"No": 13, "Yes": 20}}},
          "F": {"SBP<140": {"TC<5": {"No": 3, "Yes": 5},
                            "TC>=5": {"No": 4, "Yes": 7}},
                "SBP140-159": {"TC<5": {"No": 4, "Yes": 7},
                               "TC>=5": {"No": 6, "Yes": 10}},
                "SBP>=160": {"TC<5": {"No": 6, "Yes": 9},
                             "TC>=5": {"No": 8, "Yes": 13}}}},
    60: {"M": {"SBP<140": {"TC<5": {"No": 8, "Yes": 14},
                          "TC>=5": {"No": 12, "Yes": 19}},
               "SBP140-159": {"TC<5": {"No": 12, "Yes": 19},
                              "TC>=5": {"No": 16, "Yes": 24}},
               "SBP>=160": {"TC<5": {"No": 15, "Yes": 22},
                            "TC>=5": {"No": 20, "Yes": 28}}},
          "F": {"SBP<140": {"TC<5": {"No": 5, "Yes": 9},
                            "TC>=5": {"No": 7, "Yes": 11}},
                "SBP140-159": {"TC<5": {"No": 7, "Yes": 11},
                               "TC>=5": {"No": 10, "Yes": 15}},
                "SBP>=160": {"TC<5": {"No": 10, "Yes": 14},
                             "TC>=5": {"No": 13, "Yes": 19}}}},
    70: {"M": {"SBP<140": {"TC<5": {"No": 14, "Yes": 21},
                          "TC>=5": {"No": 19, "Yes": 27}},
               "SBP140-159": {"TC<5": {"No": 19, "Yes": 27},
                              "TC>=5": {"No": 24, "Yes": 32}},
               "SBP>=160": {"TC<5": {"No": 23, "Yes": 31},
                            "TC>=5": {"No": 28, "Yes": 36}}},
          "F": {"SBP<140": {"TC<5": {"No": 9, "Yes": 14},
                            "TC>=5": {"No": 12, "Yes": 18}},
                "SBP140-159": {"TC<5": {"No": 12, "Yes": 18},
                               "TC>=5": {"No": 16, "Yes": 23}},
                "SBP>=160": {"TC<5": {"No": 16, "Yes": 22},
                             "TC>=5": {"No": 20, "Yes": 27}}}}
}  # скопируй словарь из app.py

AGE, SEX, SBP, TC, SMOKE = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я рассчитаю 10-летний риск ССЗ.\nСколько вам полных лет? (30–79)")
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        if age not in {30, 40, 50, 60, 70}:
            age = min({30, 40, 50, 60, 70}, key=lambda x: abs(x-age))
        context.user_data['age'] = age
        await update.message.reply_text("Пол? М / Ж")
        return SEX
    except ValueError:
        await update.message.reply_text("Введите число.")
        return AGE

async def sex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s = update.message.text.strip().upper()
    if s in ['М', 'M', 'МУЖ', 'MAN']:
        context.user_data['sex'] = 'M'
    elif s in ['Ж', 'F', 'ЖЕН', 'WOMAN']:
        context.user_data['sex'] = 'F'
    else:
        await update.message.reply_text("Напишите М или Ж.")
        return SEX
    await update.message.reply_text("Систолическое давление? 120, 150 или 170")
    return SBP

async def sbp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        val = int(update.message.text)
        context.user_data['sbp'] = val
        await update.message.reply_text("Общий холестерин (ммоль/л)? <5 или ≥5")
        return TC
    except ValueError:
        await update.message.reply_text("Введите число.")
        return SBP

async def tc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.strip().replace(',', '.')  # «5,51» → «5.51»
    try:
        # уберём символы «>» «≥» «<» «≤»
        num = float(raw.lstrip('≥>≤<'))  # «≥5» → «5»
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, введите число: например 4.2 или 6.8")
        return TC

    context.user_data['tc'] = num
    await update.message.reply_text("Курите? Да / Нет")
    return SMOKE

async def smoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    smoke = update.message.text.strip().lower()
    smoke = 'Yes' if smoke in {'да', 'yes', 'y', '1'} else 'No'
    age = context.user_data['age']
    sex = context.user_data['sex']
    sbp = context.user_data['sbp']
    tc = context.user_data['tc']

    risk = RISK[age][sex][classify_sbp(sbp)][classify_tc(tc)][smoke]
    await update.message.reply_text(
        f"Ваш 10-летний риск ССЗ: *{risk}%*",
        parse_mode='Markdown')
    await update.message.reply_text(
        "Если риск ≥10 %, обсудите результаты с врачом.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("До свидания!")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            SEX: [MessageHandler(filters.TEXT & ~filters.COMMAND, sex)],
            SBP: [MessageHandler(filters.TEXT & ~filters.COMMAND, sbp)],
            TC:  [MessageHandler(filters.TEXT & ~filters.COMMAND, tc)],
            SMOKE: [MessageHandler(filters.TEXT & ~filters.COMMAND, smoke)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(conv)
    application.run_polling()

if __name__ == '__main__':
    main()