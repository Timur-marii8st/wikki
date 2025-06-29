import os
from pathlib import Path

# --- PDF ---
from pypdf import PdfWriter, PdfReader 
from reportlab.lib.pagesizes import letter 
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.units import inch

# --- Word (DOCX) ---
from docx import Document 
from docx.shared import Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

# --- PowerPoint (PPTX) ---
from pptx import Presentation 
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE

# --- Excel (XLSX) ---
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter


# --- PDF Functions ---

def create_pdf_from_text(file_path: str, text_content: str, title: str = "Документ", author: str = "AI Agent") -> str:
    """
    Создает новый PDF-документ из заданного текста.
    Каждая новая строка в text_content будет начинаться с новой строки в PDF.
    
    Args:
        file_path (str): Путь для сохранения нового PDF-файла.
        text_content (str): Текст для записи в PDF.
        title (str): Название документа.
        author (str): Автор документа.
        
    Returns:
        str: Сообщение об успешном создании или ошибке.
    """
    try:
        c = canvas.Canvas(file_path, pagesize=letter)
        c.setTitle(title)
        c.setAuthor(author)
        
        # Размеры страницы и поля
        width, height = letter
        left_margin = inch
        right_margin = width - inch
        bottom_margin = inch
        top_margin = height - inch
        
        textobject = c.beginText()
        textobject.setTextOrigin(left_margin, top_margin - 0.5 * inch)
        textobject.setFont("Helvetica", 12)
        
        # Разбиваем текст на строки и переносим, если слишком длинные
        lines = text_content.split('\n')
        y_pos = top_margin - 0.5 * inch
        line_height = 14
        
        for line in lines:
            if y_pos < bottom_margin: # Если места не хватает, новая страница
                c.drawText(textobject)
                c.showPage()
                textobject = c.beginText()
                textobject.setTextOrigin(left_margin, top_margin - 0.5 * inch)
                textobject.setFont("Helvetica", 12)
                y_pos = top_margin - 0.5 * inch

            wrapped_lines = []
            words = line.split(' ')
            current_line = []
            for word in words:
                if c.stringWidth(' '.join(current_line + [word]), "Helvetica", 12) < (right_margin - left_margin):
                    current_line.append(word)
                else:
                    wrapped_lines.append(' '.join(current_line))
                    current_line = [word]
            wrapped_lines.append(' '.join(current_line)) # Add the last line

            for wrapped_line in wrapped_lines:
                textobject.textLine(wrapped_line)
                y_pos -= line_height

        c.drawText(textobject)
        c.save()
        return f"PDF файл '{file_path}' успешно создан."
    except Exception as e:
        return f"Ошибка при создании PDF файла '{file_path}': {e}"

def merge_pdfs(output_path: str, *input_paths: str) -> str:
    """
    Объединяет несколько PDF-файлов в один.
    
    Args:
        output_path (str): Путь для сохранения объединенного PDF.
        *input_paths (str): Список путей к PDF-файлам для объединения.
        
    Returns:
        str: Сообщение об успешном объединении или ошибке.
    """
    try:
        if not input_paths:
            return "Ошибка: Не указаны входные PDF-файлы для объединения."
            
        writer = PdfWriter()
        for path in input_paths:
            if not os.path.isfile(path):
                return f"Ошибка: Входной файл PDF '{path}' не найден."
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)
        
        with open(output_path, "wb") as f:
            writer.write(f)
            
        return f"PDF файлы успешно объединены в '{output_path}'."
    except Exception as e:
        return f"Ошибка при объединении PDF файлов: {e}"

def extract_pdf_pages(input_path: str, output_path: str, pages_to_extract: list[int]) -> str:
    """
    Извлекает указанные страницы из PDF-файла в новый PDF.
    Страницы нумеруются с 0.
    
    Args:
        input_path (str): Путь к исходному PDF-файлу.
        output_path (str): Путь для сохранения нового PDF с извлеченными страницами.
        pages_to_extract (list[int]): Список номеров страниц для извлечения (начиная с 0).
        
    Returns:
        str: Сообщение об успешном извлечении или ошибке.
    """
    try:
        if not os.path.isfile(input_path):
            return f"Ошибка: Исходный файл PDF '{input_path}' не найден."
            
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page_num in pages_to_extract:
            if 0 <= page_num < len(reader.pages):
                writer.add_page(reader.pages[page_num])
            else:
                return f"Ошибка: Страница {page_num} выходит за пределы диапазона (0-{len(reader.pages)-1}) в файле '{input_path}'."
        
        if not writer.pages:
            return "Предупреждение: Не удалось извлечь ни одной страницы. Возможно, номера страниц некорректны."

        with open(output_path, "wb") as f:
            writer.write(f)
            
        return f"Страницы {pages_to_extract} успешно извлечены в '{output_path}'."
    except Exception as e:
        return f"Ошибка при извлечении страниц из PDF файла: {e}"

