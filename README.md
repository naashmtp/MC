# Minecraft Server Manager

## Features

- Connect to a server via RCON
- List online players and server status
- Ban players
- Broadcast messages
- Restart the server
- Send arbitrary commands
- Tail the server log file
- Manage the server whitelist

Enable RCON in your `server.properties` file:

```
enable-rcon=true
rcon.port=25575
rcon.password=<your_password>
```

Install Python 3.9+ and run the script:

```
python minecraft_manager.py --host <server-host> --password <rcon-password> <command> [options]
```

Examples:

```bash
# List players online
python minecraft_manager.py --host 127.0.0.1 --password secret players

# Broadcast a message
python minecraft_manager.py --host 127.0.0.1 --password secret broadcast "Server maintenance soon!"

# Ban a player
python minecraft_manager.py --host 127.0.0.1 --password secret ban Notch

# Show the last 50 lines of the log file
python minecraft_manager.py --host 127.0.0.1 --password secret --log-file /path/to/latest.log logs --lines 50
```

Note: the restart command simply sends `restart` through RCON. You must have a plugin or script handling server restarts.

## Web Dashboard

This project also includes a small FastAPI application that lets you manage the server from a browser.

### Setup

Install the web dependencies:

```bash
pip install fastapi uvicorn jinja2
```

Start the dashboard with:

```bash
uvicorn web_manager:app --host 0.0.0.0 --port 8000
```

ra4pg6-codex/ajouter-une-route-de-connexion-avec-authentification
Open `http://localhost:8000` to configure the connection to your Minecraft server. During setup you will be asked for an admin password used to access the dashboard. Once configured you can log in and send commands, broadcast messages, ban or whitelist players, restart the server and view the latest log lines.


On first launch you will be asked for the server directory, RCON details and an admin password. The password is stored as a SHA256 hash in `server_config.json` and is required to log in. The dashboard then allows you to manage the server entirely from your browser.
