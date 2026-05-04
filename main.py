from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from routes.chat import router
from config import AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_CALLBACK_URL, SECRET_KEY
import json
import os
from urllib.parse import quote_plus
from fastapi.staticfiles import StaticFiles



app = FastAPI(
    title="Chatbot API",
    description="chatbot API by Groq LLaMA",
    version="1.0.0"
)

# session middleware for login
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=False
)

# Auth0 setup
oauth = OAuth()
oauth.register(
    name='auth0',
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    server_metadata_url=f'https://{AUTH0_DOMAIN}/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid profile email'}
)

# create shares.json if missing (Render ephemeral filesystem)
if not os.path.exists("shares.json"):
    with open("shares.json", "w") as f:
        json.dump({}, f)

app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = request.session.get('user')
    if not user:
        return RedirectResponse(url='/login')

    # load per-user history
    from routes.chat import load_history, get_history_file
    user_id = user.get("sub", "default")
    history = load_history(user_id)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "messages": [],
            "chat_id": None,
            "history": history,
            "current_topic": "",
            "user": user
        }
    )


@app.get("/login")
async def login(request: Request):
    return await oauth.auth0.authorize_redirect(
        request, AUTH0_CALLBACK_URL,
        prompt="consent"
    )


@app.get("/callback")
async def callback(request: Request):
    try:
        token = await oauth.auth0.authorize_access_token(request)
        user = token.get('userinfo')

        if not user:
            return RedirectResponse(url="/login")

        request.session['user'] = dict(user)
        return RedirectResponse(url='/')

    except Exception as e:
        print("Auth Error:", e)   
        request.session.clear()
        return RedirectResponse(url="/login")


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()

    return_to = quote_plus("https://gemini-chatboard-11.onrender.com")

    return RedirectResponse(
        url=f"https://{AUTH0_DOMAIN}/v2/logout?returnTo={return_to}&client_id={AUTH0_CLIENT_ID}"
    )