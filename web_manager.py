import json
import os
import hmac
import hashlib
from typing import Optional

import asyncio
from fastapi import FastAPI, Form, Request, WebSocket, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from minecraft_manager import RCONClient, tail_log
import re

CONFIG_PATH = "server_config.json"
app = FastAPI(title="Minecraft Web Manager")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def load_config() -> Optional[dict]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf8") as f:
            return json.load(f)
    return None

def save_config(data: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf8") as f:
        json.dump(data, f, indent=2)


def is_authenticated(request: Request) -> bool:
    cfg = load_config()
    if not cfg:
        return False
    token = request.cookies.get("session")
    return bool(token and hmac.compare_digest(token, cfg.get("admin_password_hash", "")))


def require_auth(request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

def get_client() -> RCONClient:
    cfg = load_config()
    if not cfg:
        raise RuntimeError("Server not configured")
    client = RCONClient(cfg["host"], cfg["port"], cfg["password"])
    client.connect()
    return client

def parse_player_list(text: str) -> tuple[int, list[str]]:
    """Parse the output of the Minecraft 'list' command."""
    match = re.search(
        r"There are (\d+) (?:of a max \d+ )?players online(?::\s*(.*))?",
        text,
    )
    if not match:
        return 0, []
    count = int(match.group(1))
    names: list[str] = []
    if match.group(2):
        name_str = match.group(2).strip()
        names = [n.strip() for n in re.split(r",\s*", name_str) if n.strip()]
    return count, names


def render_dashboard(request: Request, result: Optional[str] = None) -> HTMLResponse:
    cfg = load_config()
    if not cfg:
        dirs = [d for d in os.listdir("/opt") if os.path.isdir(os.path.join("/opt", d))]
        return templates.TemplateResponse("setup.html", {"request": request, "dirs": dirs})

    client = get_client()
    try:
        players_raw = client.command("list")
    finally:
        client.close()

    player_count, player_list = parse_player_list(players_raw)

    log_path = os.path.join(cfg["path"], "logs", "latest.log")
    try:
        logs = tail_log(log_path, 20)
    except FileNotFoundError:
        logs = f"Log file not found: {log_path}"

    context = {
        "request": request,
        "players_raw": players_raw,
        "player_count": player_count,
        "player_list": player_list,
        "logs": logs,
        "result": result,
    }
    return templates.TemplateResponse("dashboard.html", context)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return render_dashboard(request)


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    cfg = load_config()
    if not cfg:
        return RedirectResponse("/", status_code=302)
    if hmac.compare_digest(hash_password(password), cfg.get("admin_password_hash", "")):
        response = RedirectResponse("/", status_code=302)
        response.set_cookie("session", cfg.get("admin_password_hash"), httponly=True)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password"})


@app.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("session")
    return response

@app.post("/setup")
async def setup(
    request: Request,
    server_dir: str = Form(...),
    host: str = Form(...),
    port: int = Form(...),
    password: str = Form(...),
    admin_password: str = Form(...),
):
    save_config({
        "path": server_dir,
        "host": host,
        "port": port,
        "password": password,
        "admin_password_hash": hash_password(admin_password),
    })
    return RedirectResponse("/", status_code=302)

@app.post("/command", response_class=HTMLResponse, dependencies=[Depends(require_auth)])
async def command(request: Request, cmd: str = Form(...)):
    client = get_client()
    try:
        result = client.command(cmd)
    finally:
        client.close()
    return render_dashboard(request, result)

@app.post("/broadcast", response_class=HTMLResponse, dependencies=[Depends(require_auth)])
async def broadcast(request: Request, message: str = Form(...)):
    client = get_client()
    try:
        result = client.command(f"say {message}")
    finally:
        client.close()
    return render_dashboard(request, result)

@app.post("/ban", response_class=HTMLResponse, dependencies=[Depends(require_auth)])
async def ban(request: Request, player: str = Form(...)):
    client = get_client()
    try:
        result = client.command(f"ban {player}")
    finally:
        client.close()
    return render_dashboard(request, result)

@app.post("/whitelist", response_class=HTMLResponse, dependencies=[Depends(require_auth)])
async def whitelist(request: Request, player: str = Form(...), action: str = Form("add")):
    client = get_client()
    try:
        result = client.command(f"whitelist {action} {player}")
    finally:
        client.close()
    return render_dashboard(request, result)

@app.post("/restart", response_class=HTMLResponse, dependencies=[Depends(require_auth)])
async def restart(request: Request):
    client = get_client()
    try:
        result = client.command("restart")
    finally:
        client.close()
    return render_dashboard(request, result)

@app.get("/logs", response_class=HTMLResponse, dependencies=[Depends(require_auth)])
async def logs(request: Request, lines: int = 50):
    cfg = load_config()
    if not cfg:
        return render_dashboard(request)
    log_path = os.path.join(cfg["path"], "logs", "latest.log")
    try:
        text = tail_log(log_path, lines)
    except FileNotFoundError:
        text = f"Log file not found: {log_path}"
    return HTMLResponse(f"<pre>{text}</pre><p><a href='/'>Back</a></p>")


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    cfg = load_config()
    if not cfg:
        await websocket.close()
        return
    token = websocket.cookies.get("session")
    if not token or not hmac.compare_digest(token, cfg.get("admin_password_hash", "")):
        await websocket.close()
        return
    log_path = os.path.join(cfg["path"], "logs", "latest.log")
    try:
        with open(log_path, "r", encoding="utf8") as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if line:
                    await websocket.send_text(line.rstrip())
                else:
                    await asyncio.sleep(1)
    except Exception:
        await websocket.close()


