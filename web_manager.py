import json
import os
from typing import Optional

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse


def html_page(title: str, body: str) -> HTMLResponse:
    """Return a basic HTML page with simple styling."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
            .container {{ max-width: 800px; margin: 2em auto; background: #fff; padding: 2em; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            form {{ margin-bottom: 1em; }}
            input, select {{ padding: 0.4em; margin: 0.2em 0; width: 100%; }}
            button {{ padding: 0.5em 1em; }}
            pre {{ background: #eee; padding: 1em; overflow: auto; }}
        </style>
    </head>
    <body>
        <div class="container">
            {body}
        </div>
    </body>
    </html>
    """
    return HTMLResponse(html)

from minecraft_manager import RCONClient, tail_log

CONFIG_PATH = 'server_config.json'

app = FastAPI(title="Minecraft Web Manager")


def load_config() -> Optional[dict]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf8") as f:
            return json.load(f)
    return None


def save_config(data: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf8") as f:
        json.dump(data, f, indent=2)


def render_setup() -> HTMLResponse:
    body = """
    <h2>Setup Server Connection</h2>
    <form method='post' action='/setup'>
      <label>Server folder path:<input type='text' name='path'></label><br>
      <label>RCON host:<input type='text' name='host' value='127.0.0.1'></label><br>
      <label>RCON port:<input type='number' name='port' value='25575'></label><br>
      <label>RCON password:<input type='password' name='password'></label><br>
      <button type='submit'>Save</button>
    </form>
    """
    return html_page("Setup", body)


def render_dashboard(result: Optional[str] = None) -> HTMLResponse:
    client = get_client()
    try:
        players = client.command("list")
    finally:
        client.close()

    cfg = load_config()
    log_text = ""
    if cfg:
        log_path = os.path.join(cfg["path"], "logs", "latest.log")
        try:
            log_text = tail_log(log_path, 20)
        except FileNotFoundError:
            log_text = f"Log file not found: {log_path}"

    msg = f"<p><strong>Result:</strong> {result}</p>" if result else ""
    body = f"""
    {msg}
    <form action='/command' method='post'>
      <input name='cmd' placeholder='Command'>
      <button type='submit'>Send</button>
    </form>
    <form action='/broadcast' method='post'>
      <input name='message' placeholder='Broadcast message'>
      <button type='submit'>Broadcast</button>
    </form>
    <form action='/ban' method='post'>
      <input name='player' placeholder='Player name'>
      <button type='submit'>Ban</button>
    </form>
    <form action='/whitelist' method='post'>
      <input name='player' placeholder='Whitelist player'>
      <select name='action'>
        <option value='add'>Add</option>
        <option value='remove'>Remove</option>
      </select>
      <button type='submit'>Update</button>
    </form>
    <form action='/restart' method='post'>
      <button type='submit'>Restart Server</button>
    </form>
    <h3>Online Players</h3>
    <pre>{players}</pre>
    <h3>Latest Logs</h3>
    <pre>{log_text}</pre>
    """
    return html_page("Dashboard", body)


@app.get('/', response_class=HTMLResponse)
async def index(result: str | None = None):
    """Main entry point showing setup or dashboard."""
    cfg = load_config()
    if not cfg:
        return render_setup()
    return render_dashboard(result)


@app.post('/setup')
async def setup(path: str = Form(...), host: str = Form(...), port: int = Form(...), password: str = Form(...)):
    save_config({"path": path, "host": host, "port": port, "password": password})
    return render_dashboard("Configuration saved")


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
    body = f"<pre>{resp}</pre><p><a href='/'>Back</a></p>"
    return html_page('Players', body)


@app.get('/broadcast', response_class=HTMLResponse)
async def broadcast_form():
    body = (
        "<h1>Broadcast Message</h1>"
        "<form method='post'>"
        "  <input type='text' name='message' placeholder='Message'>"
        "  <button type='submit'>Send</button>"
        "</form>"
        "<p><a href='/'>Back</a></p>"
    )
    return html_page('Broadcast', body)


@app.post('/broadcast', response_class=HTMLResponse)
async def broadcast(message: str = Form(...)):
    client = get_client()
    try:
        resp = client.command(f'say {message}')
    finally:
        client.close()
    return render_dashboard(resp)


@app.get('/ban', response_class=HTMLResponse)
async def ban_form():
    body = (
        "<h1>Ban Player</h1>"
        "<form method='post'>"
        "  <input type='text' name='player' placeholder='Player name'>"
        "  <button type='submit'>Ban</button>"
        "</form>"
        "<p><a href='/'>Back</a></p>"
    )
    return html_page('Ban Player', body)


@app.post('/ban', response_class=HTMLResponse)
async def ban(player: str = Form(...)):
    client = get_client()
    try:
        resp = client.command(f'ban {player}')
    finally:
        client.close()
    return render_dashboard(resp)


@app.post('/restart', response_class=HTMLResponse)
async def restart():
    client = get_client()
    try:
        resp = client.command('restart')
    finally:
        client.close()
    return render_dashboard(resp)


@app.get('/logs', response_class=HTMLResponse)
async def logs(lines: int = 50):
    cfg = load_config()
    if not cfg:
        return render_setup()
    log_path = os.path.join(cfg['path'], 'logs', 'latest.log')
    try:
        text = tail_log(log_path, lines)
    except FileNotFoundError:
        text = f'Log file not found: {log_path}'
    body = f"<pre>{text}</pre><p><a href='/'>Back</a></p>"
    return html_page('Logs', body)


@app.get('/command', response_class=HTMLResponse)
async def command_form():
    body = (
        "<h1>Send Command</h1>"
        "<form method='post'>"
        "  <input type='text' name='cmd' placeholder='Command'>"
        "  <button type='submit'>Send</button>"
        "</form>"
        "<p><a href='/'>Back</a></p>"
    )
    return html_page('Command', body)


@app.post('/command', response_class=HTMLResponse)
async def command(cmd: str = Form(...)):
    client = get_client()
    try:
        resp = client.command(cmd)
    finally:
        client.close()
 464hqa-codex/corriger-l-erreur--nameerror--main-not-defined
    return render_dashboard(resp)


@app.post('/whitelist', response_class=HTMLResponse)
async def whitelist(player: str = Form(...), action: str = Form('add')):
    client = get_client()
    try:
        resp = client.command(f'whitelist {action} {player}')
    finally:
        client.close()
    return render_dashboard(resp)

