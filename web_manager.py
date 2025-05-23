import json
import os
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from minecraft_manager import RCONClient, tail_log

CONFIG_FILE = "web_config.json"
TEMPLATES_DIR = "templates"

app = FastAPI()
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def load_config() -> Optional[dict]:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    return None


def save_config(data: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf8") as f:
        json.dump(data, f)


def rcon_client() -> RCONClient:
    conf = load_config()
    if conf is None:
        raise RuntimeError("Server not configured")
    client = RCONClient(conf["host"], conf["port"], conf["password"])
    client.connect()
    return client


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    config = load_config()
    if not config:
        folders = [d for d in os.listdir("/opt") if os.path.isdir(os.path.join("/opt", d))]
        return templates.TemplateResponse("setup.html", {"request": request, "folders": folders})
    log_file = os.path.join(config["server_dir"], "logs", "latest.log")
    log = ""
    if os.path.exists(log_file):
        log = tail_log(log_file, 20)
    return templates.TemplateResponse("dashboard.html", {"request": request, "config": config, "log": log, "response": None})


@app.post("/setup")
async def setup(server_dir: str = Form(...), host: str = Form(...), port: int = Form(...), password: str = Form(...)):
    save_config({"server_dir": server_dir, "host": host, "port": port, "password": password})
    return RedirectResponse("/", status_code=303)


@app.post("/command", response_class=HTMLResponse)
async def send_command(request: Request, cmd: str = Form(...)):
    resp = ""
    try:
        client = rcon_client()
        resp = client.command(cmd)
    finally:
        if 'client' in locals():
            client.close()
    config = load_config()
    log_file = os.path.join(config["server_dir"], "logs", "latest.log")
    log = tail_log(log_file, 20) if os.path.exists(log_file) else ""
    return templates.TemplateResponse("dashboard.html", {"request": request, "config": config, "log": log, "response": resp})


@app.post("/broadcast", response_class=HTMLResponse)
async def broadcast(request: Request, message: str = Form(...)):
    resp = ""
    try:
        client = rcon_client()
        resp = client.command(f"say {message}")
    finally:
        if 'client' in locals():
            client.close()
    config = load_config()
    log_file = os.path.join(config["server_dir"], "logs", "latest.log")
    log = tail_log(log_file, 20) if os.path.exists(log_file) else ""
    return templates.TemplateResponse("dashboard.html", {"request": request, "config": config, "log": log, "response": resp})


@app.post("/ban", response_class=HTMLResponse)
async def ban(request: Request, player: str = Form(...)):
    resp = ""
    try:
        client = rcon_client()
        resp = client.command(f"ban {player}")
    finally:
        if 'client' in locals():
            client.close()
    config = load_config()
    log_file = os.path.join(config["server_dir"], "logs", "latest.log")
    log = tail_log(log_file, 20) if os.path.exists(log_file) else ""
    return templates.TemplateResponse("dashboard.html", {"request": request, "config": config, "log": log, "response": resp})


@app.post("/restart", response_class=HTMLResponse)
async def restart(request: Request):
    resp = ""
    try:
        client = rcon_client()
        resp = client.command("restart")
    finally:
        if 'client' in locals():
            client.close()
    config = load_config()
    log_file = os.path.join(config["server_dir"], "logs", "latest.log")
    log = tail_log(log_file, 20) if os.path.exists(log_file) else ""
    return templates.TemplateResponse("dashboard.html", {"request": request, "config": config, "log": log, "response": resp})

