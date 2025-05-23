import json
import os
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from minecraft_manager import RCONClient, tail_log

CONFIG_PATH = 'config.json'

app = FastAPI()
templates = Jinja2Templates(directory='templates')


def load_config() -> Optional[dict]:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return None

def save_config(cfg: dict):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(cfg, f)


def rcon_command(cfg: dict, cmd: str) -> str:
    client = RCONClient(cfg['host'], cfg['port'], cfg['password'])
    client.connect()
    try:
        return client.command(cmd)
    finally:
        client.close()


def available_dirs(path: str = '/opt'):
    try:
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    except FileNotFoundError:
        return []


@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    cfg = load_config()
    if not cfg:
        return RedirectResponse('/setup')
    players = rcon_command(cfg, 'list')
    log_file = os.path.join(cfg['server_dir'], 'logs/latest.log')
    logs = tail_log(log_file, 20) if os.path.exists(log_file) else 'No logs found.'
    return templates.TemplateResponse('dashboard.html', {
        'request': request,
        'players': players,
        'logs': logs,
        'result': None,
    })


@app.get('/setup', response_class=HTMLResponse)
async def setup_form(request: Request):
    if load_config():
        return RedirectResponse('/')
    dirs = available_dirs('/opt')
    return templates.TemplateResponse('setup.html', {'request': request, 'dirs': dirs})


@app.post('/setup', response_class=HTMLResponse)
async def setup(request: Request, server_dir: str = Form(...), host: str = Form(...), port: int = Form(...), password: str = Form(...)):
    save_config({'server_dir': server_dir, 'host': host, 'port': port, 'password': password})
    return RedirectResponse('/', status_code=303)


@app.post('/command', response_class=HTMLResponse)
async def command(request: Request, cmd: str = Form(...)):
    cfg = load_config()
    if not cfg:
        return RedirectResponse('/setup')
    result = rcon_command(cfg, cmd)
    players = rcon_command(cfg, 'list')
    log_file = os.path.join(cfg['server_dir'], 'logs/latest.log')
    logs = tail_log(log_file, 20) if os.path.exists(log_file) else 'No logs found.'
    return templates.TemplateResponse('dashboard.html', {
        'request': request,
        'players': players,
        'logs': logs,
        'result': result,
    })


@app.post('/broadcast', response_class=HTMLResponse)
async def broadcast(request: Request, message: str = Form(...)):
    return await command(request, cmd=f'say {message}')


@app.post('/ban', response_class=HTMLResponse)
async def ban(request: Request, player: str = Form(...)):
    return await command(request, cmd=f'ban {player}')


@app.post('/restart', response_class=HTMLResponse)
async def restart(request: Request):
    return await command(request, cmd='restart')

