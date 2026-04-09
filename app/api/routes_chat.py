from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.deps import enforce_router_auth, get_services, validate_request_limits
from app.api.schemas import ChatCompletionRequest
from app.core.errors import ValidationError
from app.core.ids import new_request_id


router = APIRouter(tags=["chat"])


@router.post("/v1/chat/completions")
async def chat_completions(request: Request, body: ChatCompletionRequest):
    services = get_services(request)
    enforce_router_auth(request, services)
    validate_request_limits(body, services)

    request_id = request.headers.get("x-request-id") or new_request_id()
    payload = body.model_dump(exclude_none=True)

    if not services.config.routing.enabled and payload.get("model") not in services.config.models:
        raise ValidationError("Routing is disabled and model is not a configured internal model")

    if body.stream:
        if not services.config.streaming.enabled or not services.config.streaming.passthrough_streaming:
            raise ValidationError("Streaming is disabled")

        stream_result = await services.dispatcher.dispatch_stream(payload=payload, request_id=request_id)
        return StreamingResponse(
            stream_result.stream,
            media_type="text/event-stream",
            headers={
                "x-request-id": request_id,
                "x-selected-model": stream_result.selected_model,
                "x-route-mode": stream_result.route_mode,
            },
        )

    result = await services.dispatcher.dispatch_non_stream(payload=payload, request_id=request_id)
    return JSONResponse(
        result.response_json,
        headers={
            "x-request-id": request_id,
            "x-selected-model": result.selected_model,
            "x-route-mode": result.route_mode,
        },
    )