# --- Word (DOCX) Functions ---

def create_docx(file_path: str, content: str = "") -> str:
    """
    Создает новый документ Word (.docx) с заданным содержимым.
    
    Args:
        file_path (str): Путь для сохранения нового DOCX-файла.
        content (str): Начальный текст для документа.
        
    Returns:
        str: Сообщение об успешном создании или ошибке.
    """
    try:
        document = Document()
        if content:
            document.add_paragraph(content)
        document.save(file_path)
        return f"DOCX файл '{file_path}' успешно создан."
    except Exception as e:
        return f"Ошибка при создании DOCX файла '{file_path}': {e}"

def add_text_to_docx(file_path: str, text_to_add: str) -> str:
    """
    Добавляет новый абзац текста в конец существующего DOCX-документа.
    
    Args:
        file_path (str): Путь к DOCX-файлу.
        text_to_add (str): Текст для добавления.
        
    Returns:
        str: Сообщение об успешном добавлении или ошибке.
    """
    try:
        if not os.path.exists(file_path):
            return f"Ошибка: DOCX файл '{file_path}' не найден."
            
        document = Document(file_path)
        document.add_paragraph(text_to_add)
        document.save(file_path)
        return f"Текст успешно добавлен в '{file_path}'."
    except Exception as e:
        return f"Ошибка при добавлении текста в DOCX файл '{file_path}': {e}"

def replace_text_in_docx(file_path: str, old_text: str, new_text: str) -> str:
    """
    Заменяет все вхождения старого текста на новый текст в DOCX-документе.
    
    Args:
        file_path (str): Путь к DOCX-файлу.
        old_text (str): Текст, который нужно найти.
        new_text (str): Текст, на который нужно заменить.
        
    Returns:
        str: Сообщение об успешной замене или ошибке.
    """
    try:
        if not os.path.exists(file_path):
            return f"Ошибка: DOCX файл '{file_path}' не найден."
            
        document = Document(file_path)
        replaced_count = 0
        for paragraph in document.paragraphs:
            if old_text in paragraph.text:
                paragraph.text = paragraph.text.replace(old_text, new_text)
                replaced_count += 1
        
        # Также ищем в таблицах
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if old_text in paragraph.text:
                            paragraph.text = paragraph.text.replace(old_text, new_text)
                            replaced_count += 1
        
        document.save(file_path)
        return f"Вхождения '{old_text}' успешно заменены на '{new_text}' в '{file_path}'. Заменено {replaced_count} раз."
    except Exception as e:
        return f"Ошибка при замене текста в DOCX файле '{file_path}': {e}"

def delete_paragraph_from_docx(file_path: str, paragraph_index: int) -> str:
    """
    Удаляет абзац по его индексу (начиная с 0) из DOCX-документа.
    
    Args:
        file_path (str): Путь к DOCX-файлу.
        paragraph_index (int): Индекс абзаца для удаления.
        
    Returns:
        str: Сообщение об успешном удалении или ошибке.
    """
    try:
        if not os.path.exists(file_path):
            return f"Ошибка: DOCX файл '{file_path}' не найден."
            
        document = Document(file_path)
        
        if not (0 <= paragraph_index < len(document.paragraphs)):
            return f"Ошибка: Индекс абзаца {paragraph_index} вне диапазона (0-{len(document.paragraphs)-1})."
            
        p = document.paragraphs[paragraph_index]
        p._element.getparent().remove(p._element) # Манипуляция с XML элементом
        
        document.save(file_path)
        return f"Абзац по индексу {paragraph_index} успешно удален из '{file_path}'."
    except Exception as e:
        return f"Ошибка при удалении абзаца из DOCX файла '{file_path}': {e}"

# --- PowerPoint (PPTX) Functions ---

