import requests
import os
import sys
from tkinter import messagebox

VERSION_FILE = "version.txt"

def get_current_version():
    """Читает версию из version.txt, если файла нет — возвращает 0.0.0"""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "0.0.0"

CURRENT_VERSION = get_current_version()

# Прямые ссылки на файлы в репозитории (используйте свои)
BASE_RAW_URL = "https://raw.githubusercontent.com/adalV228Side/my-launcher/refs/heads/main/"
VERSION_URL = BASE_RAW_URL + "version.txt"
# Список файлов, которые нужно обновлять (можно добавить updater.py, если он тоже меняется)
FILES_TO_UPDATE = ["main.py", "version.txt"]  # при необходимости добавьте "updater.py"

def check_for_updates():
    try:
        response = requests.get(VERSION_URL, timeout=5)
        if response.status_code != 200:
            return
        latest_version = response.text.strip()

        # Простое сравнение строк (можно заменить на более умное)
        if latest_version > CURRENT_VERSION:
            if messagebox.askyesno("Обновление", f"Доступна новая версия {latest_version}.\nУстановить сейчас?"):
                perform_update()
    except Exception as e:
        print(f"Ошибка проверки обновлений: {e}")

def perform_update():
    try:
        # Определяем базовую директорию (где лежит программа)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        downloaded = []  # список скачанных временных файлов

        # Скачиваем все необходимые файлы
        for filename in FILES_TO_UPDATE:
            url = BASE_RAW_URL + filename
            local_path = os.path.join(base_dir, filename)
            new_path = local_path + ".new"

            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                messagebox.showerror("Ошибка", f"Не удалось загрузить {filename}")
                # Удаляем уже скачанные временные файлы
                for f in downloaded:
                    try:
                        os.remove(f)
                    except:
                        pass
                return

            with open(new_path, "wb") as f:
                f.write(response.content)
            downloaded.append(new_path)

        # Создаём bat-скрипт для замены файлов
        bat_file = os.path.join(base_dir, "updater_script.bat")
        with open(bat_file, "w", encoding="utf-8-sig") as f:
            f.write("@echo off\n")
            f.write("chcp 65001 > nul\n")
            f.write("timeout /t 2 /nobreak > nul\n")
            for filename in FILES_TO_UPDATE:
                local_path = os.path.join(base_dir, filename)
                new_path = local_path + ".new"
                f.write(f'del "{local_path}"\n')
                f.write(f'ren "{new_path}" "{filename}"\n')
            # Запускаем main.py (или main.exe, если собрано в exe)
            main_path = os.path.join(base_dir, "main.py")
            f.write(f'start "" "{main_path}"\n')
            f.write('del "%~f0"\n')

        messagebox.showinfo("Обновление", "Программа будет перезагружена для применения изменений.")
        os.startfile(bat_file)
        sys.exit()

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось обновить: {e}")