import ipaddress, socket
from urllib.parse import urlparse
from fastapi import HTTPException
from ..config import get_settings

def validate_target(url: str) -> None:
    parsed = urlparse(url)
    try: port = parsed.port
    except ValueError: raise HTTPException(422, "Invalid target port")
    hostname = (parsed.hostname or "").rstrip(".").lower()
    blocked_names = {"localhost", "metadata.google.internal", "metadata.google.com", "instance-data.ec2.internal"}
    if parsed.scheme not in {"http", "https"} or not hostname or parsed.username or parsed.password or hostname in blocked_names:
        raise HTTPException(422, "Only absolute HTTP(S) URLs are allowed")
    if get_settings().allow_unsafe_outbound: return
    try: addresses = {item[4][0] for item in socket.getaddrinfo(hostname, port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)}
    except socket.gaierror: raise HTTPException(422, "Target hostname cannot be resolved")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise HTTPException(422, "Private, local, and metadata targets are blocked")
