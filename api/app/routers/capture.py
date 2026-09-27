import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..config import get_settings
from ..models import CapturedRequest, Delivery, Endpoint, ForwardingRule
from ..services.rate_limit import enforce
from ..services.realtime import hub
from ..services.storage import storage
from ..services.transforms import matches

router = APIRouter(tags=["capture"])
@router.api_route("/h/{endpoint_token}", methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS","HEAD"])
async def capture(endpoint_token: str, request: Request, db: AsyncSession = Depends(get_db)):
    await enforce(request, f"receive:{endpoint_token}", get_settings().rate_limit_receive_per_minute)
    endpoint = await db.scalar(select(Endpoint).where(Endpoint.token == endpoint_token, Endpoint.enabled.is_(True)))
    if not endpoint or (endpoint.expires_at and endpoint.expires_at < datetime.now(timezone.utc)): raise HTTPException(404, "Endpoint not found")
    content_length = request.headers.get("content-length")
    if content_length:
        try: declared_size = int(content_length)
        except ValueError: raise HTTPException(400, "Invalid Content-Length")
        if declared_size < 0: raise HTTPException(400, "Invalid Content-Length")
        if declared_size > endpoint.max_body_size: raise HTTPException(413, "Request body too large")
    body = await request.body()
    if len(body) > endpoint.max_body_size: raise HTTPException(413, "Request body too large")
    headers = dict(request.headers); content_type = headers.get("content-type")
    text = body.decode("utf-8", errors="replace") if (not content_type or any(x in content_type for x in ("json", "text", "xml", "form"))) else "[binary body withheld]"
    item = CapturedRequest(endpoint_id=endpoint.id, method=request.method, path=request.url.path, query=dict(request.query_params), headers=headers, cookies=request.cookies, content_type=content_type, body_size=len(body), body_preview=text[:100_000], source_ip=request.client.host if request.client else "unknown", protocol=request.scope.get("http_version", "unknown"), user_agent=headers.get("user-agent"))
    db.add(item); await db.flush()
    if body: item.body_path = storage.put(str(item.id), body)
    parsed_body = None
    if content_type and "json" in content_type:
        try: parsed_body = json.loads(text)
        except json.JSONDecodeError: pass
    rules = (await db.scalars(select(ForwardingRule).where(ForwardingRule.endpoint_id == endpoint.id, ForwardingRule.enabled.is_(True)))).all()
    for rule in rules:
        if matches(rule.condition, headers, parsed_body): db.add(Delivery(request_id=item.id, rule_id=rule.id))
    await db.commit(); await db.refresh(item)
    await hub.publish(endpoint_token, {"type":"captured", "request":{"id":str(item.id),"method":item.method,"path":item.path,"body_size":item.body_size,"received_at":item.received_at.isoformat()}})
    return Response(status_code=204, headers={"X-RequestBinX-Request-Id": str(item.id)})
@router.websocket("/ws/h/{endpoint_token}")
async def stream(endpoint_token: str, websocket: WebSocket):
    await hub.connect(endpoint_token, websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: hub.disconnect(endpoint_token, websocket)
