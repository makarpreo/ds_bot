import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from config import TOKEN, LOGIN, PASSWORD, IP, PORT
from parser import get_cybershoke_duels_connects
# 1. НАСТРОЙКА ИНТЕНТОВ (ПРАВ ДОСТУПА)
# Интенты обязательны, без них бот не сможет читать сообщения или видеть пользователей
intents = discord.Intents.default()
intents.message_content = True  # Чтение содержимого сообщений (для префиксных команд)
intents.members = True          # Видеть участников (для приветствий, банов)
intents.voice_states = True     # Видеть подключения к голосовым каналам

# PROXY_URL = f"http://{LOGIN}:{PASSWORD}@{IP}:{PORT}"

intents = discord.Intents.default()
intents.message_content = True

# Передаем прокси в constructor бота
bot = commands.Bot(command_prefix="!", intents=intents) #, proxy=PROXY_URL


# 2. ИНИЦИАЛИЗАЦИЯ И СИНХРОНИЗАЦИЯ СЛЭШ-КОМАНД (/)
@bot.event
async def on_ready():
    print("=" * 40)
    print(f" УСПЕШНЫЙ ЗАПУСК!")
    print(f" Бот авторизован как: {bot.user.name} (ID: {bot.user.id})")
    print(f" Пинг до Discord API: {round(bot.latency * 1000)} мс")
    print(" Бот полностью готов к работе и слушает команды!")
    print("=" * 40)

    print(f"[{bot.user}] успешно авторизован.")
    try:
        # Синхронизируем слэш-команды глобально, чтобы они появились в Discord
        synced = await bot.tree.sync()
        print(f"Синхронизировано слэш-команд: {len(synced)}")
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")
        
    # Установка статуса бота (Играет в...)
    await bot.change_presence(activity=discord.Game(name="pipiskoi"))


# Слэш-команда с выпадающим списком вариантов (Choices)
@bot.tree.command(name="roll", description="Бросить кубик с выбором граней")
@app_commands.choices(грани=[
    app_commands.Choice(name="D6 (6 граней)", value=6),
    app_commands.Choice(name="D20 (20 граней)", value=20),
    app_commands.Choice(name="D100 (100 граней)", value=100)
])
async def roll(interaction: discord.Interaction, грани: app_commands.Choice[int]):
    import random
    result = random.randint(1, грани.value)
    await interaction.response.send_message(f"🎲 Вы бросили {грани.name} и выпало: **{result}**")

# ==============================================================================
# КОМАНДА DUELS (ПАРСИНГ СЕРВЕРОВ)
# ==============================================================================

@bot.command(name="duels")
async def duels(ctx, map_name: str = "dust"):
    map_name = map_name.lower()
    
    if map_name not in ["dust", "mirage"]:
        await ctx.send("❌ Доступные карты только: `dust` или `mirage`")
        return

    # Сначала отправляем сообщение и сразу сохраняем его в переменную status_message
    status_message = await ctx.send(f"🔎 Начинаю сбор серверов для карты: **{map_name.upper()}**... Подождите.")

    try:
        # Вызываем правильное имя функции: get_cybershoke_duels_connects
        # Запуск в asyncio.to_thread обязателен, чтобы Selenium не вешал всего бота
        servers = await asyncio.to_thread(get_cybershoke_duels_connects, map_name)

        if not servers:
            await status_message.edit(content=f"❌ Серверы для карты **{map_name.upper()}** не найдены.")
            return

        # Форматируем вывод IP и Онлайна для копирования в один клик
        lines = []
        lines.append(f"✅ **Найдено серверов ({map_name.upper()}):** {len(servers)}\n")
        
        for s in servers:
            # Каждая строка коннекта оборачивается в однострочный блок кода `...`, 
            # благодаря чему Дискорд позволяет скопировать только её одним нажатием.
            lines.append(f"`{s['connect']}` — Онлайн: **{s['online']}**")

        response_text = "\n".join(lines)
        
        # Если серверов слишком много, разбиваем на части, чтобы не превысить лимит Дискорда в 2000 символов
        if len(response_text) > 2000:
            await status_message.delete()
            # Отправляем кусками по 15 серверов
            for i in range(0, len(lines), 15):
                chunk = "\n".join(lines[i:i+15])
                if i == 0:
                    await ctx.send(chunk)
                else:
                    await ctx.send(chunk)
        else:
            await status_message.edit(content=response_text)

    except Exception as e:
        # Теперь status_message гарантированно существует и отредактируется без ошибок
        await status_message.edit(content=f"❌ Произошла ошибка при парсинге: {e}")

# ==============================================================================
# 8. ОБРАБОТКА ОШИБОК (ERROR HANDLING)
# ==============================================================================

# ЗАПУСК БОТА (ВСТАВЬТЕ СЮДА СВОЙ ТОКЕН)
bot.run(TOKEN)
