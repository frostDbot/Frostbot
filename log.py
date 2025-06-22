import logging
import traceback
from datetime import datetime
import pytz


# Configurar logging centralizado com horário de Brasília
def setup_logging():
    # Configurar formatter com horário de Brasília
    class BrasiliaFormatter(logging.Formatter):

        def formatTime(self, record, datefmt=None):
            brasilia_tz = pytz.timezone('America/Sao_Paulo')
            dt = datetime.fromtimestamp(record.created, brasilia_tz)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.strftime('%Y-%m-%d %H:%M:%S (Brasília)')

    formatter = BrasiliaFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Configurar handlers
    file_handler = logging.FileHandler('bot.log', encoding='utf-8')
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO,
                        handlers=[file_handler, console_handler])
    return logging.getLogger(__name__)


# Logger global para o módulo
logger = setup_logging()


def log_error(message, error, extra_info=None):
    """Função auxiliar para log de erros com traceback"""
    logger.error(f"{message}: {error}")
    if extra_info:
        logger.error(f"Info adicional: {extra_info}")
    logger.error(f"Traceback: {traceback.format_exc()}")


def log_warning(message, extra_info=None):
    """Função auxiliar para logs de warning"""
    logger.warning(message)
    if extra_info:
        logger.warning(f"Info adicional: {extra_info}")


def log_info(message, extra_info=None):
    """Função auxiliar para logs informativos"""
    logger.info(message)
    if extra_info:
        logger.info(f"Info adicional: {extra_info}")