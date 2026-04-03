from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from routes.chat import router

app = FastAPI(
    title="Chatbot API",
    description="chatbot API by Groq LLaMA",
    version="1.0.0"
)

app.include_router(router)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    import json, os
    history = {}
    if os.path.exists("history.json"):
        with open("history.json", "r") as f:
            history = json.load(f)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"messages": [], "chat_id": None, "history": history}
    )