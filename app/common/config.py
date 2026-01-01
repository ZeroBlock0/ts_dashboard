import os
import sys
import json
import logging
import tempfile

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
        except json.JSONDecodeError as e:
            logging.error("配置文件损坏，已忽略: %s", e)
        except Exception as e:
            logging.error("读取配置失败: %s", e)
    return {}

def save_config(data):
    """原子写入配置，避免损坏文件。"""
    path = get_config_path()
    base_dir = os.path.dirname(path) or "."
    os.makedirs(base_dir, exist_ok=True)

    try:
        fd, tmp_path = tempfile.mkstemp(prefix="ts_config", suffix=".json", dir=base_dir)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        finally:
            os.replace(tmp_path, path)
    except Exception as e:
        logging.error("保存配置失败: %s", e)
        raise
