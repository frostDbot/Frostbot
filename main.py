import discord
import asyncio
from discord.ext import commands
import os
import logging
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'),
              logging.StreamHandler()])
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Necessário para ver membros do servidor
intents.guilds = True  # Necessário para acessar informações do servidor
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
  try:
    logger.info(f'Bot conectado como {bot.user}')
    print(f'Bot conectado como {bot.user}')

    # Aguardar um pouco antes de sincronizar
    await asyncio.sleep(2)

    # Sincronizar comandos
    synced = await bot.tree.sync()
    logger.info(f'Sincronizados {len(synced)} comandos slash')
    print(f'Sincronizados {len(synced)} comandos slash')

    # Log dos comandos sincronizados para debug
    for command in synced:
      logger.info(f'Comando sincronizado: /{command.name}')
      print(f'Comando sincronizado: /{command.name}')

  except Exception as e:
    logger.error(f'Erro crítico em on_ready: {e}')
    logger.error(f'Traceback: {traceback.format_exc()}')
    print(f'Erro ao sincronizar comandos: {e}')


@bot.event
async def on_error(event, *args, **kwargs):
  logger.error(f'Erro no evento {event}: {args}, {kwargs}')
  logger.error(f'Traceback: {traceback.format_exc()}')
  print(f'Erro no evento {event}')


@bot.event
async def on_command_error(ctx, error):
  logger.error(f'Erro no comando {ctx.command}: {error}')
  logger.error(f'Usuário: {ctx.author}, Canal: {ctx.channel}')
  logger.error(f'Traceback: {traceback.format_exc()}')
  print(f'Erro no comando: {error}')


# Carregar extensões (cogs)
async def load_extensions():
  logger.info("Iniciando carregamento de extensões...")
  print("Iniciando carregamento de extensões...")

  try:
    # Verificar se o diretório coag existe
    if not os.path.exists("./coag"):
      logger.warning("Diretório './coag' não encontrado")
      print("Aviso: Diretório './coag' não encontrado")
      return

    cog_files = [
        f for f in os.listdir("./coag")
        if f.endswith(".py") and f != "__init__.py" and f != "log.py"
    ]

    if not cog_files:
      logger.info("Nenhum arquivo de cog encontrado no diretório './coag'")
      print("Nenhum arquivo de cog encontrado")
      return

    logger.info(f"Encontrados {len(cog_files)} arquivos de cog: {cog_files}")
    print(f"Encontrados {len(cog_files)} arquivos de cog")

    for filename in cog_files:
      try:
        cog_name = filename[:-3]  # Remove .py
        await bot.load_extension(f"coag.{cog_name}")
        logger.info(f"Extensão carregada com sucesso: {cog_name}")
        print(f"Loaded extension: {cog_name}")

      except commands.ExtensionNotFound:
        logger.error(f"Extensão não encontrada: {cog_name}")
        print(f"Erro: Extensão não encontrada: {cog_name}")

      except commands.ExtensionAlreadyLoaded:
        logger.warning(f"Extensão já carregada: {cog_name}")
        print(f"Aviso: Extensão já carregada: {cog_name}")

      except commands.NoEntryPointError:
        logger.error(f"Função setup() não encontrada em: {cog_name}")
        print(f"Erro: Função setup() não encontrada em: {cog_name}")

      except commands.ExtensionFailed as e:
        logger.error(f"Falha ao carregar extensão {cog_name}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"Failed to load extension {cog_name}: {e}")

      except Exception as e:
        logger.error(f"Erro inesperado ao carregar {cog_name}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"Erro inesperado ao carregar {cog_name}: {e}")

  except PermissionError:
    logger.error("Sem permissão para acessar o diretório './coag'")
    print("Erro: Sem permissão para acessar o diretório './coag'")

  except Exception as e:
    logger.error(f"Erro crítico ao carregar extensões: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    print(f"Erro crítico ao carregar extensões: {e}")


async def main():
  logger.info("Iniciando aplicação do bot...")
  print("Iniciando aplicação do bot...")

  try:
    # Verificar token
    token = os.getenv("DISCORD_TOKEN")
    if not token:
      logger.critical(
          "DISCORD_TOKEN não configurado nas variáveis de ambiente!")
      print("Error: DISCORD_TOKEN environment variable not set!")
      return

    if len(token.strip()) == 0:
      logger.critical("DISCORD_TOKEN está vazio!")
      print("Error: DISCORD_TOKEN is empty!")
      return

    logger.info("Token encontrado, iniciando bot...")
    print("Token encontrado, iniciando bot...")

    async with bot:
      try:
        await load_extensions()
        logger.info("Tentando conectar ao Discord...")
        print("Tentando conectar ao Discord...")

        await bot.start(token)

      except discord.LoginFailure:
        logger.critical("Token do Discord inválido!")
        print("Error: Invalid Discord token!")

      except discord.HTTPException as e:
        logger.error(f"Erro HTTP do Discord: {e}")
        print(f"Erro HTTP do Discord: {e}")

      except discord.ConnectionClosed as e:
        logger.error(f"Conexão com Discord fechada: {e}")
        print(f"Conexão com Discord fechada: {e}")

      except asyncio.TimeoutError:
        logger.error("Timeout ao conectar com Discord")
        print("Timeout ao conectar com Discord")

      except Exception as e:
        logger.error(f"Erro inesperado ao iniciar bot: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        print(f"Error starting bot: {e}")

  except KeyboardInterrupt:
    logger.info("Bot interrompido pelo usuário")
    print("Bot interrompido pelo usuário")

  except Exception as e:
    logger.critical(f"Erro crítico na função main: {e}")
    logger.critical(f"Traceback: {traceback.format_exc()}")
    print(f"Erro crítico: {e}")

  finally:
    logger.info("Encerrando aplicação...")
    print("Encerrando aplicação...")


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    logger.info("Aplicação encerrada pelo usuário")
    print("Aplicação encerrada pelo usuário")
  except Exception as e:
    logger.critical(f"Erro fatal ao executar aplicação: {e}")
    logger.critical(f"Traceback: {traceback.format_exc()}")
    print(f"Erro fatal: {e}")