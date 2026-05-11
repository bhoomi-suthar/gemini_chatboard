from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.templating import Jinja2Templates
from models.schemas import ChatRequest, ChatResponse
from services.gemini import get_gemini_response, generate_chat_title, check_topic_relevance
import json
import uuid
import os
import pathlib
import hashlib
import time
from fastapi import Body


SHARES_FILE = "/tmp/shares.json"
router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_history_file(user_id: str) -> str:
    # sanitize user_id to be safe for filenames
    safe_id = user_id.replace("|", "_").replace("/", "_").replace("\\", "_")
    return f"history_{safe_id}.json"


PDF_DIR = pathlib.Path("uploaded_pdfs")
PDF_DIR.mkdir(exist_ok=True)

def get_history_file(user_id: str) -> str:
    safe_id = user_id.replace("|", "_").replace("/", "_")
    return f"/tmp/history_{safe_id}.json"

def load_history(user_id: str = "default"):
    path = get_history_file(user_id)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_history(history, user_id: str = "default"):
    path = get_history_file(user_id)
    with open(path, "w") as f:
        json.dump(history, f, indent=2)

def get_user_id(request: Request) -> str:
    user = request.session.get("user", {})
    return user.get("sub", "default")


def load_shares():
    if not os.path.exists(SHARES_FILE):
        return {}
    with open(SHARES_FILE, "r") as f:
        return json.load(f)

def save_shares(shares):
    with open(SHARES_FILE, "w") as f:
        json.dump(shares, f, indent=2)


@router.post("/chat", response_model=ChatResponse)
async def chat_api(request: ChatRequest):
    try:
        ai_response = get_gemini_response(request.message)
        return ChatResponse(response=ai_response)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")


@router.post("/chat/ui", response_class=HTMLResponse)
async def chat_ui(
    request: Request,
    message: str = Form(...),
    chat_id: str = Form(None),
    pdf_file: UploadFile = File(None),
    response_mode: str = Form("table"),
    topic: str = Form("")  
):
    user_id = get_user_id(request)
    history = load_history(user_id)

    is_new_chat = not chat_id
    if not chat_id:
        chat_id = str(uuid.uuid4())[:8]
        history[chat_id] = {"title": message[:40], "messages": []}

    try:
        full_message = message
        pdf_name = None

        if pdf_file and pdf_file.filename:
            pdf_name = pdf_file.filename
            import fitz
            from services.rag import embed_and_store_pdf, get_relevant_chunks

            contents = await pdf_file.read()

            pdf_path = PDF_DIR / pdf_file.filename
            with open(pdf_path, "wb") as f:
                f.write(contents)

            doc = fitz.open(stream=contents, filetype="pdf")
            pdf_text = "".join(page.get_text() for page in doc)
            doc.close()

            if pdf_text.strip():
                # store chunks in Pinecone
                embed_and_store_pdf(pdf_text, pdf_name, chat_id)
                
                # get only relevant chunks for this question
                relevant_chunks = get_relevant_chunks(message, chat_id, pdf_name)
                
                if relevant_chunks:
                    full_message = f"{message}\n\n[Relevant PDF Content]:\n{relevant_chunks}"
                else:
                    # fallback to first 3000 chars if no matches
                    full_message = f"{message}\n\n[PDF Content]:\n{pdf_text[:3000]}"

        #  Topic Filter Logic 
        topic = topic.strip() if topic else ""

    
        history[chat_id]["topic"] = topic

        if topic != "":
            is_relevant = check_topic_relevance(message, topic)
            if not is_relevant:
                ai_response = f"<p>This question is not from selected topic <strong>{topic}</strong>. Please ask something related to selected topic <strong>{topic}</strong>.</p>"
            else:
                ai_response = get_gemini_response(full_message, response_mode, history[chat_id]["messages"])
        else:
            ai_response = get_gemini_response(full_message, response_mode, history[chat_id]["messages"])

        history[chat_id]["messages"].append({
            "role": "user",
            "text": message,
            "pdf": pdf_name
        })

        history[chat_id]["messages"].append({
            "role": "ai",
            "text": ai_response
        })

        if is_new_chat:
            smart_title = generate_chat_title(message, ai_response)
            history[chat_id]["title"] = smart_title

    except Exception as e:
        history[chat_id]["messages"].append({
            "role": "user",
            "text": message,
            "pdf": pdf_file.filename if pdf_file else None
        })
        history[chat_id]["messages"].append({
            "role": "ai",
            "text": f"Error: {str(e)}"
        })

    save_history(history, user_id)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "messages": history[chat_id]["messages"],
            "chat_id": chat_id,
            "history": history,
            "current_topic": history.get(chat_id, {}).get("topic", "")
        }
    )


@router.get("/chat/{chat_id}", response_class=HTMLResponse)
async def load_chat(request: Request, chat_id: str):
    user_id = get_user_id(request)
    history = load_history(user_id)
    messages = history.get(chat_id, {}).get("messages", [])
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "messages": messages,
            "chat_id": chat_id,
            "history": history,
            "current_topic": history.get(chat_id, {}).get("topic", "") 
        }
    )


@router.post("/chat/{chat_id}/rename")
async def rename_chat(request: Request, chat_id: str, new_title: str = Form(...)):
    user_id = get_user_id(request)
    history = load_history(user_id)
    if chat_id in history:
        history[chat_id]["title"] = new_title[:30]
        save_history(history, user_id)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/chat/{chat_id}", status_code=303)


