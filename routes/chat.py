from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from models.schemas import ChatRequest, ChatResponse
from services.gemini import get_gemini_response
import json
import uuid
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

HISTORY_FILE = "history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


@router.post("/chat", response_model=ChatResponse)
async def chat_api(request: ChatRequest):
    try:
        ai_response = get_gemini_response(request.message)
        return ChatResponse(response=ai_response)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")


@router.post("/chat/ui", response_class=HTMLResponse)
async def chat_ui(request: Request, message: str = Form(...), chat_id: str = Form(None)):
    history = load_history()

    if not chat_id:
        chat_id = str(uuid.uuid4())[:8]
        history[chat_id] = {"title": message[:30], "messages": []}

    try:
        ai_response = get_gemini_response(message)
        history[chat_id]["messages"].append({"role": "user", "text": message})
        history[chat_id]["messages"].append({"role": "ai", "text": ai_response})
    except Exception as e:
        history[chat_id]["messages"].append({"role": "user", "text": message})
        history[chat_id]["messages"].append({"role": "ai", "text": f"Error: {str(e)}"})

    save_history(history)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "messages": history[chat_id]["messages"],
            "chat_id": chat_id,
            "history": history
        }
    )


@router.get("/chat/{chat_id}", response_class=HTMLResponse)
async def load_chat(request: Request, chat_id: str):
    history = load_history()
    messages = history.get(chat_id, {}).get("messages", [])
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "messages": messages,
            "chat_id": chat_id,
            "history": history
        }
    )

@router.post("/chat/{chat_id}/rename")
async def rename_chat(chat_id: str, new_title: str = Form(...)):
    history = load_history()
    if chat_id in history:
        history[chat_id]["title"] = new_title[:30]
        save_history(history)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/chat/{chat_id}", status_code=303)


@router.post("/chat/{chat_id}/delete")
async def delete_chat(chat_id: str):
    history = load_history()
    if chat_id in history:
        del history[chat_id]
        save_history(history)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)