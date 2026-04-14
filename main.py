import os
from datetime import datetime, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Настройки рабочего дня по дням недели (0=понедельник, 6=воскресенье)
WORK_SCHEDULE = {
    0: (time(8, 0), time(17, 0)),  # Понедельник
    1: (time(8, 0), time(17, 0)),  # Вторник
    2: (time(8, 0), time(17, 0)),  # Среда
    3: (time(8, 0), time(17, 0)),  # Четверг
    4: (time(8, 0), time(16, 0)),  # Пятница
    5: None,                        # Суббота - выходной
    6: None,                        # Воскресенье - выходной
}

DAY_NAMES = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье",
}

# Токен бота (получить у @BotFather)
BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")


def get_workday_progress() -> str:
    """Рассчитывает прогресс рабочего дня и возвращает сообщение."""
    now_dt = datetime.now()
    now = now_dt.time()
    weekday = now_dt.weekday()

    schedule = WORK_SCHEDULE.get(weekday)

    # Выходной
    if schedule is None:
        return f"🎉 Сегодня {DAY_NAMES[weekday]} — выходной!"

    work_start, work_end = schedule

    start_dt = now_dt.replace(hour=work_start.hour, minute=work_start.minute, second=0, microsecond=0)
    end_dt = now_dt.replace(hour=work_end.hour, minute=work_end.minute, second=0, microsecond=0)

    # Если сейчас до начала рабочего дня
    if now < work_start:
        return f"🌅 Рабочий день ещё не начался.\nНачало в {work_start.strftime('%H:%M')}."

    # Если сейчас после конца рабочего дня
    if now > work_end:
        return f"🌙 Рабочий день уже закончился.\nКонец в {work_end.strftime('%H:%M')}."

    # Расчёт прогресса
    total_seconds = (end_dt - start_dt).total_seconds()
    elapsed_seconds = (now_dt - start_dt).total_seconds()
    remaining_seconds = total_seconds - elapsed_seconds

    percentage = (elapsed_seconds / total_seconds) * 100
    hours = int(remaining_seconds // 3600)
    minutes = int((remaining_seconds % 3600) // 60)

    # Визуальный прогресс-бар
    bar_length = 10
    filled = int(bar_length * percentage / 100)
    bar = "█" * filled + "░" * (bar_length - filled)

    message = (
        f"📊 *Прогресс рабочего дня*\n"
        f"📅 {DAY_NAMES[weekday]} | ⏰ {now.strftime('%H:%M')}\n\n"
        f"{bar} {percentage:.1f}%\n\n"
        f"🔹 Осталось: *{hours} ч {minutes} мин*\n"
        f"🔹 Начало: {work_start.strftime('%H:%M')}\n"
        f"🔹 Конец: {work_end.strftime('%H:%M')}"
    )
    return message


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    keyboard = [
        [InlineKeyboardButton("📊 Прогресс рабочего дня", callback_data="progress")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Я бот для отслеживания прогресса рабочего дня.\n"
        "Нажми на кнопку ниже, чтобы узнать, сколько осталось до конца рабочего дня:",
        reply_markup=reply_markup,
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку."""
    query = update.callback_query
    await query.answer()

    message = get_workday_progress()
    await query.edit_message_text(
        text=message,
        parse_mode="Markdown",
    )


def main():
    """Запуск бота."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Ошибка: установите токен бота в переменную окружения TG_BOT_TOKEN")
        print("Или замените YOUR_BOT_TOKEN_HERE в коде на ваш токен от @BotFather")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
