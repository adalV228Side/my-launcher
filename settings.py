import os
import json

APP_NAME = "MyLauncher"
DATA_DIR = os.path.join(os.getenv('APPDATA'), APP_NAME)

DEFAULT_SETTINGS = {
    "theme": "dark",
    "tiles_per_row": 3,
    "plugin_order": [],
    "favorites": []
}

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_settings_path():
    return os.path.join(DATA_DIR, "settings.json")

def load_settings():
    ensure_data_dir()
    settings_file = get_settings_path()
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                return {**DEFAULT_SETTINGS, **loaded}
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    ensure_data_dir()
    try:
        with open(get_settings_path(), "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка сохранения настроек: {e}")