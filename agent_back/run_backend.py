import asyncio
import uvicorn
import threading
from gemma_mcp_server import mcp
from agent import app as fastapi_app

def run_mcp():
    print("MCP-сервер стартует на 127.0.0.1:8000")
    mcp.run(transport="sse", host="127.0.0.1", port=8000)

async def main():
    # Запуск MCP в отдельном потоке
    print("Запускаем MCP-сервер в фоновом потоке...")
    mcp_thread = threading.Thread(target=run_mcp, daemon=True)
    mcp_thread.start()

    # Запуск FastAPI через Uvicorn
    print("Запускаем FastAPI-сервер (агент)...")
    config_fastapi = uvicorn.Config(fastapi_app, host="127.0.0.1", port=5000, reload=False)
    server_fastapi = uvicorn.Server(config_fastapi)
    await server_fastapi.serve()

if __name__ == "__main__":
    asyncio.run(main())