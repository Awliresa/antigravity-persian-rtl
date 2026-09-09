# cdp_client.py
"""
سبک‌ترین WebSocket/CDP کلاینت بدون dependency خارجی
Compatible with Python 3.8+
"""

import socket
import urllib.request
import json
import base64
import os
import struct
import urllib.parse


def send_cdp_command(ws_url: str, method: str, params: dict = None, timeout: float = 8.0) -> dict:
    """
    یک دستور CDP (Chrome DevTools Protocol) را از طریق WebSocket ارسال می‌کند
    و نتیجه JSON را برمی‌گرداند.
    
    Args:
        ws_url:  WebSocket URL از /json endpoint (مثل ws://127.0.0.1:PORT/devtools/page/...)
        method:  نام متد CDP (مثل Runtime.evaluate)
        params:  پارامترهای JSON متد
        timeout: تایم‌اوت ثانیه
    """
    parsed = urllib.parse.urlparse(ws_url)
    host = parsed.hostname
    port = parsed.port
    path = parsed.path

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)

    try:
        s.connect((host, port))

        # ─── WebSocket Handshake ───────────────────────────────────────────────
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        s.sendall(handshake.encode("ascii"))

        # خواندن response headers تا رسیدن به \r\n\r\n
        header_buf = b""
        while b"\r\n\r\n" not in header_buf:
            chunk = s.recv(1024)
            if not chunk:
                break
            header_buf += chunk

        if b"101 " not in header_buf:
            raise RuntimeError(
                "WebSocket handshake failed: " + header_buf.decode("ascii", errors="ignore")[:200]
            )

        # ─── ارسال پیام (client → server, masked) ─────────────────────────────
        payload = json.dumps({
            "id": 1,
            "method": method,
            "params": params or {}
        }).encode("utf-8")

        mask = os.urandom(4)
        length = len(payload)

        if length <= 125:
            header = bytearray([0x81, 0x80 | length])
        elif length <= 65535:
            header = bytearray([0x81, 0x80 | 126]) + struct.pack("!H", length)
        else:
            header = bytearray([0x81, 0x80 | 127]) + struct.pack("!Q", length)

        masked_payload = bytearray(payload[i] ^ mask[i % 4] for i in range(length))
        s.sendall(header + mask + masked_payload)

        # ─── دریافت پاسخ (server → client, unmasked) ─────────────────────────
        # حلقه برای مدیریت frames بزرگ‌تر از بافر اولیه
        raw = _recv_full_frame(s)

        if len(raw) < 2:
            return {}

        # تجزیه هدر WebSocket frame
        second_byte = raw[1]
        pay_len = second_byte & 0x7F
        offset = 2

        if pay_len == 126:
            if len(raw) < 4:
                return {}
            pay_len = struct.unpack("!H", raw[2:4])[0]
            offset = 4
        elif pay_len == 127:
            if len(raw) < 10:
                return {}
            pay_len = struct.unpack("!Q", raw[2:10])[0]
            offset = 10

        # اگر هنوز داده کافی نداریم، بیشتر دریافت کن
        while len(raw) < offset + pay_len:
            chunk = s.recv(65536)
            if not chunk:
                break
            raw += chunk

        data = raw[offset: offset + pay_len].decode("utf-8", errors="ignore")
        if not data:
            return {}
        return json.loads(data)

    finally:
        try:
            s.close()
        except Exception:
            pass


def _recv_full_frame(s: socket.socket, initial_buf_size: int = 65536) -> bytes:
    """
    یک frame کامل WebSocket را از socket می‌خواند.
    برای frames بزرگ به‌صورت حلقه‌ای عمل می‌کند.
    """
    raw = b""
    try:
        raw = s.recv(initial_buf_size)
        if len(raw) < 2:
            return raw

        # طول payload را از هدر استخراج می‌کنیم
        pay_len_indicator = raw[1] & 0x7F
        if pay_len_indicator <= 125:
            total_expected = 2 + pay_len_indicator
        elif pay_len_indicator == 126:
            if len(raw) < 4:
                return raw
            total_expected = 4 + struct.unpack("!H", raw[2:4])[0]
        else:  # 127
            if len(raw) < 10:
                return raw
            total_expected = 10 + struct.unpack("!Q", raw[2:10])[0]

        # دریافت تا رسیدن به اندازه کامل
        while len(raw) < total_expected:
            chunk = s.recv(min(65536, total_expected - len(raw)))
            if not chunk:
                break
            raw += chunk

    except socket.timeout:
        pass
    return raw