@router.post("/chat/{chat_id}/delete")
async def delete_chat(request: Request, chat_id: str):
    user_id = get_user_id(request)
    history = load_history(user_id)
    if chat_id in history:
        del history[chat_id]
        save_history(history, user_id)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


@router.post("/chat/{chat_id}/pin")
async def pin_chat(request: Request, chat_id: str):
    user_id = get_user_id(request)
    history = load_history(user_id)
    if chat_id in history:
        history[chat_id]["pinned"] = not history[chat_id].get("pinned", False)
        save_history(history, user_id)
    from fastapi.responses import JSONResponse
    return JSONResponse({"status": "ok"})


@router.get("/pdf/{filename}")
async def serve_pdf(filename: str):
    pdf_path = PDF_DIR / filename
    if pdf_path.exists():
        return FileResponse(pdf_path, media_type="application/pdf")
    raise HTTPException(status_code=404, detail="PDF not found")



@router.post("/chat/edit", response_class=HTMLResponse)
async def chat_edit(
    request: Request,
    message: str = Form(...),
    chat_id: str = Form(None),
    response_mode: str = Form("table"),
    topic: str = Form(""),
    edit_from_index: str = Form("0")
):
    user_id = get_user_id(request)
    history = load_history(user_id)

    if not chat_id or chat_id not in history:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    try:
        idx = int(edit_from_index) - 1
    except:
        idx = len(history[chat_id]["messages"]) - 1

    history[chat_id]["messages"] = history[chat_id]["messages"][:idx]

    topic = topic.strip() if topic else ""

    try:
        if topic:
            is_relevant = check_topic_relevance(message, topic)
            if not is_relevant:
                ai_response = f"<p>This question is not from selected topic <strong>{topic}</strong>. Please ask something related to <strong>{topic}</strong>.</p>"
            else:
                ai_response = get_gemini_response(message, response_mode, history[chat_id]["messages"])
        else:
            ai_response = get_gemini_response(message, response_mode, history[chat_id]["messages"])

        history[chat_id]["messages"].append({"role": "user", "text": message, "pdf": None})
        history[chat_id]["messages"].append({"role": "ai", "text": ai_response})

    except Exception as e:
        history[chat_id]["messages"].append({"role": "user", "text": message, "pdf": None})
        history[chat_id]["messages"].append({"role": "ai", "text": f"Error: {str(e)}"})

    save_history(history, user_id)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "messages": history[chat_id]["messages"],
            "chat_id": chat_id,
            "history": history,
            "current_topic": history.get(chat_id, {}).get("topic", "")
        }
    )




# sharing chart
@router.post("/chat/{chat_id}/share")
async def create_share(request: Request, chat_id: str):
    user_id = get_user_id(request)
    history = load_history(user_id)
    if chat_id not in history:
        raise HTTPException(status_code=404, detail="Chat not found")

    share_id = hashlib.md5(f"{chat_id}{time.time()}".encode()).hexdigest()[:10]

    shares = load_shares()
    shares[share_id] = {
        "title": history[chat_id].get("title", "Shared Chat"),
        "messages": history[chat_id]["messages"]  # snapshort of messages at the time of sharing
    }
    save_shares(shares)

    # mark this chat as shared in history
    history[chat_id]["shared"] = True
    history[chat_id]["share_id"] = share_id
    save_history(history, user_id)

    from fastapi.responses import JSONResponse
    return JSONResponse({"share_id": share_id})



@router.get("/share/{share_id}", response_class=HTMLResponse)
async def view_share(request: Request, share_id: str):
    shares = load_shares()
    if share_id not in shares:
        # show expired page instead of raw error
        return templates.TemplateResponse(
            request=request,
            name="share.html",
            context={
                "title": "Chat Unavailable",
                "messages": [],
                "share_id": share_id
            }
        )
    chat = shares[share_id]
    return templates.TemplateResponse(
        request=request,
        name="share.html",
        context={
            "title": chat["title"],
            "messages": chat["messages"],
            "share_id": share_id
        }
    )

@router.post("/share/api/chat")
async def share_chat_api(payload: dict = Body(...)):
    message = payload.get("message", "")
    history = payload.get("history", [])
    response_mode = payload.get("response_mode", "table")
    topic = payload.get("topic", "")

    if not message:
        from fastapi.responses import JSONResponse
        return JSONResponse({"response": "No message."})

    try:
        if topic:
            is_relevant = check_topic_relevance(message, topic)
            if not is_relevant:
                from fastapi.responses import JSONResponse
                return JSONResponse({"response": f"<p>This question is not related to selected topic <strong>{topic}</strong>.</p>"})

        ai_response = get_gemini_response(message, response_mode, history)
        from fastapi.responses import JSONResponse
        return JSONResponse({"response": ai_response})
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse({"response": f"Error: {str(e)}"})


@router.post("/chat/{chat_id}/unshare")
async def unshare_chat(request: Request, chat_id: str):
    user_id = get_user_id(request)
    history = load_history(user_id)
    if chat_id in history:
        # get the share_id before removing
        share_id = history[chat_id].get("share_id")
        
        # remove shared from history
        history[chat_id]["shared"] = False
        history[chat_id].pop("share_id", None)
        save_history(history, user_id)
        
        # remove from shares.json so the link stops working
        if share_id:
            shares = load_shares()
            shares.pop(share_id, None)
            save_shares(shares)
    
    from fastapi.responses import JSONResponse
    return JSONResponse({"status": "ok"})