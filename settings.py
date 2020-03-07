import logging


TEMPLATE_PATH = "./report.html"

ERROR_THRESHOLD = 0.5

CONFIG = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

logging.basicConfig(
     filename=CONFIG.get('LOGGING_DIR'),
     level=logging.INFO, 
     format= '[%(asctime)s] %(levelname).1s %(message)s',
     datefmt='%Y.%m.%d %H:%M:%S'
 )