from fastapi import FastAPI
from pydantic import BaseModel
from agent_back.langchain import chain 

app = FastAPI()

class Query(BaseModel):
    input: str

@app.post("/ask")
async def ask_agent(query: Query):
    response = await chain.ainvoke({"input": query.input})
    return {"answer": response}