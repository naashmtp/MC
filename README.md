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

 l7slgt-codex/corriger-l-erreur--nameerror--main-not-defined
## Web Dashboard

This project also includes a small FastAPI application that lets you manage the server from a browser. Install the web dependencies and run Uvicorn:

## Web Interface

p0df9a-codex/corriger-l-erreur--nameerror--main-not-defined
This repository also provides a small FastAPI application offering a web-based dashboard.
Install the extra dependencies and launch the server with:
main

```bash
pip install fastapi uvicorn jinja2
uvicorn web_manager:app --host 0.0.0.0 --port 8000
```

l7slgt-codex/corriger-l-erreur--nameerror--main-not-defined
Open `http://localhost:8000` to configure the connection to your Minecraft server. Once configured you can send commands, broadcast messages, ban or whitelist players, restart the server and view the latest log lines.

Once running, open your browser to the chosen host and port. The interface allows
you to send commands, broadcast messages, ban players, manage the whitelist and
view recent logs directly from your browser.


Run the FastAPI app with `uvicorn`:

```bash
uvicorn web_manager:app --host 0.0.0.0 --port 8000
```

On first launch you will be asked for the server directory and RCON details.
The dashboard then allows you to send commands, broadcast messages, ban or
whitelist players, restart the server and view recent log entries.
main
main

