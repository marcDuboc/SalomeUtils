import os
import inspect
import logging

PATH = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
LOG_FILE = os.path.join(PATH, '..' ,'log', 'contact.log')
LOG_LEVEL = logging.DEBUG
logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(message)s')