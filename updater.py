import requests
import os
import sys
import ctypes
from tkinter import messagebox
from settings import DATA_DIR, ensure_data_dir

def get_current_version():
    version_file = os.path.join(DATA_DIR, "version.txt")
    if os.path.exists(version_file):
        with open(version_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "0.0.0"

CURRENT_VERSION = get_current_version()

# Базовый URL для RAW-файлов (замените на свой, если нужно)
BASE_RAW_URL = "https://raw.githubusercontent.com/adalV228Side/my-launcher/refs/heads/main/"

def check_for_updates():
    try:
        response = requests.get(BASE_RAW_URL + "version.txt", timeout=5)
        if response.status_code != 200:
            return
        latest_version = response.text.strip()
        if latest_version > CURRENT_VERSION:
            if messagebox.askyesno("Обновление", f"Доступна новая версия {latest_version}.\nУстановить сейчас?"):
                perform_update()
    except Exception as e:
        print(f"Ошибка проверки обновлений: {e}")

def need_admin_for_dir(path):
    """Проверяет, нужны ли права администратора для записи в папку."""
    test_file = os.path.join(path, "write_test.tmp")
    try:
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return False
    except (PermissionError, OSError):
        return True

def perform_update():
    try:
        # Определяем тип сборки и базовые пути
        if getattr(sys, 'frozen', False):
            # Режим .exe
            is_frozen = True
            current_exe = sys.executable
            program_dir = os.path.dirname(current_exe)
            exe_name = os.path.basename(current_exe)
            files_to_download = [
                ("main.exe", exe_name),
                ("version.txt", "version.txt")
            ]
        else:
            # Режим .py (скрипт)
            is_frozen = False
            current_script = os.path.abspath(sys.argv[0])
            program_dir = os.path.dirname(current_script)
            files_to_download = [
                ("main.py", "main.py"),
                ("settings.py", "settings.py"),
                ("app_card.py", "app_card.py"),
                ("version.txt", "version.txt")
            ]

        ensure_data_dir()  # создаём папку в AppData, если её нет
        downloaded_new_files = []

        # Скачиваем все необходимые файлы
        for remote_name, local_name in files_to_download:
            # version.txt сохраняем в AppData, остальные — в папку программы
            target_dir = DATA_DIR if local_name == "version.txt" else program_dir
            local_path = os.path.join(target_dir, local_name)
            new_path = local_path + ".new"

            url = BASE_RAW_URL + remote_name
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                messagebox.showerror("Ошибка", f"Не удалось загрузить {remote_name} (код {response.status_code})")
                # Удаляем уже скачанные временные файлы
                for p, _ in downloaded_new_files:
                    try:
                        os.remove(p)
                    except:
                        pass
                return

            if len(response.content) == 0:
                messagebox.showerror("Ошибка", f"Скачанный файл {remote_name} пуст.")
                for p, _ in downloaded_new_files:
                    try:
                        os.remove(p)
                    except:
                        pass
                return

            with open(new_path, "wb") as f:
                f.write(response.content)
            downloaded_new_files.append((new_path, local_path))

        # Проверяем, нужны ли права администратора для замены файлов в program_dir
        admin_needed = is_frozen and need_admin_for_dir(program_dir)

        # Создаём bat-скрипт для замены файлов
        bat_path = os.path.join(program_dir, "updater_script.bat")
        with open(bat_path, "w", encoding="utf-8-sig") as f:
            f.write("@echo off\n")
            f.write("chcp 65001 > nul\n")
            f.write("timeout /t 2 /nobreak > nul\n")
            # Заменяем каждый скачанный файл
            for new_path, local_path in downloaded_new_files:
                f.write(f'del "{local_path}"\n')
                f.write(f'ren "{new_path}" "{os.path.basename(local_path)}"\n')
            # Для exe-версии удаляем main.py, если он есть (остался от предыдущих запусков)
            if is_frozen:
                main_py_path = os.path.join(program_dir, "main.py")
                f.write(f'if exist "{main_py_path}" del "{main_py_path}"\n')
            # Запускаем обновлённую программу
            if is_frozen:
                f.write(f'start "" "{current_exe}"\n')
            else:
                f.write(f'start "" python "{os.path.join(program_dir, "main.py")}"\n')
            f.write('del "%~f0"\n')

        # Запускаем bat-файл (с повышением прав, если требуется)
        if admin_needed:
            messagebox.showinfo("Обновление", "Для обновления требуются права администратора. Будет запущен запрос UAC.")
            ctypes.windll.shell32.ShellExecuteW(None, "runas", bat_path, None, None, 1)
        else:
            messagebox.showinfo("Обновление", "Программа будет перезагружена для применения обновления.")
            os.startfile(bat_path)

        sys.exit()  # завершаем текущий процесс

    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось обновить: {e}")