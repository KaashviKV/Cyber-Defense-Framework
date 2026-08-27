from flask import Blueprint, jsonify, request

from backend.middleware.request_context import current_request_id
from backend.models.incident_model import count_incidents, get_incident_by_id, list_incidents
from backend.utils.errors import APIError, error_response

incidents_bp = Blueprint("incidents", __name__)


def _mongo_error_response(exc: Exception):
    message = str(exc)
    unavailable = any(
        token in message.lower()
        for token in ("10061", "timeout", "connection", "refused", "server selection")
    )
    code = "MONGODB_UNAVAILABLE" if unavailable else "MONGODB_ERROR"
    status = 503 if unavailable else 500
    return jsonify(error_response(code=code, message=message, request_id=current_request_id())), status


@incidents_bp.route("/incidents", methods=["GET"])
def incidents():
    """
    List SOC incidents
    ---
    tags:
      - Incidents
    responses:
      200:
        description: Paginated incidents
    """
    try:
        limit = request.args.get("limit", 50, type=int)
        skip = request.args.get("skip", 0, type=int)
        rows = list_incidents(limit=limit, skip=skip)
        return jsonify({
            "status": "success",
            "request_id": current_request_id(),
            "total": count_incidents(),
            "count": len(rows),
            "incidents": rows,
        })
    except Exception as exc:
        return _mongo_error_response(exc)


@incidents_bp.route("/incidents/<incident_id>", methods=["GET"])
def incident_item(incident_id):
    """
    Get one incident
    ---
    tags:
      - Incidents
    responses:
      200:
        description: Incident document
      404:
        description: Not found
    """
    try:
        document = get_incident_by_id(incident_id)
        if document is None:
            raise APIError(message="Incident not found.", code="INCIDENT_NOT_FOUND", status_code=404)
        return jsonify({
            "status": "success",
            "request_id": current_request_id(),
            "incident": document,
        })
    except APIError:
        raise
    except Exception as exc:
        return _mongo_error_response(exc)
