# Minecraft Server Manager

 

## Features

- Connect to a server via RCON
- List online players and server status
- Ban players
- Broadcast messages
- Restart the server
- Send arbitrary commands
- Tail the server log file
- Manage the server from a web dashboard


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

## Web Interface

Install `fastapi`, `uvicorn`, and `jinja2` in your environment. Then run:

```bash
uvicorn web_manager:app --host 0.0.0.0 --port 8000
```

Open `http://<server>:8000` in your browser to access the dashboard. The first
visit lets you configure the server directory and RCON credentials. Afterwards
you can send commands, broadcast messages, ban or whitelist players, restart the
server, and view recent log output.

