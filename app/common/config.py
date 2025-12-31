import os
import sys
import json

def get_config_path():
    # Nuitka specific check
    if "__compiled__" in globals():
        # Nuitka standalone/onefile
        # sys.argv[0] is the path to the executable file
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # Development
        # Assuming this file is in app/common/config.py, we need to go up two levels to get to root
        # But wait, the original code used __file__ of main.py.
        # If we want to keep config in the root folder:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
    return os.path.join(base_path, "ts_config.json")

def load_config():
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}
