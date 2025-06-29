import os
from pathlib import Path
from datetime import datetime

def list_directory_contents(path: str) -> str:
    """
    Перечисляет содержимое указанной директории (файлы и папки).

    Args:
        path (str): Путь к директории.

    Returns:
        str: Строка, содержащая список файлов и папок, или сообщение об ошибке.
    """
    try:
        if not os.path.isdir(path):
            return f"Ошибка: Путь '{path}' не является директорией."
        
        contents = os.listdir(path)
        if not contents:
            return f"Директория '{path}' пуста."
        
        output = f"Содержимое директории '{path}':\n"
        files = []
        dirs = []
        for item in contents:
            full_path = os.path.join(path, item)
            if os.path.isfile(full_path):
                files.append(item)
            elif os.path.isdir(full_path):
                dirs.append(item)
        
        if dirs:
            output += "Папки:\n" + "\n".join([f"- {d}" for d in dirs]) + "\n"
        if files:
            output += "Файлы:\n" + "\n".join([f"- {f}" for f in files]) + "\n"
            
        return output.strip()
    except Exception as e:
        return f"Ошибка при получении содержимого директории '{path}': {e}"

def search_files_by_name(root_dir: str, filename_pattern: str) -> str:
    """
    Ищет файлы и папки по названию (или части названия) в указанной директории
    и её поддиректориях. Регистр символов игнорируется.

    Args:
        root_dir (str): Корневая директория для поиска.
        filename_pattern (str): Шаблон названия (часть названия) для поиска.

    Returns:
        str: Строка со списком найденных путей или сообщением о том, что ничего не найдено.
    """
    found_paths = []
    pattern_lower = filename_pattern.lower()
    
    try:
        if not os.path.isdir(root_dir):
            return f"Ошибка: Корневая директория '{root_dir}' не существует."

        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Проверяем папки
            for dname in dirnames:
                if pattern_lower in dname.lower():
                    found_paths.append(os.path.join(dirpath, dname) + " (Папка)")
            # Проверяем файлы
            for fname in filenames:
                if pattern_lower in fname.lower():
                    found_paths.append(os.path.join(dirpath, fname) + " (Файл)")
        
        if found_paths:
            return "Найденные файлы/папки:\n" + "\n".join(found_paths)
        else:
            return f"Ничего не найдено по запросу '{filename_pattern}' в '{root_dir}'."
    except Exception as e:
        return f"Ошибка при поиске файлов/папок в '{root_dir}': {e}"

def get_file_info(filepath: str) -> str:
    """
    Получает информацию о файле: размер, время создания, время последнего изменения.

    Args:
        filepath (str): Путь к файлу.

    Returns:
        str: Строка с информацией о файле или сообщением об ошибке.
    """
    try:
        if not os.path.isfile(filepath):
            return f"Ошибка: Файл '{filepath}' не существует или не является файлом."
        
        stats = os.stat(filepath)
        size_bytes = stats.st_size
        creation_time = datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        modification_time = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        return (f"Информация о файле '{filepath}':\n"
                f"  Размер: {size_bytes} байт\n"
                f"  Создан: {creation_time}\n"
                f"  Последнее изменение: {modification_time}")
    except Exception as e:
        return f"Ошибка при получении информации о файле '{filepath}': {e}"

def create_directory(path: str) -> str:
    """
    Создает новую директорию по указанному пути.

    Args:
        path (str): Путь для создания директории.

    Returns:
        str: Сообщение об успешном создании или ошибке.
    """
    try:
        if os.path.exists(path):
            return f"Ошибка: Директория '{path}' уже существует."
        os.makedirs(path)
        return f"Директория '{path}' успешно создана."
    except Exception as e:
        return f"Ошибка при создании директории '{path}': {e}"

def delete_path(path: str, is_directory: bool = False) -> str:
    """
    Удаляет файл или пустую директорию. Будьте осторожны при использовании!

    """
    try:
        if not os.path.exists(path):
            return f"Ошибка: Путь '{path}' не существует."

        if is_directory:
            if not os.path.isdir(path):
                return f"Ошибка: '{path}' не является директорией."
            if os.listdir(path):
                return f"Ошибка: Директория '{path}' не пуста. Используйте 'delete_non_empty_directory' для непустых папок."
            os.rmdir(path)
            return f"Пустая директория '{path}' успешно удалена."
        else:
            if not os.path.isfile(path):
                return f"Ошибка: '{path}' не является файлом."
            os.remove(path)
            return f"Файл '{path}' успешно удален."
    except Exception as e:
        return f"Ошибка при удалении '{path}': {e}"

import shutil

