import ipaddress, socket
from urllib.parse import urlparse
from fastapi import HTTPException
from ..config import get_settings

def validate_target(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(422, "Only absolute HTTP(S) URLs are allowed")
    if get_settings().allow_unsafe_outbound: return
    try: addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)}
    except socket.gaierror: raise HTTPException(422, "Target hostname cannot be resolved")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise HTTPException(422, "Private, local, and metadata targets are blocked")
