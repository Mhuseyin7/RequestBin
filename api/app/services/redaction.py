SENSITIVE_HEADERS = {"authorization", "proxy-authorization", "cookie", "set-cookie", "x-api-key"}
def redact_headers(headers: dict[str, str], reveal: bool = False) -> dict[str, str]:
    if reveal: return headers
    result = {}
    for key, value in headers.items():
        result[key] = value if key.lower() not in SENSITIVE_HEADERS else (value[:10] + "••••••••" + value[-4:] if len(value) > 14 else "••••••••")
    return result
