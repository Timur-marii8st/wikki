import sys
import platform
import psutil 
import subprocess
import json
import os

def get_system_info() -> str:
    """
    Возвращает базовую информацию о системе (ОС, процессор, RAM).
    Требует `pip install psutil`.
    """
    try:
        info = {
            "Операционная система": platform.system(),
            "Версия ОС": platform.version(),
            "Архитектура": platform.machine(),
            "Процессор": platform.processor(),
            "Ядра CPU": os.cpu_count(),
            "Общая RAM": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
            "Свободная RAM": f"{round(psutil.virtual_memory().available / (1024**3), 2)} GB",
            "Python версия": sys.version.splitlines()[0]
        }
        return json.dumps(info, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Ошибка при получении системной информации: {e}"

def execute_shell_command(command: str) -> str:
    """
    Выполняет команду в системной оболочке и возвращает её вывод.
    Будьте очень осторожны с этой функцией, так как она может привести к проблемам безопасности!
    Агент должен быть строго ограничен в типах команд, которые он может выполнять.

    Args:
        command (str): Команда для выполнения.

    Returns:
        str: Стандартный вывод команды или сообщение об ошибке.
    """
    try:
        # shell=True позволяет выполнять команды как в обычной оболочке (например, 'dir' или 'ls')
        # text=True декодирует вывод как текст
        # check=True вызывает исключение, если команда завершается с ошибкой
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, encoding='utf-8')
        return f"Команда выполнена успешно:\n{result.stdout.strip()}"
    except subprocess.CalledProcessError as e:
        return f"Ошибка выполнения команды '{command}':\nСтандартный вывод: {e.stdout}\nОшибка: {e.stderr}"
    except Exception as e:
        return f"Неизвестная ошибка при выполнении команды '{command}': {e}"

def get_current_working_directory() -> str:
    """
    Возвращает текущую рабочую директорию агента.
    """
    try:
        return f"Текущая рабочая директория: {os.getcwd()}"
    except Exception as e:
        return f"Ошибка при получении текущей рабочей директории: {e}"

def change_working_directory(path: str) -> str:
    """
    Изменяет текущую рабочую директорию агента.

    Args:
        path (str): Путь к директории, на которую нужно сменить.

    Returns:
        str: Сообщение об успешной смене или ошибке.
    """
    try:
        if not os.path.isdir(path):
            return f"Ошибка: Путь '{path}' не существует или не является директорией."
        os.chdir(path)
        return f"Текущая рабочая директория успешно изменена на '{os.getcwd()}'"
    except Exception as e:
        return f"Ошибка при смене рабочей директории на '{path}': {e}"