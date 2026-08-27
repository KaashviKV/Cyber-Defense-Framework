from flask import Blueprint, Response, jsonify, stream_with_context

from backend.middleware.request_context import current_request_id
from backend.services.event_bus import latest, snapshot_json

stream_bp = Blueprint("stream", __name__)


@stream_bp.route("/stream/analyses", methods=["GET"])
def stream_analyses():
    """
    Server-sent events for new analyses
    ---
    tags:
      - Stream
    responses:
      200:
        description: text/event-stream
    """
    def generate():
        yield f"data: {snapshot_json()}\n\n"
        # Long-poll style heartbeat; clients also poll /stream/latest
        yield "event: ping\ndata: {}\n\n"

    response = Response(stream_with_context(generate()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


@stream_bp.route("/stream/latest", methods=["GET"])
def stream_latest():
    """
    Latest in-memory analysis events (SSE fallback)
    ---
    tags:
      - Stream
    responses:
      200:
        description: Recent live events
    """
    return jsonify({
        "status": "success",
        "request_id": current_request_id(),
        "events": latest(20),
    })
