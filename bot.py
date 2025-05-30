import discord
from discord import app_commands
from discord.ext import commands
import os
import logging
import asyncio
import aiohttp

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

# Настройка интентов бота
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Создание бота
bot = commands.Bot(command_prefix='!', intents=intents)

# Категория для тикетов
TICKET_CATEGORY_NAME = "🚑・ПОМОЩЬ"

# Переменные для верификации
VERIFICATION_CHANNEL_ID = None
VERIFIED_ROLE_ID = None

@bot.event
async def on_ready():
    logger.info(f'Бот {bot.user} успешно запущен!')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Синхронизировано {len(synced)} команд")
    except Exception as e:
        logger.error(f"Ошибка при синхронизации команд: {e}")

@bot.tree.command(name="setup", description="Настройка системы тикетов")
@app_commands.checks.has_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    """Настройка системы тикетов"""
    try:
        # Создание категории для тикетов
        category = discord.utils.get(interaction.guild.categories, name=TICKET_CATEGORY_NAME)
        if category is None:
             category = await interaction.guild.create_category(TICKET_CATEGORY_NAME)
        
        # Создание канала для создания тикетов
        channel = discord.utils.get(category.text_channels, name="создать-тикет")
        if channel is None:
            channel = await interaction.guild.create_text_channel(
                "создать-тикет",
                category=category
            )
        
        # Создание сообщения с кнопкой
        embed = discord.Embed(
            title="🎫 Создать тикет",
            description="Нажмите на кнопку ниже, чтобы создать новый тикет",
            color=discord.Color.blue()
        )
        
        # Создание кнопки
        button = discord.ui.Button(
            style=discord.ButtonStyle.primary,
            label="Создать тикет",
            custom_id="create_ticket"
        )
        
        view = discord.ui.View()
        view.add_item(button)
        
        # Проверяем, есть ли уже сообщение с кнопкой, и удаляем старое
        async for msg in channel.history(limit=10):
            if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "🎫 Создать тикет":
                await msg.delete()
                break

        await channel.send(embed=embed, view=view)
        await interaction.response.send_message("Система тикетов успешно настроена!", ephemeral=True)
    except Exception as e:
        logger.error(f"Ошибка при настройке тикетов: {e}")
        await interaction.response.send_message("Произошла ошибка при настройке тикетов. Проверьте права бота.", ephemeral=True)

@bot.tree.command(name="close", description="Закрыть текущий тикет")
async def close(interaction: discord.Interaction):
    """Закрытие тикета"""
    try:
        if not interaction.channel.name.startswith("тикет-"):
            await interaction.response.send_message("Эта команда может быть использована только в каналах тикетов!", ephemeral=True)
            return
        
        await interaction.response.send_message("Тикет будет закрыт через 5 секунд...", ephemeral=True)
        await interaction.channel.delete()
    except Exception as e:
        logger.error(f"Ошибка при закрытии тикета: {e}")
        await interaction.response.send_message("Произошла ошибка при закрытии тикета.", ephemeral=True)

@bot.tree.command(name="set_verification", description="Настройка системы верификации")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    channel="Канал для отправки сообщения о верификации",
    role="Роль, которая будет выдана после верификации"
)
async def set_verification(interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role):
    """Настройка системы верификации"""
    global VERIFICATION_CHANNEL_ID, VERIFIED_ROLE_ID
    try:
        VERIFICATION_CHANNEL_ID = channel.id
        VERIFIED_ROLE_ID = role.id

        embed = discord.Embed(
            title="✅ Верификация",
            description="Нажмите на кнопку ниже, чтобы пройти верификацию и получить доступ к серверу.",
            color=discord.Color.green()
        )

        button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Верифицироваться",
            custom_id="verify_button"
        )

        view = discord.ui.View()
        view.add_item(button)
        
        # Проверяем, есть ли уже сообщение верификации, и удаляем старое
        async for msg in channel.history(limit=10):
            if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "✅ Верификация":
                await msg.delete()
                break

        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"Система верификации настроена! Канал: {channel.mention}, Роль: {role.name}", ephemeral=True)
    except Exception as e:
        logger.error(f"Ошибка при настройке верификации: {e}")
        await interaction.response.send_message("Произошла ошибка при настройке системы верификации.", ephemeral=True)

