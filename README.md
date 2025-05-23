# Minecraft Server Manager

This repository provides utilities to manage a Minecraft server using the RCON protocol. A command line client is provided as well as a small web interface.

## Features

- Connect to a server via RCON
- List online players and server status
- Ban players
- Broadcast messages
- Restart the server
- Send arbitrary commands
- Tail the server log file
- Simple web dashboard

## Command Line Usage

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

A small FastAPI application provides a basic dashboard. Start it with `uvicorn`:

```bash
uvicorn web_manager:app --reload
```

On first launch it will ask for the Minecraft server directory and RCON details. It lists all folders found under `/opt` so you can easily select your server. After saving, the dashboard lets you send commands, broadcast messages, ban players, restart the server, and view the latest log entries and online players.
