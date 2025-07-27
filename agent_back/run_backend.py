import asyncio
import uvicorn
import threading

# Импортируем ваши приложения FastAPI и FastMCP
from agent import app as fastapi_app

def run_mcp():
    from gemma_mcp_server import mcp
    mcp.run(transport="sse", host="127.0.0.1", port=8000)

async def main():
    # Запуск MCP в отдельном потоке
    mcp_thread = threading.Thread(target=run_mcp, daemon=True)
    mcp_thread.start()

    # Запуск FastAPI через Uvicorn
    config_fastapi = uvicorn.Config(fastapi_app, host="127.0.0.1", port=5000)
    server_fastapi = uvicorn.Server(config_fastapi)
    await server_fastapi.serve()

if __name__ == "__main__":
    asyncio.run(main())