import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from gemma_mcp_client import GemmaMCPClient 
from fastapi.middleware.cors import CORSMiddleware

# Модели Pydantic для валидации 
class ChatRequest(BaseModel):
    prompt: str
    history: list = []

class ChatResponse(BaseModel):
    response: str
    history: list

# a standard MCP configuration
MCP_CONFIG = {
    "mcpServers": {
        "main_server": {
            "url": "http://localhost:8000/sse/" 
        }
    }
}

OLLAMA_MODEL = "hf.co/unsloth/gemma-3n-E4B-it-GGUF:Q4_K_XL"

# Локальная функция, которая будет доступна агенту
def get_user_info(user_id: int) -> dict:
    """Возвращает информацию о пользователе по его ID."""
    if user_id == 101:
        return {"name": "Timur", "status": "active"}
    return {"error": "User not found"}


# Управление жизненным циклом агента 
# Создаем один экземпляр клиента для всего приложения
agent_client = GemmaMCPClient(model=OLLAMA_MODEL, mcp_config=MCP_CONFIG)
agent_client.add_function(get_user_info)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код, который выполнится при старте сервера
    print("Сервер запускается, инициализация клиента агента...")
    await agent_client.initialize()
    yield
    # Код, который выполнится при остановке сервера
    print("Сервер останавливается, очистка ресурсов клиента...")
    await agent_client.cleanup()

# Приложение FastAPI 
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # 1. Получаем ответ от агента, который будет Union
    response_from_agent = await agent_client.chat(
        request.prompt,
        execute_functions=True,
        history=request.history.copy()
    )
    # 2. Проверяем тип ответа и "уточняем" его до строки
    final_response_text: str
    if isinstance(response_from_agent, str):
        # Это ожидаемый, успешный результат
        final_response_text = response_from_agent
    else:
        # Это хуёвый результат. Агент не смог дать финальный ответ.
        # Логируем это для отладки и отдаем пользователю сообщение об ошибке.
        print(f"ОШИБКА: Агент вернул не строковый тип: {type(response_from_agent)} | {response_from_agent}")
        final_response_text = "Извините, я не смог обработать ваш запрос до конца."

    # 3. Формируем историю с гарантированно текстовым ответом
    updated_history = request.history + [
        {"role": "model", "content": final_response_text}
    ]

    # 4. Возвращаем фронтенду предсказуемый и чистый объект ChatResponse
    return ChatResponse(response=final_response_text, history=updated_history)