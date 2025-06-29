from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOllama

# 1. Инициализация модели
llm = ChatOllama(model="gemma3:4b")

# 2. Создание шаблона промпта
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("user", "{input}")
])

# 3. Парсер для получения строки в ответе
output_parser = StrOutputParser()

# 4. Сборка цепочки
chain = prompt | llm | output_parser