import os
import inspect
import logging

# Base path
BASE_DIR = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# Logging
LOG_DIR = os.path.join(BASE_DIR, '..', 'log')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, 'debug.log')
if not os.path.exists(LOG_FILE):
    open(LOG_FILE, 'a').close()
    
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

#Gui image folder
IMG_PATH = os.path.join(BASE_DIR, 'img')