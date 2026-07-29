"""Deny non-loopback network connections in Privacy Studio Python processes."""

from __future__ import annotations

import ipaddress
import socket
from typing import Any

_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex
_original_create_connection = socket.create_connection
_original_getaddrinfo = socket.getaddrinfo


def _host_is_local(host: Any) -> bool:
    if host in (None, "", "localhost"):
        return True
    if isinstance(host, bytes):
        host = host.decode("ascii", errors="ignore")
    if not isinstance(host, str):
        return False
    host = host.removeprefix("[").removesuffix("]")
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host.casefold() == "localhost"


def _address_is_local(address: Any) -> bool:
    if isinstance(address, tuple) and address:
        return _host_is_local(address[0])
    # Unix-domain sockets and platform-specific local address forms are allowed.
    return not isinstance(address, tuple)


def _deny(address: Any) -> None:
    if not _address_is_local(address):
        raise PermissionError(
            "Privacy Studio ha bloccato una connessione di rete non locale."
        )


def guarded_connect(self: socket.socket, address: Any) -> None:
    _deny(address)
    return _original_connect(self, address)


def guarded_connect_ex(self: socket.socket, address: Any) -> int:
    try:
        _deny(address)
    except PermissionError:
        return 13
    return _original_connect_ex(self, address)


def guarded_create_connection(
    address: Any,
    timeout: object = socket._GLOBAL_DEFAULT_TIMEOUT,
    source_address: Any = None,
    *,
    all_errors: bool = False,
) -> socket.socket:
    _deny(address)
    return _original_create_connection(
        address,
        timeout,
        source_address,
        all_errors=all_errors,
    )


def guarded_getaddrinfo(
    host: Any,
    port: Any,
    family: int = 0,
    type: int = 0,
    proto: int = 0,
    flags: int = 0,
):
    if not _host_is_local(host):
        raise socket.gaierror(
            socket.EAI_NONAME,
            "Privacy Studio consente soltanto nomi e indirizzi loopback.",
        )
    return _original_getaddrinfo(host, port, family, type, proto, flags)


socket.socket.connect = guarded_connect
socket.socket.connect_ex = guarded_connect_ex
socket.create_connection = guarded_create_connection
socket.getaddrinfo = guarded_getaddrinfo
