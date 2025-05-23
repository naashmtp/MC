import json
import os
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from minecraft_manager import RCONClient, tail_log

app = FastAPI()
CONFIG_PATH = Path("config.json")


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return None


def save_config(cfg: dict):
    CONFIG_PATH.write_text(json.dumps(cfg))


def get_client(cfg: dict) -> RCONClient:
    client = RCONClient(cfg["host"], cfg.get("port", 25575), cfg["password"])
    client.connect()
    return client


@app.get("/", response_class=HTMLResponse)
async def index():
    cfg = load_config()
    if not cfg:
        return HTMLResponse(
            """
            <h1>Configuration</h1>
            <form method='post' action='/configure'>
                <label>Server directory:<input name='server_dir' required></label><br>
                <label>RCON host:<input name='host' value='127.0.0.1' required></label><br>
                <label>RCON port:<input name='port' value='25575'></label><br>
                <label>RCON password:<input name='password' type='password' required></label><br>
                <button type='submit'>Save</button>
            </form>
            """
        )
    html = ["<h1>Minecraft Manager</h1>"]
    html.append("<a href='/logs'>View Logs</a> | <a href='/players'>Players</a>")
    html.append(
        """
        <h2>Send Command</h2>
        <form method='post' action='/command'>
            <input name='cmd' placeholder='command'>
            <button type='submit'>Send</button>
        </form>
        """
    )
    html.append(
        """
        <h2>Broadcast Message</h2>
        <form method='post' action='/broadcast'>
            <input name='msg' placeholder='message'>
            <button type='submit'>Broadcast</button>
        </form>
        """
    )
    html.append(
        """
        <h2>Ban Player</h2>
        <form method='post' action='/ban'>
            <input name='player' placeholder='player'>
            <button type='submit'>Ban</button>
        </form>
        """
    )
    html.append(
        """
        <form method='post' action='/restart'>
            <button type='submit'>Restart Server</button>
        </form>
        """
    )
    return HTMLResponse("\n".join(html))


@app.post("/configure")
async def configure(
    server_dir: str = Form(...),
    host: str = Form(...),
    port: int = Form(25575),
    password: str = Form(...),
):
    save_config({"server_dir": server_dir, "host": host, "port": port, "password": password})
    return RedirectResponse("/", status_code=303)


@app.get("/players", response_class=HTMLResponse)
async def players():
    cfg = load_config()
    if not cfg:
        return RedirectResponse("/")
    client = get_client(cfg)
    try:
        resp = client.command("list")
    finally:
        client.close()
    return HTMLResponse(f"<pre>{resp}</pre><a href='/'>Back</a>")


@app.get("/logs", response_class=HTMLResponse)
async def logs():
    cfg = load_config()
    if not cfg:
        return RedirectResponse("/")
    log_path = Path(cfg["server_dir"]) / "logs/latest.log"
    try:
        text = tail_log(str(log_path), 50)
    except FileNotFoundError:
        text = f"Log file not found: {log_path}"
    return HTMLResponse(f"<pre>{text}</pre><a href='/'>Back</a>")


@app.post("/command")
async def send_command(cmd: str = Form(...)):
    cfg = load_config()
    if not cfg:
        return RedirectResponse("/")
    client = get_client(cfg)
    try:
        resp = client.command(cmd)
    finally:
        client.close()
    return HTMLResponse(f"<pre>{resp}</pre><a href='/'>Back</a>")


@app.post("/broadcast")
async def broadcast(msg: str = Form(...)):
    return await send_command(f"say {msg}")


@app.post("/ban")
async def ban(player: str = Form(...)):
    return await send_command(f"ban {player}")


@app.post("/restart")
async def restart():
    return await send_command("restart")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
