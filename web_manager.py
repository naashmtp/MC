import json
import os
from typing import Optional

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from minecraft_manager import RCONClient, tail_log

CONFIG_PATH = 'server_config.json'

app = FastAPI(title="Minecraft Web Manager")
main


def load_config() -> Optional[dict]:
    if os.path.exists(CONFIG_PATH):

        with open(CONFIG_PATH, 'r', encoding='utf8') as f:
            return json.load(f)
    return None


def save_config(data: dict) -> None:
    with open(CONFIG_PATH, 'w', encoding='utf8') as f:
        json.dump(data, f, indent=2)


@app.get('/', response_class=HTMLResponse)
async def index():
    cfg = load_config()
    if not cfg:
        return HTMLResponse(
            """
            <h1>Setup Server Connection</h1>
            <form method='post' action='/setup'>
              <label>Server folder path: <input type='text' name='path'></label><br>
              <label>RCON host: <input type='text' name='host' value='127.0.0.1'></label><br>
              <label>RCON port: <input type='number' name='port' value='25575'></label><br>
              <label>RCON password: <input type='password' name='password'></label><br>
              <button type='submit'>Save</button>
            </form>
            """
        )

    return HTMLResponse(
        """
        <h1>Minecraft Server Manager</h1>
        <ul>
          <li><a href='/players'>Players Online</a></li>
          <li><a href='/broadcast'>Broadcast Message</a></li>
          <li><a href='/ban'>Ban Player</a></li>
          <li><a href='/restart'>Restart Server</a></li>
          <li><a href='/logs'>View Logs</a></li>
          <li><a href='/command'>Send Command</a></li>
        </ul>
        """
    )


@app.post('/setup')
async def setup(path: str = Form(...), host: str = Form(...), port: int = Form(...), password: str = Form(...)):
    save_config({"path": path, "host": host, "port": port, "password": password})
    return RedirectResponse('/', status_code=302)


def get_client() -> RCONClient:
    cfg = load_config()
    if not cfg:
        raise RuntimeError('Server not configured')
    client = RCONClient(cfg['host'], cfg['port'], cfg['password'])
    client.connect()
    return client


@app.get('/players', response_class=HTMLResponse)
async def players():
    client = get_client()
    try:
        resp = client.command('list')
    finally:
        client.close()
    return HTMLResponse(f"<pre>{resp}</pre><p><a href='/'>Back</a></p>")


@app.get('/broadcast', response_class=HTMLResponse)
async def broadcast_form():
    return HTMLResponse(
        """
        <h1>Broadcast Message</h1>
        <form method='post'>
          <input type='text' name='message' placeholder='Message'>
          <button type='submit'>Send</button>
        </form>
        <p><a href='/'>Back</a></p>
        """
    )


@app.post('/broadcast', response_class=HTMLResponse)
async def broadcast(message: str = Form(...)):
    client = get_client()
    try:
        resp = client.command(f'say {message}')
    finally:
        client.close()
    return HTMLResponse(f"<pre>{resp}</pre><p><a href='/'>Back</a></p>")


@app.get('/ban', response_class=HTMLResponse)
async def ban_form():
    return HTMLResponse(
        """
        <h1>Ban Player</h1>
        <form method='post'>
          <input type='text' name='player' placeholder='Player name'>
          <button type='submit'>Ban</button>
        </form>
        <p><a href='/'>Back</a></p>
        """
    )


@app.post('/ban', response_class=HTMLResponse)
async def ban(player: str = Form(...)):
    client = get_client()
    try:
        resp = client.command(f'ban {player}')
    finally:
        client.close()
    return HTMLResponse(f"<pre>{resp}</pre><p><a href='/'>Back</a></p>")


@app.get('/restart', response_class=HTMLResponse)
async def restart():
    client = get_client()
    try:
        resp = client.command('restart')
    finally:
        client.close()
    return HTMLResponse(f"<pre>{resp}</pre><p><a href='/'>Back</a></p>")


@app.get('/logs', response_class=HTMLResponse)
async def logs(lines: int = 50):
    cfg = load_config()
    if not cfg:
        return RedirectResponse('/', status_code=302)
    log_path = os.path.join(cfg['path'], 'logs', 'latest.log')
    try:
        text = tail_log(log_path, lines)
    except FileNotFoundError:
        text = f'Log file not found: {log_path}'
    html = f"<pre>{text}</pre><p><a href='/'>Back</a></p>"
    return HTMLResponse(html)


@app.get('/command', response_class=HTMLResponse)
async def command_form():
    return HTMLResponse(
        """
        <h1>Send Command</h1>
        <form method='post'>
          <input type='text' name='cmd' placeholder='Command'>
          <button type='submit'>Send</button>
        </form>
        <p><a href='/'>Back</a></p>
        """
    )


@app.post('/command', response_class=HTMLResponse)
async def command(cmd: str = Form(...)):
    client = get_client()
    try:
        resp = client.command(cmd)
    finally:
        client.close()
    return HTMLResponse(f"<pre>{resp}</pre><p><a href='/'>Back</a></p>")
main
