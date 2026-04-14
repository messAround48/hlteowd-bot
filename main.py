import os
import asyncio
from datetime import datetime, time
from telethon import TelegramClient, Button, events, connection

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
BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")

# MTProto прокси
MT_PROTO_PROXY = os.getenv("MT_PROTO_PROXY", "")  # формат: mtproxy://secret@host:port или secret@host:port


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


async def handle_start(event):
    """Обработчик команды /start."""
    keyboard = [[Button.inline("📊 Прогресс рабочего дня", b"progress")]]
    await event.respond(
        "Привет! Я бот для отслеживания прогресса рабочего дня.\n"
        "Нажми на кнопку ниже, чтобы узнать, сколько осталось до конца рабочего дня:",
        buttons=keyboard,
    )


async def handle_callback(event):
    """Обработчик нажатия на кнопку."""
    if event.data == b"progress":
        await event.answer()
        message = get_workday_progress()
        await event.edit(message, parse_mode="md")


def parse_mtproto_proxy(proxy_str: str):
    """Парсит строку MTProto прокси в формат для Telethon.

    Форматы:
        - mtproxy://secret@host:port
        - secret@host:port

    Возвращает кортеж (proxy_type, addr, port, secret, rdns, username, password)
    """
    if not proxy_str:
        return None

    # Убираем префикс если есть
    proxy_str = proxy_str.replace("mtproxy://", "")

    parts = proxy_str.rsplit("@", 1)
    if len(parts) != 2:
        print(f"Неверный формат MTProto прокси: {proxy_str}")
        return None

    secret, host_port = parts

    if ":" not in host_port:
        print(f"Неверный формат MTProto прокси (нет порта): {proxy_str}")
        return None

    host, port_str = host_port.rsplit(":", 1)
    try:
        port = int(port_str)
    except ValueError:
        print(f"Неверный порт в MTProto прокси: {port_str}")
        return None

    return (host, port, secret)


def main():
    """Запуск бота."""
    if not BOT_TOKEN:
        print("Ошибка: установите токен бота в переменную окружения TG_BOT_TOKEN")
        return

    connection_proxy = parse_mtproto_proxy(MT_PROTO_PROXY)
    client = TelegramClient("hlteowd-bot", 6, "a7899e410f0c6c24623890290306d947", connection=connection.ConnectionTcpMTProxyRandomizedIntermediate, proxy=connection_proxy)
    
    client.add_event_handler(handle_start, events.NewMessage(pattern="/start"))
    client.add_event_handler(handle_callback, events.CallbackQuery())

    print("Бот запущен...")
    client.start(bot_token=BOT_TOKEN)
    client.run_until_disconnected()


if __name__ == "__main__":
    main()
