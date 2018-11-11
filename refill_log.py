
import logging.config
import logging.handlers
import json

# logging.handlers.RotatingFileHandler('refiller.log', mode="a", maxBytes=10e6, backupCount=5,encoding='utf-8')

with open("log_config.json", 'r') as logging_configuration_file:
    config_dict = json.load(logging_configuration_file)

logging.config.dictConfig(config_dict)

# Log that the logger was configured
logger = logging.getLogger(__name__)
logger.info('Completed configuring logger()!')