def create_pptx(file_path: str, title: str = "", subtitle: str = "") -> str:
    """
    Создает новую презентацию PowerPoint (.pptx) с титульным слайдом.
    
    Args:
        file_path (str): Путь для сохранения нового PPTX-файла.
        title (str): Заголовок титульного слайда.
        subtitle (str): Подзаголовок титульного слайда.
        
    Returns:
        str: Сообщение об успешном создании или ошибке.
    """
    try:
        prs = Presentation()
        title_slide_layout = prs.slide_layouts[0] # Обычно первый макет - это титульный слайд
        slide = prs.slides.add_slide(title_slide_layout)
        
        if title:
            slide.shapes.title.text = title
        if subtitle:
            slide.placeholders[1].text = subtitle # Подзаголовок обычно на втором placeholder
            
        prs.save(file_path)
        return f"PPTX файл '{file_path}' успешно создан с титульным слайдом."
    except Exception as e:
        return f"Ошибка при создании PPTX файла '{file_path}': {e}"

def add_slide_to_pptx(file_path: str, layout_index: int = 1, title: str = "", content: str = "") -> str:
    """
    Добавляет новый слайд в существующую презентацию PowerPoint.
    
    Args:
        file_path (str): Путь к PPTX-файлу.
        layout_index (int): Индекс макета слайда (например, 1 для "Заголовок и содержимое").
                            Доступные макеты зависят от темы.
        title (str): Заголовок нового слайда.
        content (str): Основное содержимое нового слайда.
        
    Returns:
        str: Сообщение об успешном добавлении или ошибке.
    """
    try:
        if not os.path.exists(file_path):
            return f"Ошибка: PPTX файл '{file_path}' не найден."
            
        prs = Presentation(file_path)
        
        if not (0 <= layout_index < len(prs.slide_layouts)):
            return f"Ошибка: Индекс макета слайда {layout_index} вне диапазона (0-{len(prs.slide_layouts)-1})."
            
        slide_layout = prs.slide_layouts[layout_index]
        slide = prs.slides.add_slide(slide_layout)
        
        # Поиск и заполнение заголовочного placeholder
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            if shape.is_placeholder and shape.placeholder_format.is_title:
                shape.text_frame.text = title
                break
        
        # Поиск и заполнение текстового placeholder (если есть)
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            # Ищем body placeholder или просто любой другой текстовый фрейм, который не заголовок
            if shape.is_placeholder and not shape.placeholder_format.is_title:
                text_frame = shape.text_frame
                text_frame.clear()  # Очищаем существующий текст
                p = text_frame.paragraphs[0]
                run = p.add_run()
                run.text = content
                break
        
        prs.save(file_path)
        return f"Новый слайд успешно добавлен в '{file_path}'."
    except Exception as e:
        return f"Ошибка при добавлении слайда в PPTX файл '{file_path}': {e}"

def update_slide_text_by_index(file_path: str, slide_index: int, old_text: str, new_text: str) -> str:
    """
    Заменяет текст на указанном слайде в PPTX-документе.
    
    Args:
        file_path (str): Путь к PPTX-файлу.
        slide_index (int): Индекс слайда для обновления (начиная с 0).
        old_text (str): Текст, который нужно найти.
        new_text (str): Текст, на который нужно заменить.
        
    Returns:
        str: Сообщение об успешном обновлении или ошибке.
    """
    try:
        if not os.path.exists(file_path):
            return f"Ошибка: PPTX файл '{file_path}' не найден."
            
        prs = Presentation(file_path)
        
        if not (0 <= slide_index < len(prs.slides)):
            return f"Ошибка: Индекс слайда {slide_index} вне диапазона (0-{len(prs.slides)-1})."
            
        slide = prs.slides[slide_index]
        replaced_count = 0
        
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            
            text_frame = shape.text_frame
            for paragraph in text_frame.paragraphs:
                for run in paragraph.runs:
                    if old_text in run.text:
                        run.text = run.text.replace(old_text, new_text)
                        replaced_count += 1
                        
        prs.save(file_path)
        return f"Текст на слайде {slide_index} в '{file_path}' обновлен. Заменено {replaced_count} раз."
    except Exception as e:
        return f"Ошибка при обновлении текста на слайде в PPTX файле '{file_path}': {e}"

# --- Excel (XLSX) Functions ---

def create_xlsx(file_path: str, sheet_name: str = "Sheet1") -> str:
    """
    Создает новый документ Excel (.xlsx) с одним листом.
    
    Args:
        file_path (str): Путь для сохранения нового XLSX-файла.
        sheet_name (str): Имя первого листа.
        
    Returns:
        str: Сообщение об успешном создании или ошибке.
    """
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name
        wb.save(file_path)
        return f"XLSX файл '{file_path}' успешно создан с листом '{sheet_name}'."
    except Exception as e:
        return f"Ошибка при создании XLSX файла '{file_path}': {e}"

