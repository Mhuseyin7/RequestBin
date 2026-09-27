import json, shlex
from .redaction import redact_headers
def curl(method: str, url: str, headers: dict[str,str], body: str | None) -> str:
    parts = ["curl", "-X", shlex.quote(method), shlex.quote(url)]
    for name, value in redact_headers(headers).items(): parts += ["-H", shlex.quote(f"{name}: {value}")]
    if body: parts += ["--data-raw", shlex.quote(body)]
    return " ".join(parts)
def snippets(method: str, url: str, headers: dict[str,str], body: str | None) -> dict[str,str]:
    clean = redact_headers(headers); data = json.dumps(body or "")
    return {"curl":curl(method,url,headers,body), "javascript":f"await fetch({json.dumps(url)}, {{ method: {json.dumps(method)}, headers: {json.dumps(clean)}, body: {data} }});", "python":f"requests.request({method!r}, {url!r}, headers={clean!r}, data={body!r})", "php":f"$response = $client->request('{method}', '{url}');", "go":f"req, _ := http.NewRequest(\"{method}\", \"{url}\", strings.NewReader({json.dumps(body or '')}))"}