def delete_non_empty_directory(path: str) -> str:
    """
    Удаляет директорию со всем её содержимым (файлами и поддиректориями).

    """
    try:
        if not os.path.isdir(path):
            return f"Ошибка: Путь '{path}' не является директорией."
        
        # Запрос подтверждения (этот механизм может быть реализован в агенте)
        # Агент должен быть явно запрограммирован на подтверждение критических действий.
        # В рамках самой функции это простое удаление.
        shutil.rmtree(path)
        return f"Директория '{path}' и всё её содержимое успешно удалены."
    except Exception as e:
        return f"Ошибка при удалении непустой директории '{path}': {e}"

def rename_path(old_path: str, new_name: str) -> str:
    """
    Переименовывает файл или директорию.

    Args:
        old_path (str): Старый путь к файлу или директории.
        new_name (str): Новое название (только название, не полный путь).

    Returns:
        str: Сообщение об успешном переименовании или ошибке.
    """
    try:
        if not os.path.exists(old_path):
            return f"Ошибка: Путь '{old_path}' не существует."
        
        directory = os.path.dirname(old_path)
        new_path = os.path.join(directory, new_name)

        if os.path.exists(new_path):
            return f"Ошибка: Путь '{new_path}' уже существует."
            
        os.rename(old_path, new_path)
        return f"'{old_path}' успешно переименован в '{new_path}'."
    except Exception as e:
        return f"Ошибка при переименовании '{old_path}': {e}"

def move_path(source_path: str, destination_path: str) -> str:
    """
    Перемещает файл или директорию из одного места в другое.

    Args:
        source_path (str): Путь к исходному файлу или директории.
        destination_path (str): Путь к целевой директории или новое имя пути.

    Returns:
        str: Сообщение об успешном перемещении или ошибке.
    """
    try:
        if not os.path.exists(source_path):
            return f"Ошибка: Исходный путь '{source_path}' не существует."
        
        # Если destination_path - существующая директория, то перемещаем в нее
        if os.path.isdir(destination_path):
            final_dest = os.path.join(destination_path, os.path.basename(source_path))
        else: # Иначе считаем, что destination_path - это новый полный путь/имя
            final_dest = destination_path

        if os.path.exists(final_dest) and final_dest != source_path:
             return f"Ошибка: Целевой путь '{final_dest}' уже существует."

        shutil.move(source_path, final_dest)
        return f"'{source_path}' успешно перемещен в '{final_dest}'."
    except Exception as e:
        return f"Ошибка при перемещении '{source_path}': {e}"

def copy_path(source_path: str, destination_path: str) -> str:
    """
    Копирует файл или директорию. Для директорий копирует все содержимое.

    Args:
        source_path (str): Путь к исходному файлу или директории.
        destination_path (str): Путь к целевой директории или новое имя пути.

    Returns:
        str: Сообщение об успешном копировании или ошибке.
    """
    try:
        if not os.path.exists(source_path):
            return f"Ошибка: Исходный путь '{source_path}' не существует."
        
        if os.path.isfile(source_path):
            shutil.copy2(source_path, destination_path) # copy2 сохраняет метаданные
            return f"Файл '{source_path}' успешно скопирован в '{destination_path}'."
        elif os.path.isdir(source_path):
            # Если целевой путь уже существует и это директория, копируем в нее
            if os.path.exists(destination_path) and os.path.isdir(destination_path):
                dest_dir = os.path.join(destination_path, os.path.basename(source_path))
                if os.path.exists(dest_dir):
                     return f"Ошибка: Директория '{dest_dir}' уже существует в целевом пути."
                shutil.copytree(source_path, dest_dir)
                return f"Директория '{source_path}' успешно скопирована в '{dest_dir}'."
            else: # Иначе, destination_path - это новый путь для копии директории
                shutil.copytree(source_path, destination_path)
                return f"Директория '{source_path}' успешно скопирована в '{destination_path}'."
        else:
            return f"Ошибка: '{source_path}' не является ни файлом, ни директорией."
    except Exception as e:
        return f"Ошибка при копировании '{source_path}': {e}"

def get_drive_info(drive_path: str) -> str:
    """
    Возвращает информацию о свободном и общем пространстве на диске.
    Работает для Windows (C:\\), Unix-like (/), или монтированных точек.

    Args:
        drive_path (str): Путь к диску или смонтированной точке (например, 'C:\\' или '/').

    Returns:
        str: Информация о диске или сообщение об ошибке.
    """
    try:
        if not os.path.exists(drive_path):
            return f"Ошибка: Путь '{drive_path}' не существует."

        total, used, free = shutil.disk_usage(drive_path)
        
        # Преобразование байтов в ГБ для читаемости
        total_gb = total / (1024**3)
        used_gb = used / (1024**3)
        free_gb = free / (1024**3)

        return (f"Информация о диске '{drive_path}':\n"
                f"  Общий объем: {total_gb:.2f} ГБ\n"
                f"  Использовано: {used_gb:.2f} ГБ\n"
                f"  Свободно: {free_gb:.2f} ГБ")
    except Exception as e:
        return f"Ошибка при получении информации о диске '{drive_path}': {e}"