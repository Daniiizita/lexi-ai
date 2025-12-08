import logging
import sys
from pythonjsonlogger import jsonlogger
from .config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Formatter customizado para logs estruturados"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['service'] = 'lexi-translator'
        log_record['environment'] = settings.environment
        log_record['level'] = record.levelname


def setup_logger(name: str = __name__) -> logging.Logger:
    """
    Configura logger com formato JSON para integração com ELK.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level))
    
    # Handler para stdout (Docker/K8s)
    handler = logging.StreamHandler(sys.stdout)
    
    # Formato JSON
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        rename_fields={'levelname': 'level', 'asctime': 'timestamp'},
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Logger global
logger = setup_logger()