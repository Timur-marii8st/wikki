import os
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from langchain_community.llms import Ollama

# Импортируем наши функции (provereno)
from filesystem_tools import (
    list_directory_contents, search_files_by_name, get_file_info,
    create_directory, delete_path, delete_non_empty_directory,
    rename_path, move_path, copy_path, get_drive_info
)

from document_readers import (read_document, read_docx, read_pptx, read_plain_text, read_xlsx)
from system_tools import (
    get_system_info, execute_shell_command, 
    get_current_working_directory, change_working_directory
)

from document_editing_tools import (create_pdf_from_text, create_docx,
                                    create_pptx, create_xlsx, merge_pdfs, extract_pdf_pages, add_sheet_to_xlsx,
                                    add_slide_to_pptx, add_text_to_docx, replace_text_in_docx,
                                    update_slide_text_by_index, delete_paragraph_from_docx, write_data_to_excel_range,
                                    write_to_excel_cell, read_from_excel_cell)

# 1. Определ LLM
llm = Ollama(model="gemma3:4b")

# 2. Превратите функции в LangChain Tools
tools = [
    Tool(
        name="create_pdf_from_text",
        func=create_pdf_from_text,
        description="Создает PDF-документ из текстового контента. Принимает 'file_path' (строка), 'text_content' (строка) и 'title' (строка, по умолчанию 'Документ')."
    ),
    Tool(
        name="list_directory_contents",
        func=list_directory_contents,
        description="Перечисляет содержимое (файлы и папки) указанной директории. Принимает аргумент 'path' (строка)."
    ),
    Tool(
        name="search_files_by_name",
        func=search_files_by_name,
        description="Ищет файлы и папки по части названия (без учета регистра) в указанной директории и её поддиректориях. Принимает 'root_dir' (строка) и 'filename_pattern' (строка)."
    ),
    Tool(
        name="get_file_info",
        func=get_file_info,
        description="Получает размер файла, время создания и время последнего изменения. Принимает 'filepath' (строка)."
    ),
    Tool(
        name="create_directory",
        func=create_directory,
        description="Создает новую директорию. Принимает 'path' (строка)."
    ),
    Tool(
        name="delete_path",
        func=delete_path,
        description="Удаляет файл или ПУСТУЮ директорию. ИСПОЛЬЗУЙТЕ С ОСТОРОЖНОСТЬЮ! Принимает 'path' (строка) и 'is_directory' (булево, по умолчанию False)."
    ),
    Tool(
        name="delete_non_empty_directory",
        func=delete_non_empty_directory,
        description="Удаляет директорию СО ВСЕМ ЕЁ СОДЕРЖИМЫМ. ИСПОЛЬЗУЙТЕ С ЧРЕЗВЫЧАЙНОЙ ОСТОРОЖНОСТЬЮ! Принимает 'path' (строка)."
    ),
    Tool(
        name="rename_path",
        func=rename_path,
        description="Переименовывает файл или директорию. Принимает 'old_path' (строка) и 'new_name' (строка, только новое название, не полный путь)."
    ),
    Tool(
        name="move_path",
        func=move_path,
        description="Перемещает файл или директорию. Принимает 'source_path' (строка) и 'destination_path' (строка)."
    ),
    Tool(
        name="copy_path",
        func=copy_path,
        description="Копирует файл или директорию. Принимает 'source_path' (строка) и 'destination_path' (строка)."
    ),
    Tool(
        name="get_drive_info",
        func=get_drive_info,
        description="Получает информацию о свободном и общем пространстве на диске. Принимает 'drive_path' (строка, например 'C:\\' или '/')."
    ),
    Tool(
        name="read_document",
        func=read_document,
        description="Читает содержимое текстового файла, PDF, DOCX, PPTX, XLSX, RTF, ODT, LaTeX, CSV, EPUB и других поддерживаемых форматов. Возвращает текстовое содержимое. Принимает 'file_path' (строка)."
    ),
    Tool(
        name="get_system_info",
        func=get_system_info,
        description="Возвращает базовую информацию об операционной системе, процессоре, RAM и версии Python."
    ),
    Tool(
        name="execute_shell_command",
        func=execute_shell_command,
        description="Выполняет команду в системной оболочке. ОПАСНАЯ ФУНКЦИЯ, ИСПОЛЬЗУЙТЕ С ОГРАНИЧЕНИЯМИ! Принимает 'command' (строка)."
    ),
    Tool(
        name="get_current_working_directory",
        func=get_current_working_directory,
        description="Возвращает текущую рабочую директорию агента."
    ),
    Tool(
        name="change_working_directory",
        func=change_working_directory,
        description="Изменяет текущую рабочую директорию агента. Принимает 'path' (строка)."
    ),
    Tool(
        name="read_docx",
        func=read_docx,
        description="Читает текст из файла .docx. Требует 'pip install python-docx'. Принимает 'file_path' (строка)."
    ),
    Tool(
        name="read_pptx",
        func=read_pptx,
        description="Читает текст из файла .pptx (только текстовые поля). Требует 'pip install python-pptx'. Принимает 'file_path' (строка)."
    ),
    Tool(
        name="read_plain_text",
        func=read_plain_text,
        description="Читает обычный текстовый файл (.txt, .log, .md, .py и т.д.). Принимает 'file_path' (строка)."
    ),
    Tool(
        name="read_xlsx",
        func=read_xlsx,
        description="Читает данные из файла .xlsx (все листы). Требует 'pip install openpyxl'. Принимает 'file_path' (строка)."
    ),
    Tool(
        name="create_docx",
        func=create_docx,
        description="Создает новый документ Word (.docx) с заданным содержимым. Принимает 'file_path' (строка), 'content' (строка, по умолчанию пусто)."
    ),
    Tool(
        name="add_text_to_docx",
        func=add_text_to_docx,
        description="Добавляет новый абзац текста в конец существующего DOCX-документа. Принимает 'file_path' (строка), 'text_to_add' (строка)."
    ),
    Tool(
        name="replace_text_in_docx",
        func=replace_text_in_docx,
        description="Заменяет все вхождения старого текста на новый текст в DOCX-документе. Принимает 'file_path' (строка), 'old_text' (строка), 'new_text' (строка)."
    ),
    Tool(
        name="delete_paragraph_from_docx",
        func=delete_paragraph_from_docx,
        description="Удаляет абзац по его индексу (начиная с 0) из DOCX-документа. Принимает 'file_path' (строка), 'paragraph_index' (int)."
    ),
    Tool(
        name="add_slide_to_pptx",
        func=add_slide_to_pptx,
        description="Добавляет новый слайд в существующую презентацию PowerPoint. Принимает 'file_path' (строка), 'layout_index' (int, по умолчанию 1), 'title' (строка), 'content' (строка)."
    ),
    Tool(
        name="update_slide_text_by_index",
        func=update_slide_text_by_index,
        description="Заменяет текст на указанном слайде в PPTX-документе. Принимает 'file_path' (строка), 'slide_index' (int), 'old_text' (строка), 'new_text' (строка)."
    ),
    Tool(
        name="write_to_excel_cell",
        func=write_to_excel_cell,
        description="Записывает значение в указанную ячейку Excel-файла. Принимает 'file_path' (строка), 'sheet_name' (строка), 'cell_address' (строка), 'value' (любой тип)."
    ),
    Tool(
        name="read_from_excel_cell",
        func=read_from_excel_cell,
        description="Читает значение из указанной ячейки Excel-файла. Принимает 'file_path' (строка), 'sheet_name' (строка), 'cell_address' (строка)."
    ),
    Tool(
        name="add_sheet_to_xlsx",
        func=add_sheet_to_xlsx,
        description="Добавляет новый лист в существующий Excel-файл. Принимает 'file_path' (строка), 'new_sheet_name' (строка)."
    ),
    Tool(
        name="write_data_to_excel_range",
        func=write_data_to_excel_range,
        description="Записывает двумерный массив данных (список списков) в Excel, начиная с указанной ячейки. Принимает 'file_path' (строка), 'sheet_name' (строка), 'start_cell' (строка), 'data' (двумерный список)."
    ),
    Tool(
        name="create_pptx",
        func=create_pptx,
        description="Создает новую презентацию PowerPoint (.pptx) с титульным слайдом. Принимает 'file_path' (строка), 'title' (строка, по умолчанию пусто), 'subtitle' (строка, по умолчанию пусто)."
    ),
    Tool(
        name="create_xlsx",
        func=create_xlsx,
        description="Создает новый документ Excel (.xlsx) с одним листом. Принимает 'file_path' (строка), 'sheet_name' (строка, по умолчанию 'Sheet1')."
    ),
    Tool(
        name="merge_pdfs",
        func=merge_pdfs,
        description="Объединяет несколько PDF-файлов в один. Принимает 'output_path' (строка) и список входных PDF-файлов ('*input_paths' — строки путей)."
    ),
    Tool(
        name="extract_pdf_pages",
        func=extract_pdf_pages,
        description="Извлекает указанные страницы из PDF-файла в новый PDF. Принимает 'input_path' (строка), 'output_path' (строка), 'pages_to_extract' (список int, номера страниц с 0)."
    ),
]

