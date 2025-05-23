# Minecraft Server Manager

This repository provides utilities to manage a Minecraft server using the RCON protocol. It includes a command line tool and a lightweight web interface.

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

### Web Interface

You can also run a small web UI to manage the server. Launch it with:

```bash
uvicorn web_manager:app --reload --port 8000
```

On first launch the app asks for the path to your server folder as well as the
RCON connection details. These settings are saved in `server_config.json`.
After configuration, open <http://localhost:8000> in a browser to access
actions like viewing players online, banning, broadcasting messages, restarting
the server and tailing the latest log file.

