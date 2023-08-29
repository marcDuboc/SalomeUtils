# load a module 

sys.path.append('package location')
from package_name.modulename import Class, function....

# Reload a modules

from importlib import reload
reload(sys.modules['package_name.modulename'])
from package_name.modulename import Class, function....
