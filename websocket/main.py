from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from routes import chat, admin

app = FastAPI()

def load_html(path):
    with open(path, "r", encoding="utf8") as f:
        return f.read()

@app.get("/")
async def chat_page():
    return HTMLResponse(load_html("templates/chat.html"))

@app.get("/admin")
async def admin_page():
    return HTMLResponse(load_html("templates/admin.html"))

app.include_router(chat.router)
app.include_router(admin.router)