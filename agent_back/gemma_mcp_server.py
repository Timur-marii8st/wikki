import asyncio
import os
import sys
import shutil
import re
import fnmatch
from collections import deque
import zipfile
import aiofiles

from typing import Dict, List, Optional, Any
from fastmcp import FastMCP
import aiofiles

from document_editing_tools import (create_pdf_from_text, merge_pdfs,
                                    extract_pdf_pages, create_docx, add_text_to_docx, replace_text_in_docx, create_pptx,
                                    add_slide_to_pptx, create_xlsx, write_to_excel_cell, read_from_excel_cell, 
                                    write_data_to_excel_range)

# Print startup message
print("[fastfs-mcp] Server starting...", file=sys.stderr, flush=True)

# Set the default workspace directory to the parent directory
WORKSPACE_DIR = os.path.join(os.getcwd(), 'workspace')

if os.path.exists(WORKSPACE_DIR):
    os.chdir(WORKSPACE_DIR)
    print(f"[fastfs-mcp] Working directory set to {WORKSPACE_DIR}", file=sys.stderr, flush=True)
else:
    current_dir = os.getcwd()
    print(f"[fastfs-mcp] Warning: {WORKSPACE_DIR} not found, using current directory: {current_dir}", file=sys.stderr, flush=True)

# Initialize the MCP server
mcp = FastMCP(name="fastfs-mcp")

# Define tool schemas with proper typing and input validation
@mcp.tool(description="List files and directories at a given path.")
async def ls(path: str = ".") -> Dict[str, Any]:
    try:
        print(f"[DEBUG] ls called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        return {"files": os.listdir(path)}
    except Exception as e:
        print(f"[ERROR] ls failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Print the current working directory.")
async def pwd() -> Dict[str, Any]:
    try:
        print(f"[DEBUG] pwd called", file=sys.stderr, flush=True)
        return {"cwd": os.getcwd()}
    except Exception as e:
        print(f"[ERROR] pwd failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Change the current working directory.")
async def cd(path: str) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] cd called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        if not os.path.isdir(path):
            return {"error": f"'{path}' is not a directory"}
        os.chdir(path)
        return {"cwd": os.getcwd()}
    except Exception as e:
        print(f"[ERROR] cd failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Read the contents of a file.")
async def read(path: str) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] read called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"File '{path}' does not exist"}
        if not os.path.isfile(path):
            return {"error": f"'{path}' is not a file"}
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            content = await f.read()
        return {"content": content}
    except Exception as e:
        print(f"[ERROR] read failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Write contents to a file.")
async def write(path: str, content: str = "") -> Dict[str, Any]:
    try:
        print(f"[DEBUG] write called with path: {path}", file=sys.stderr, flush=True)
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(content)
        return {"success": True, "path": path}
    except Exception as e:
        print(f"[ERROR] write failed: {str(e)}", file=sys.stderr, flush=True)
        return {"success": False, "error": str(e)}

@mcp.tool(description="Search for a pattern in a file.")
async def grep(pattern: str, path: str) -> Dict[str, Any]:
    try:
        if not os.path.exists(path):
            return {"error": f"File '{path}' does not exist"}
        if not os.path.isfile(path):
            return {"error": f"'{path}' is not a file"}

        matches = []
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            line_num = 0
            async for line in f:
                line_num += 1
                if pattern in line:
                    matches.append(f"{line_num}:{line.strip()}")

        return {"matches": matches}

    except Exception as e:
        return {"error": str(e)}

@mcp.tool(description="Perform stream editing on a file, similar to 'sed'. Supports find and replace using regex.")
async def sed(script: str, path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"error": f"File '{path}' does not exist"}
    if not os.path.isfile(path):
        return {"error": f"'{path}' is not a file"}

    # sed-подобная логика: предполагаем простой 's/pattern/replacement/flags'
    match = re.match(r's/(.*?)/(.*?)/(.*)?', script)
    if not match:
        return {"error": "Unsupported sed script format. Only 's/pattern/replacement/flags' is supported."}

    pattern_str = match.group(1)
    replacement_str = match.group(2)
    flags_str = match.group(3) or ''

    re_flags = 0
    if 'i' in flags_str:
        re_flags |= re.IGNORECASE
    if 'g' in flags_str:
        pass

    try:
        temp_path = f"{path}.tmp"
        async with aiofiles.open(path, 'r', encoding='utf-8') as infile, \
                   aiofiles.open(temp_path, 'w', encoding='utf-8') as outfile:
            async for line in infile:
                # Если флаг 'g' присутствует, заменяем все вхождения
                # Иначе, re.sub заменяет только первое вхождение по умолчанию
                new_line = re.sub(pattern_str, replacement_str, line, flags=re_flags)
                await outfile.write(new_line)

        os.replace(temp_path, path) # Атомарная замена файла

        return {"output": f"File '{path}' processed successfully."}
    except re.error as re_err:
        return {"error": f"Regular expression error: {re_err}"}
    except Exception as e:
        # Удалить временный файл, если произошла ошибка
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"error": str(e)}


