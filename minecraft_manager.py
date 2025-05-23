import argparse
import os
import socket
import struct
from typing import Optional

# Basic RCON protocol implementation
class RCONClient:
    def __init__(self, host: str, port: int, password: str, timeout: float = 3.0):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self.request_id = 0

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)
        if not self._login():
            raise ConnectionError("Failed to authenticate with RCON server")

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def _send_packet(self, packet_type: int, body: str) -> int:
        if self.sock is None:
            raise RuntimeError("RCON socket is not connected")
        self.request_id += 1
        payload = (
            struct.pack('<ii', self.request_id, packet_type)
            + body.encode("utf8")
            + b"\x00\x00"
        )
        packet = struct.pack("<i", len(payload)) + payload
        self.sock.sendall(packet)
        return self.request_id

    def _recv_packet(self) -> tuple[int, int, str]:
        if self.sock is None:
            raise RuntimeError("RCON socket is not connected")
        raw_len = self.sock.recv(4)
        if len(raw_len) < 4:
            raise ConnectionError("Unexpected EOF")
        (length,) = struct.unpack('<i', raw_len)
        payload = b''
        while len(payload) < length:
            data = self.sock.recv(length - len(payload))
            if not data:
                raise ConnectionError("Unexpected EOF while reading packet")
            payload += data
        req_id, pkt_type = struct.unpack('<ii', payload[:8])
        body = payload[8:-2].decode('utf8', errors='replace')
        return req_id, pkt_type, body

    def _login(self) -> bool:
        self._send_packet(3, self.password)
        req_id, pkt_type, body = self._recv_packet()
        if req_id == -1 or pkt_type != 2:
            return False
        return True

    def command(self, cmd: str) -> str:
        self._send_packet(2, cmd)
        _req_id, _pkt_type, body = self._recv_packet()
        return body


def parse_args():
    parser = argparse.ArgumentParser(description="Basic Minecraft server manager via RCON")
    parser.add_argument('--host', required=True, help='Server host')
    parser.add_argument('--port', type=int, default=25575, help='RCON port (default: 25575)')
    parser.add_argument('--password', required=True, help='RCON password')
    parser.add_argument('--log-file', help='Path to server log file for log operations')

    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('players', help='List online players')
    subparsers.add_parser('status', help='Get server status (uses command list)')

    ban_p = subparsers.add_parser('ban', help='Ban a player')
    ban_p.add_argument('player', help='Player name to ban')

    msg_p = subparsers.add_parser('broadcast', help='Broadcast a message to all players')
    msg_p.add_argument('message', help='Message to broadcast')

    subparsers.add_parser('restart', help='Send restart command to the server')

    log_p = subparsers.add_parser('logs', help='Show last lines of log file')
    log_p.add_argument('--lines', type=int, default=20, help='Number of log lines to show')

    cmd_p = subparsers.add_parser('command', help='Send raw command')
    cmd_p.add_argument('cmd', help='Command string')

    return parser.parse_args()


def tail_log(path: str, lines: int = 20) -> str:
    """Return the last ``lines`` lines from ``path``.

    The function reads the file from the end in blocks so it can efficiently
    return the requested number of lines even for large log files.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    target_lines = max(0, lines)
    remaining_lines = target_lines

    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        end = f.tell()
        block_size = 8192
        data = b""

        while end > 0 and remaining_lines > 0:
            start = max(0, end - block_size)
            f.seek(start)
            chunk = f.read(end - start)
            data = chunk + data
            remaining_lines -= chunk.count(b"\n")
            end = start

        text = data.decode("utf8", errors="replace")
        return "\n".join(text.splitlines()[-target_lines:])


def main():
    args = parse_args()
    if args.command == 'logs':
        if not args.log_file:
            print('Log file path is required for logs command')
            return
        print(tail_log(args.log_file, args.lines))
        return

    manager = RCONClient(args.host, args.port, args.password)
    manager.connect()
    try:
        if args.command == 'players':
            resp = manager.command('list')
            print(resp)
        elif args.command == 'status':
            resp = manager.command('list')
            print(resp)
        elif args.command == 'ban':
            resp = manager.command(f'ban {args.player}')
            print(resp)
        elif args.command == 'broadcast':
            resp = manager.command(f'say {args.message}')
            print(resp)
        elif args.command == 'restart':
            resp = manager.command('restart')
            print(resp)
        elif args.command == 'command':
            resp = manager.command(args.cmd)
            print(resp)
        else:
            print('No command given. Use -h for help.')
    finally:
        manager.close()


if __name__ == '__main__':
    main()
