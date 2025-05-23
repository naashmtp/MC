import json
import os
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from minecraft_manager import RCONClient, tail_log

CONFIG_PATH = "server_config.json"

app = FastAPI(title="Minecraft Web Manager")
templates = Jinja2Templates(directory="templates")


def load_config() -> Optional[dict]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf8") as f:
            return json.load(f)
    return None


def save_config(data: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf8") as f:
        json.dump(data, f, indent=2)


def get_client() -> RCONClient:
    cfg = load_config()
    if not cfg:
        raise RuntimeError("Server not configured")
    client = RCONClient(cfg["host"], cfg["port"], cfg["password"])
    client.connect()
    return client


def render_dashboard(request: Request, result: Optional[str] = None) -> HTMLResponse:
    cfg = load_config()
    if not cfg:
        dirs = [d for d in os.listdir("/opt") if os.path.isdir(os.path.join("/opt", d))]
        return templates.TemplateResponse("setup.html", {"request": request, "dirs": dirs})

    client = get_client()
    try:
        players = client.command("list")
    finally:
        client.close()

    log_path = os.path.join(cfg["path"], "logs", "latest.log")
    try:
        logs = tail_log(log_path, 20)
    except FileNotFoundError:
        logs = f"Log file not found: {log_path}"

    context = {
        "request": request,
        "players": players,
        "logs": logs,
        "result": result,
    }
    return templates.TemplateResponse("dashboard.html", context)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return render_dashboard(request)


@app.post("/setup")
async def setup(
    request: Request,
    server_dir: str = Form(...),
    host: str = Form(...),
    port: int = Form(...),
    password: str = Form(...),
):
    save_config({"path": server_dir, "host": host, "port": port, "password": password})
    return RedirectResponse("/", status_code=302)


@app.post("/command", response_class=HTMLResponse)
async def command(request: Request, cmd: str = Form(...)):
    client = get_client()
    try:
        result = client.command(cmd)
    finally:
        client.close()
    return render_dashboard(request, result)


@app.post("/broadcast", response_class=HTMLResponse)
async def broadcast(request: Request, message: str = Form(...)):
    client = get_client()
    try:
        result = client.command(f"say {message}")
    finally:
        client.close()
    return render_dashboard(request, result)


@app.post("/ban", response_class=HTMLResponse)
async def ban(request: Request, player: str = Form(...)):
    client = get_client()
    try:
        result = client.command(f"ban {player}")
    finally:
        client.close()
    return render_dashboard(request, result)


@app.post("/restart", response_class=HTMLResponse)
async def restart(request: Request):
    client = get_client()
    try:
        result = client.command("restart")
    finally:
        client.close()
    return render_dashboard(request, result)


@app.post("/whitelist", response_class=HTMLResponse)
async def whitelist(
    request: Request,
    player: str = Form(...),
    action: str = Form(...),  # "add" or "remove"
):
    client = get_client()
    try:
        if action == "remove":
            result = client.command(f"whitelist remove {player}")
        else:
            result = client.command(f"whitelist add {player}")
    finally:
        client.close()
    return render_dashboard(request, result)