# 3. Создание промпта для агента
prompt = ChatPromptTemplate.from_messages([
    ("system", "Ты AI ассистент, который может взаимодействовать с файловой системой пользователя. "
               "Используй доступные инструменты для выполнения задач, связанных с файлами, папками и системной информацией. "
               "Будь осторожен при удалении или изменении файлов. Всегда спрашивай подтверждение, если действие деструктивное."),
    MessagesPlaceholder(variable_name="chat_history"), # Для сохранения истории диалога
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 4. Создание агента
agent = create_tool_calling_agent(llm, tools, prompt)

# 5. Создание исполнителя агента (AgentExecutor)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 6. Запуск агента
if __name__ == "__main__":
    # Пример использования агента
    print("--- Запуск AI Агента ---")
    
    # Создадим временные файлы для демонстрации
    os.makedirs("agent_test_area", exist_ok=True)
    with open("agent_test_area/document.txt", "w") as f:
        f.write("Это тестовый документ для агента.")
    with open("agent_test_area/report.pdf", "w") as f: # Имитация PDF
        f.write("Fake PDF content.")
    
    chat_history = [] # Для сохранения истории диалога

    while True:
        user_input = input("\nВаш запрос (или 'выход' для завершения): ")
        if user_input.lower() == 'выход':
            break

        try:
            # invoke() - для одного запроса
            # stream() - для потоковой передачи ответов
            # ainvoke() - для асинхронных запросов
            result = agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history # Передаем историю
            })
            
            print(f"\nАгент: {result['output']}")
            
            # Обновляем историю чата
            chat_history.extend([
                ("human", user_input),
                ("ai", result['output'])
            ])

        except Exception as e:
            print(f"Произошла ошибка при работе агента: {e}")
            chat_history.extend([
                ("human", user_input),
                ("ai", f"Произошла ошибка: {e}. Пожалуйста, попробуйте еще раз.")
            ])

    # Очистка
    # import shutil
    # if os.path.exists("agent_test_area"):
    #     shutil.rmtree("agent_test_area")
    print("--- Агент завершил работу ---")