@mcp.tool(description="Process file content, similar to 'gawk'. Executing a Python script for each line.")
async def gawk(script: str, path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"error": f"File '{path}' does not exist"}
    if not os.path.isfile(path):
        return {"error": f"'{path}' is not a file"}

    results = []
    try:
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            line_num = 0
            async for line_content in f:
                line_num += 1
                # Создаем локальное окружение для выполнения скрипта
                # 'line' - текущая строка, 'NR' - номер строки
                local_vars = {'line': line_content.strip(), 'NR': line_num, 'result': None}
                
                # Выполняем скрипт. Скрипт должен установить 'result'
                exec(script, {}, local_vars) 
                
                if local_vars.get('result') is not None:
                    results.append(str(local_vars['result'])) # Собираем результаты, если скрипт их генерирует
        
        return {"output": "\n".join(results)}
    except Exception as e:
        return {"error": f"Error executing gawk-like script: {str(e)}"}

# ===== ADDITIONAL FILESYSTEM TOOLS =====

@mcp.tool(description="Display file status (metadata).")
def stat(path: str) -> Dict[str, Any]:
    """Display file status and metadata."""
    import stat
    try:
        print(f"[DEBUG] stat called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        
        st = os.stat(path)
        result = {
            "path": path,
            "size": st.st_size,
            "mode": stat.filemode(st.st_mode),
            "mode_octal": oct(st.st_mode)[-3:],
            "inode": st.st_ino,
            "device": st.st_dev,
            "links": st.st_nlink,
            "uid": st.st_uid,
            "gid": st.st_gid,
            "access_time": st.st_atime,
            "modification_time": st.st_mtime,
            "change_time": st.st_ctime,
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
            "is_link": os.path.islink(path)
        }
        return result
    except Exception as e:
        print(f"[ERROR] stat failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Find files by pattern.")
async def find(path: str = ".", pattern: str = "*", file_type: str = "", max_depth: int = -1) -> Dict[str, Any]:

    if not os.path.exists(path):
        return {"error": f"Path '{path}' does not exist"}

    if not os.path.isdir(path):
        return {"error": f"Path '{path}' is not a directory"}

    found_files = []
    
    # Нормализуем путь для os.walk
    start_path = os.path.abspath(path)
    
    # Определяем тип файла для проверки
    target_is_file = False
    target_is_dir = False
    target_is_link = False
    
    if file_type:
        if file_type == 'f':
            target_is_file = True
        elif file_type == 'd':
            target_is_dir = True
        elif file_type == 'l':
            target_is_link = True
        else:
            # Для 'b', 'c', 'p', 's' (блочные, символьные устройства, именованные каналы, сокеты)
            # в Python нет прямого кроссплатформенного аналога os.path.isblockdevice и т.п.
            return {"error": f"Invalid or unsupported file type '{file_type}' for cross-platform find. Supported: 'f' (file), 'd' (directory), 'l' (symlink)."}

    try:
        for root, dirs, files in os.walk(start_path):
            current_depth = root.count(os.sep) - start_path.count(os.sep)
            
            if max_depth != -1 and current_depth >= max_depth:
                # Очищаем dirs, чтобы os.walk не заходил в поддиректории
                dirs[:] = [] 
                continue # Продолжаем обрабатывать файлы в текущей директории, но не ее поддиректории

            # Проверяем файлы
            for name in files:
                full_path = os.path.join(root, name)
                if fnmatch.fnmatch(name, pattern):
                    if not file_type or target_is_file:
                        found_files.append(full_path)
            
            for name in dirs:
                full_path = os.path.join(root, name)
                # Проверяем паттерн для имени директории, если он подходит
                if fnmatch.fnmatch(name, pattern):
                    if target_is_dir:
                        found_files.append(full_path)

            # Дополнительная проверка на симлинки, если они явно запрашиваются
            if target_is_link:
                # os.listdir() может быть относительно дорогим, если много директорий
                # Но для точной обработки symlink, это необходимо.
                for item_name in os.listdir(root):
                    item_full_path = os.path.join(root, item_name)
                    if os.path.islink(item_full_path) and fnmatch.fnmatch(item_name, pattern):
                        # Убедимся, что мы не добавляем уже найденные файлы/директории,
                        # если симлинк указывает на них, но запрос был на симлинк
                        if item_full_path not in found_files:
                            found_files.append(item_full_path)

        return {"files": found_files}

    except Exception as e:
        return {"error": str(e)}

@mcp.tool(description="Copy files or directories.")
def cp(source: str, destination: str, recursive: bool = False) -> str:
    """Copy files or directories."""
    try:
        print(f"[DEBUG] cp called with source: {source}, destination: {destination}", file=sys.stderr, flush=True)
        if not os.path.exists(source):
            return f"Error: Source '{source}' does not exist"
        
        if os.path.isdir(source) and not recursive:
            return f"Error: Source '{source}' is a directory, use recursive=True to copy directories"
        
        if recursive:
            shutil.copytree(source, destination)
            return f"Successfully copied directory '{source}' to '{destination}'"
        else:
            shutil.copy2(source, destination)
            return f"Successfully copied file '{source}' to '{destination}'"
    except Exception as e:
        print(f"[ERROR] cp failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Move or rename files or directories.")
def mv(source: str, destination: str) -> str:
    """Move or rename files or directories."""
    try:
        print(f"[DEBUG] mv called with source: {source}, destination: {destination}", file=sys.stderr, flush=True)
        if not os.path.exists(source):
            return f"Error: Source '{source}' does not exist"
        
        shutil.move(source, destination)
        return f"Successfully moved '{source}' to '{destination}'"
    except Exception as e:
        print(f"[ERROR] mv failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Remove files or directories.")
def rm(path: str, recursive: bool = False, force: bool = False) -> str:
    """Remove files or directories."""
    try:
        print(f"[DEBUG] rm called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            if force:
                return f"Warning: Path '{path}' does not exist, nothing removed"
            else:
                return f"Error: Path '{path}' does not exist"
        
        if os.path.isdir(path):
            if not recursive:
                return f"Error: '{path}' is a directory, use recursive=True to remove directories"
            shutil.rmtree(path)
            return f"Successfully removed directory '{path}'"
        else:
            os.remove(path)
            return f"Successfully removed file '{path}'"
    except Exception as e:
        print(f"[ERROR] rm failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Create a new empty file or update its timestamp.")
def touch(path: str) -> str:
    """Create a new empty file or update its timestamp."""
    try:
        print(f"[DEBUG] touch called with path: {path}", file=sys.stderr, flush=True)
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(path, 'a'):
            os.utime(path, None)
        return f"Successfully touched '{path}'"
    except Exception as e:
        print(f"[ERROR] touch failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Create a new directory.")
def mkdir(path: str, parents: bool = False) -> str:
    """Create a new directory."""
    try:
        print(f"[DEBUG] mkdir called with path: {path}", file=sys.stderr, flush=True)
        if os.path.exists(path):
            return f"Error: Path '{path}' already exists"
        
        if parents:
            os.makedirs(path)
        else:
            os.mkdir(path)
        return f"Successfully created directory '{path}'"
    except Exception as e:
        print(f"[ERROR] mkdir failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Display the first part of files.")
def head(path: str, lines: int = 10) -> str:
    """Display the first part of files."""
    try:
        print(f"[DEBUG] head called with path: {path}, lines: {lines}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file"
        
        with open(path, 'r', encoding='utf-8') as f:
            result = ''.join(f.readline() for _ in range(lines))
            
        return result
    except Exception as e:
        print(f"[ERROR] head failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Display the last part of files.")
async def tail(path: str, lines: int = 10) -> Dict[str, Any]:
    print(f"[DEBUG] tail called with path: {path}, lines: {lines}", file=sys.stderr, flush=True)

    if not os.path.exists(path):
        return {"error": f"File '{path}' does not exist"}
    if not os.path.isfile(path):
        return {"error": f"'{path}' is not a file"}
    if lines <= 0:
        return {"error": "Number of lines must be a positive integer."}

    try:
        # Используем deque (двустороннюю очередь) для эффективного хранения последних N строк.
        last_n_lines = deque(maxlen=lines)

        async with aiofiles.open(path, 'r', encoding='utf-8', errors='ignore') as f:
            async for line in f:
                last_n_lines.append(line.strip())

        # Собираем строки из deque в одну строку, разделяя их символом новой строки.
        output_content = "\n".join(last_n_lines)

        return {"output": output_content}

    except Exception as e:
        print(f"[ERROR] tail failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

# ===== TEXT MANIPULATION TOOLS =====

@mcp.tool(description="Split a file into smaller parts.")
async def split(path: str, prefix: str = 'x', lines: Optional[int] = None, bytes_size: Optional[str] = None) -> Dict[str, Any]:
    # print(f"[DEBUG] split called with path: {path}, prefix: {prefix}, lines: {lines}, bytes_size: {bytes_size}", file=sys.stderr, flush=True)

    if not os.path.exists(path):
        return {"error": f"File '{path}' does not exist"}
    if not os.path.isfile(path):
        return {"error": f"'{path}' is not a file"}

    # Проверка, что указан только один способ разбиения
    if lines is not None and bytes_size is not None:
        return {"error": "Cannot specify both 'lines' and 'bytes_size'. Choose one."}
    if lines is None and bytes_size is None:
        return {"error": "Must specify either 'lines' or 'bytes_size'."}
    
    # Валидация 'lines'
    if lines is not None and (not isinstance(lines, int) or lines <= 0):
        return {"error": "'lines' must be a positive integer."}

    # Валидация и парсинг 'bytes_size'
    parsed_bytes_size = 0
    if bytes_size is not None:
        try:
            bytes_size_lower = bytes_size.lower()
            if bytes_size_lower.endswith('b'): # 512-byte blocks
                value = int(bytes_size_lower[:-1])
                parsed_bytes_size = value * 512
            elif bytes_size_lower.endswith('k'): # 1K blocks
                value = int(bytes_size_lower[:-1])
                parsed_bytes_size = value * 1024
            elif bytes_size_lower.endswith('m'): # 1M blocks
                value = int(bytes_size_lower[:-1])
                parsed_bytes_size = value * 1024**2
            elif bytes_size_lower.endswith('g'): # 1G blocks
                value = int(bytes_size_lower[:-1])
                parsed_bytes_size = value * 1024**3
            elif bytes_size_lower.endswith('t'):
                value = int(bytes_size_lower[:-1])
                parsed_bytes_size = value * 1024**4
            elif bytes_size_lower.endswith('p'):
                value = int(bytes_size_lower[:-1])
                parsed_bytes_size = value * 1024**5
            elif bytes_size_lower.endswith('e'):
                value = int(bytes_size_lower[:-1])
                parsed_bytes_size = value * 1024**6
            elif bytes_size_lower.endswith('z'):
                value = int(bytes_size_lower[:-1])
                parsed_bytes_size = value * 1024**7
            elif bytes_size_lower.endswith('y'):
                value = int(bytes_size_lower[:-1])
                parsed_bytes_size = value * 1024**8
            else: # Если нет суффикса, считаем байты напрямую
                parsed_bytes_size = int(bytes_size)

            if parsed_bytes_size <= 0:
                return {"error": "'bytes_size' must be a positive number."}
        except ValueError:
            return {"error": f"Invalid 'bytes_size' format: '{bytes_size}'. Use integer or with suffixes (e.g., '10k', '5m')."}


    output_files = []
    file_part_index = 0

    try:
        if lines is not None:
            # Разбиение по количеству строк
            current_line_count = 0
            output_file = None
            
            async with aiofiles.open(path, 'r', encoding='utf-8', errors='ignore') as infile:
                async for line in infile:
                    if current_line_count == 0:
                        # Закрыть предыдущий файл, если он был
                        if output_file:
                            await output_file.close()
                        
                        # Формируем имя нового выходного файла
                        part_filename = f"{prefix}{str(file_part_index).zfill(2)}" # x00, x01, x02...
                        output_files.append(part_filename)
                        output_file = await aiofiles.open(part_filename, 'w', encoding='utf-8')
                        file_part_index += 1

                    await output_file.write(line)
                    current_line_count += 1

                    if current_line_count >= lines:
                        current_line_count = 0 # Сбрасываем счетчик для нового файла
            
            # Убедиться, что последний файл закрыт
            if output_file:
                await output_file.close()

        elif bytes_size is not None:
            # Разбиение по размеру в байтах
            current_bytes_written = 0
            output_file = None

            async with aiofiles.open(path, 'rb') as infile: # Читаем в бинарном режиме
                while True:
                    if current_bytes_written == 0:
                        # Закрыть предыдущий файл, если он был
                        if output_file:
                            await output_file.close()

                        part_filename = f"{prefix}{str(file_part_index).zfill(2)}"
                        output_files.append(part_filename)
                        output_file = await aiofiles.open(part_filename, 'wb') # Пишем в бинарном режиме
                        file_part_index += 1

                    chunk_size = min(parsed_bytes_size - current_bytes_written, 4096) # Читаем чанками
                    if chunk_size <= 0: # Если текущий файл уже заполнен
                        current_bytes_written = 0
                        continue # Начнем новый файл на следующей итерации

                    chunk = await infile.read(chunk_size)
                    if not chunk: # Достигнут конец исходного файла
                        break

                    await output_file.write(chunk)
                    current_bytes_written += len(chunk)

                    if current_bytes_written >= parsed_bytes_size:
                        current_bytes_written = 0 # Сбрасываем счетчик для нового файла
            
            # Убедиться, что последний файл закрыт
            if output_file:
                await output_file.close()

        return {"success": True, "parts": len(output_files), "files": output_files}

    except Exception as e:
        print(f"[ERROR] split failed: {str(e)}", file=sys.stderr, flush=True)
        # Попытка удалить неполные части в случае ошибки
        for f in output_files:
            if os.path.exists(f):
                os.remove(f)
        return {"error": str(e)}

# ===== ARCHIVE & COMPRESSION TOOLS =====

@mcp.tool(description="Create or extract zip archives.")
async def zip(operation: str, archive_file: str, files: Optional[List[str]] = None, options: str = "") -> Dict[str, Any]:
    print(f"[DEBUG] zip called with operation: {operation}, archive: {archive_file}, files: {files}, options: {options}", file=sys.stderr, flush=True)

    if operation not in ["create", "extract"]:
        return {"error": f"Invalid operation '{operation}'. Use 'create' or 'extract'."}

    try:
        if operation == "create":
            if not files:
                return {"error": "No files specified for zip creation"}

            try:
                def _create_zip_sync():
                    with zipfile.ZipFile(archive_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                        for file_path in files:
                            if not os.path.exists(file_path):
                                raise FileNotFoundError(f"File to add not found: {file_path}")
                            # arcname - имя файла внутри архива. По умолчанию - базовое имя файла.
                            # Если нужно сохранять структуру директорий, можно использовать os.path.relpath
                            # Например: zf.write(file_path, arcname=os.path.relpath(file_path, start_path_for_relativity))
                            zf.write(file_path, arcname=os.path.basename(file_path))
                    return {"output": f"Archive '{archive_file}' created successfully."}

                result = await asyncio.to_thread(_create_zip_sync)
                return result

            except FileNotFoundError as e:
                return {"error": str(e)}
            except Exception as e:
                return {"error": f"Error creating zip archive: {str(e)}"}

        elif operation == "extract":
            if not os.path.exists(archive_file):
                return {"error": f"Archive '{archive_file}' does not exist"}
            if not zipfile.is_zipfile(archive_file):
                return {"error": f"'{archive_file}' is not a valid zip file."}

            # Извлечение происходит в текущую директорию или в указанную опциями.
            # Для простоты, здесь извлекаем в текущую директорию.
            # Если нужны опции для указания директории, их нужно будет парсить.
            extract_path = "." # По умолчанию извлекаем в текущую директорию.
            
            # Парсинг опций, если они указывают путь для извлечения.
            # Это пример того, как можно было бы обрабатывать опции.
            # В реальной реализации вам нужно определить, какие опции вы хотите поддерживать.
            if options:
                # Пример: "-d /path/to/extract"
                options_list = options.split()
                if "-d" in options_list:
                    try:
                        idx = options_list.index("-d")
                        if idx + 1 < len(options_list):
                            extract_path = options_list[idx + 1]
                            if not os.path.isdir(extract_path):
                                os.makedirs(extract_path, exist_ok=True) 
                        else:
                            return {"error": "Missing directory path for -d option."}
                    except ValueError:
                        pass
            try:
                def _extract_zip_sync():
                    with zipfile.ZipFile(archive_file, 'r') as zf:
                        zf.extractall(path=extract_path)
                    return {"output": f"Archive '{archive_file}' extracted successfully to '{extract_path}'."}

                result = await asyncio.to_thread(_extract_zip_sync)
                return result

            except Exception as e:
                return {"error": f"Error extracting zip archive: {str(e)}"}

    except Exception as e:
        print(f"[ERROR] zip failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}


# ===== TOOLS FOR WORKING WITH PDF =====

@mcp.tool(description="Creates a new PDF document from the given text.")
async def tool_create_pdf(file_path: str, text_content: str, title: str = "Document", author: str = "AI Agent") -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_create_pdf for file '{file_path}'", file=sys.stderr)
    return await create_pdf_from_text(file_path, text_content, title, author)

@mcp.tool(description="Merges several PDF files into one.")
async def tool_merge_pdfs(output_path: str, input_paths: List[str]) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_merge_pdfs for output '{output_path}'", file=sys.stderr)
    return await merge_pdfs(output_path, *input_paths)

@mcp.tool(description="Extracts specified pages from a PDF file.")
async def tool_extract_pdf_pages(input_path: str, output_path: str, pages_to_extract: List[int]) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_extract_pdf_pages from '{input_path}'", file=sys.stderr)
    return await extract_pdf_pages(input_path, output_path, pages_to_extract)

# ===== TOOLS FOR WORKING WITH WORD (DOCX) =====

@mcp.tool(description="Creates a new Word document (.docx).")
async def tool_create_docx(file_path: str, content: str = "") -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_create_docx for file '{file_path}'", file=sys.stderr)
    return await create_docx(file_path, content)

@mcp.tool(description="Adds a new paragraph to a DOCX document.")
async def tool_add_text_to_docx(file_path: str, text_to_add: str) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_add_text_to_docx for file '{file_path}'", file=sys.stderr)
    return await add_text_to_docx(file_path, text_to_add)

@mcp.tool(description="Replaces text in a DOCX document.")
async def tool_replace_text_in_docx(file_path: str, old_text: str, new_text: str) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_replace_text_in_docx for file '{file_path}'", file=sys.stderr)
    return await replace_text_in_docx(file_path, old_text, new_text)

# ===== TOOLS FOR WORKING WITH POWERPOINT (PPTX) =====

@mcp.tool(description="Creates a new PowerPoint presentation (.pptx).")
async def tool_create_pptx(file_path: str, title: str = "", subtitle: str = "") -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_create_pptx for file '{file_path}'", file=sys.stderr)
    return await create_pptx(file_path, title, subtitle)

@mcp.tool(description="Adds a new slide to a PPTX presentation.")
async def tool_add_slide_to_pptx(file_path: str, layout_index: int = 1, title: str = "", content: str = "") -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_add_slide_to_pptx for file '{file_path}'", file=sys.stderr)
    return await add_slide_to_pptx(file_path, layout_index, title, content)

# ===== TOOLS FOR WORKING WITH EXCEL (XLSX) =====

@mcp.tool(description="Creates a new Excel document (.xlsx).")
async def tool_create_xlsx(file_path: str, sheet_name: str = "Sheet1") -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_create_xlsx for file '{file_path}'", file=sys.stderr)
    return await create_xlsx(file_path, sheet_name)

@mcp.tool(description="Writes a value to an Excel cell.")
async def tool_write_to_excel_cell(file_path: str, sheet_name: str, cell_address: str, value: Any) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_write_to_excel_cell to cell {cell_address}", file=sys.stderr)
    return await write_to_excel_cell(file_path, sheet_name, cell_address, value)

@mcp.tool(description="Reads a value from an Excel cell.")
async def tool_read_from_excel_cell(file_path: str, sheet_name: str, cell_address: str) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_read_from_excel_cell from cell {cell_address}", file=sys.stderr)
    return await read_from_excel_cell(file_path, sheet_name, cell_address)

@mcp.tool(description="Writes a 2D array of data to a range of Excel cells.")
async def tool_write_data_to_excel_range(file_path: str, sheet_name: str, start_cell: str, data: List[List[Any]]) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_write_data_to_excel_range starting from {start_cell}", file=sys.stderr)
    return await write_data_to_excel_range(file_path, sheet_name, start_cell, data)

