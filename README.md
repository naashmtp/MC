# Minecraft Server Manager

This repository provides a simple command line utility to manage a Minecraft server using the RCON protocol.

## Features

- Connect to a server via RCON
- List online players and server status
- Ban players
- Broadcast messages
- Restart the server
- Send arbitrary commands
- Tail the server log file

## Usage

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


## Web App

A simple FastAPI web app is provided to manage the server through a browser. Run:

```bash
uvicorn web_manager:app --reload
```

On first start, open `http://localhost:8000` and enter the path to your Minecraft
server directory along with the RCON connection details. After saving, the app
lets you view logs, list players, send commands, ban players and restart the
server from the web interface.