def write_to_excel_cell(file_path: str, sheet_name: str, cell_address: str, value: any) -> str:
    """
    Записывает значение в указанную ячейку Excel-файла.
    
    Args:
        file_path (str): Путь к XLSX-файлу.
        sheet_name (str): Имя листа.
        cell_address (str): Адрес ячейки (например, "A1", "B5").
        value (any): Значение для записи.
        
    Returns:
        str: Сообщение об успешной записи или ошибке.
    """
    try:
        if not os.path.exists(file_path):
            return f"Ошибка: XLSX файл '{file_path}' не найден."
            
        wb = load_workbook(file_path)
        
        if sheet_name not in wb.sheetnames:
            return f"Ошибка: Лист '{sheet_name}' не найден в файле '{file_path}'."
            
        ws = wb[sheet_name]
        ws[cell_address] = value
        wb.save(file_path)
        return f"Значение '{value}' успешно записано в ячейку '{cell_address}' на листе '{sheet_name}' в '{file_path}'."
    except Exception as e:
        return f"Ошибка при записи в Excel файл '{file_path}': {e}"

def read_from_excel_cell(file_path: str, sheet_name: str, cell_address: str) -> str:
    """
    Читает значение из указанной ячейки Excel-файла.
    
    Args:
        file_path (str): Путь к XLSX-файлу.
        sheet_name (str): Имя листа.
        cell_address (str): Адрес ячейки (например, "A1", "B5").
        
    Returns:
        str: Значение ячейки или сообщение об ошибке.
    """
    try:
        if not os.path.exists(file_path):
            return f"Ошибка: XLSX файл '{file_path}' не найден."
            
        wb = load_workbook(file_path)
        
        if sheet_name not in wb.sheetnames:
            return f"Ошибка: Лист '{sheet_name}' не найден в файле '{file_path}'."
            
        ws = wb[sheet_name]
        value = ws[cell_address].value
        return f"Значение в ячейке '{cell_address}' на листе '{sheet_name}' в '{file_path}': {value}"
    except Exception as e:
        return f"Ошибка при чтении из Excel файла '{file_path}': {e}"

def add_sheet_to_xlsx(file_path: str, new_sheet_name: str) -> str:
    """
    Добавляет новый лист в существующий Excel-файл.
    
    Args:
        file_path (str): Путь к XLSX-файлу.
        new_sheet_name (str): Имя нового листа.
        
    Returns:
        str: Сообщение об успешном добавлении листа или ошибке.
    """
    try:
        if not os.path.exists(file_path):
            return f"Ошибка: XLSX файл '{file_path}' не найден."
            
        wb = load_workbook(file_path)
        
        if new_sheet_name in wb.sheetnames:
            return f"Ошибка: Лист '{new_sheet_name}' уже существует в файле '{file_path}'."
            
        wb.create_sheet(new_sheet_name)
        wb.save(file_path)
        return f"Лист '{new_sheet_name}' успешно добавлен в '{file_path}'."
    except Exception as e:
        return f"Ошибка при добавлении листа в Excel файл '{file_path}': {e}"

def write_data_to_excel_range(file_path: str, sheet_name: str, start_cell: str, data: list[list[any]]) -> str:
    """
    Записывает двумерный массив данных (список списков) в Excel, начиная с указанной ячейки.
    
    Args:
        file_path (str): Путь к XLSX-файлу.
        sheet_name (str): Имя листа.
        start_cell (str): Начальная ячейка (например, "A1").
        data (list[list[any]]): Двумерный массив данных для записи.
        
    Returns:
        str: Сообщение об успешной записи или ошибке.
    """
    try:
        if not os.path.exists(file_path):
            return f"Ошибка: XLSX файл '{file_path}' не найден."
            
        wb = load_workbook(file_path)
        
        if sheet_name not in wb.sheetnames:
            return f"Ошибка: Лист '{sheet_name}' не найден в файле '{file_path}'."
            
        ws = wb[sheet_name]
        
        # Получаем координаты начальной ячейки
        start_row = ws[start_cell].row
        start_col = ws[start_cell].column
        
        for r_idx, row_data in enumerate(data):
            for c_idx, cell_value in enumerate(row_data):
                ws.cell(row=start_row + r_idx, column=start_col + c_idx, value=cell_value)
        
        wb.save(file_path)
        return f"Данные успешно записаны в диапазон, начиная с '{start_cell}', на листе '{sheet_name}' в '{file_path}'."
    except Exception as e:
        return f"Ошибка при записи диапазона данных в Excel файл '{file_path}': {e}"