@bot.event
async def on_member_join(member: discord.Member):
    logger.info(f'{member.name} присоединился к серверу.')
    # Здесь можно добавить отправку приватного сообщения пользователю, если нужно
    # if VERIFICATION_CHANNEL_ID:
    #     try:
    #         channel = bot.get_channel(VERIFICATION_CHANNEL_ID)
    #         if channel:
    #              await member.send(f"Добро пожаловать на сервер! Пожалуйста, перейдите в канал {channel.mention} для верификации.")
    #     except Exception as e:
    #         logger.error(f"Ошибка при отправке сообщения о верификации {member.name}: {e}")

@bot.event
async def on_interaction(interaction: discord.Interaction):
    try:
        if interaction.type == discord.InteractionType.component and interaction.data:
            custom_id = interaction.data.get('custom_id')
            if custom_id == "create_ticket":
                # Логика создания тикета
                category = discord.utils.get(interaction.guild.categories, name=TICKET_CATEGORY_NAME)
                if category is None:
                     # Если категория тикетов не найдена, пытаемся создать ее
                     try:
                         category = await interaction.guild.create_category(TICKET_CATEGORY_NAME)
                     except Exception as e:
                         logger.error(f"Не удалось найти или создать категорию тикетов: {e}")
                         await interaction.response.send_message("Не удалось создать тикет: не найдена или не может быть создана категория для тикетов.", ephemeral=True)
                         return

                # Создание канала тикета
                ticket_channel = await interaction.guild.create_text_channel(
                    f"тикет-{interaction.user.name}",
                    category=category,
                    overwrites={
                        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    }
                )
                
                # Создание сообщения в тикете
                embed = discord.Embed(
                    title="🎫 Новый тикет",
                    description=f"Тикет создан пользователем {interaction.user.mention}\n\nИспользуйте команду `/close` чтобы закрыть тикет",
                    color=discord.Color.green()
                )
                
                await ticket_channel.send(embed=embed)
                await interaction.response.send_message(f"Тикет создан! {ticket_channel.mention}", ephemeral=True)

            elif custom_id == "verify_button":
                # Логика верификации
                if VERIFIED_ROLE_ID:
                    role = interaction.guild.get_role(VERIFIED_ROLE_ID)
                    if role:
                        # Проверяем, есть ли уже роль у пользователя
                        if role in interaction.user.roles:
                            # Отправляем эфемеральное сообщение, если пользователь уже верифицирован
                            await interaction.response.send_message("Вы уже верифицированы!", ephemeral=True)
                        else:
                            await interaction.user.add_roles(role)
                            # Отправляем обычное сообщение и планируем его удаление
                            await interaction.response.defer(ephemeral=True) # Откладываем ответ, чтобы можно было использовать followup
                            success_message = await interaction.followup.send("Вы успешно верифицированы!", ephemeral=False) # Отправляем обычное сообщение
                            await asyncio.sleep(5) # Ждем 5 секунд
                            await success_message.delete() # Удаляем сообщение
                    else:
                        await interaction.response.send_message("Произошла ошибка: роль для верификации не найдена. Обратитесь к администратору.", ephemeral=True)
                else:
                     await interaction.response.send_message("Система верификации не настроена администратором.", ephemeral=True)


    except Exception as e:
        logger.error(f"Ошибка при обработке взаимодействия: {e}")
        try:
            # Пытаемся ответить на взаимодействие, если оно еще не было обработано
            if not interaction.response.is_done():
                 await interaction.response.send_message("Произошла ошибка при обработке вашего запроса.", ephemeral=True)
        except:
            pass # Пропускаем, если ответить не удалось

@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Произошла ошибка в событии {event}: {args} {kwargs}")

# Запуск бота
if __name__ == "__main__":
    TOKEN = os.getenv('TOKEN')  # Получаем токен из переменных окружения
    if not TOKEN:
        TOKEN = "MTM3Nzg0MzU2MDUwNTY3MTgxMA.GHX1i4.U1t6f8wYBOwH0idGuS3TD-zunMKtEB8A2vxUh8"
    
    async def main():
        async with bot:
            try:
                await bot.start(TOKEN)
            except Exception as e:
                logger.error(f"Ошибка при запуске бота: {e}")
                logger.info("Повторная попытка подключения через 60 секунд...")
                await asyncio.sleep(60)
                await main()  # Рекурсивный вызов для повторной попытки
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        # Закрываем все сессии
        if not bot.is_closed():
            asyncio.run(bot.close()) 