from flask import Blueprint, jsonify, request

from backend.middleware.request_context import current_request_id
from backend.models.analysis_model import (
    count_analyses,
    get_analysis_by_id,
    get_analysis_history,
    save_analyst_feedback,
)
from backend.utils.errors import APIError, error_response

history_bp = Blueprint("history", __name__)


def _mongo_error_response(exc: Exception):
    message = str(exc)
    unavailable = any(
        token in message.lower()
        for token in ("10061", "timeout", "connection", "refused", "server selection")
    )

    if unavailable:
        return jsonify(error_response(
            code="MONGODB_UNAVAILABLE",
            message="MongoDB is unavailable. Start MongoDB on localhost:27017 and retry.",
            request_id=current_request_id(),
        )), 503

    return jsonify(error_response(
        code="MONGODB_ERROR",
        message=message,
        request_id=current_request_id(),
    )), 500


@history_bp.route("/history", methods=["GET"])
def history():
    """
    List analysis history
    ---
    tags:
      - History
    parameters:
      - name: limit
        in: query
        type: integer
        default: 50
      - name: skip
        in: query
        type: integer
        default: 0
    responses:
      200:
        description: Paginated analysis history
      503:
        description: MongoDB unavailable
    """
    try:
        limit = request.args.get("limit", 50, type=int)
        skip = request.args.get("skip", 0, type=int)

        documents = get_analysis_history(limit=limit, skip=skip)
        total = count_analyses()

        return jsonify({
            "status": "success",
            "request_id": current_request_id(),
            "total": total,
            "count": len(documents),
            "limit": max(1, min(limit or 50, 200)),
            "skip": max(0, skip or 0),
            "history": documents,
        })

    except Exception as exc:
        return _mongo_error_response(exc)


@history_bp.route("/history/<analysis_id>", methods=["GET"])
def history_item(analysis_id):
    """
    Get analysis by ID
    ---
    tags:
      - History
    parameters:
      - name: analysis_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Analysis document
      404:
        description: Not found
    """
    try:
        document = get_analysis_by_id(analysis_id)

        if document is None:
            raise APIError(
                message="Analysis not found.",
                code="ANALYSIS_NOT_FOUND",
                status_code=404,
            )

        return jsonify({
            "status": "success",
            "request_id": current_request_id(),
            "analysis": document,
        })

    except APIError:
        raise

    except Exception as exc:
        return _mongo_error_response(exc)


@history_bp.route("/history/<analysis_id>/feedback", methods=["POST"])
def history_feedback(analysis_id):
    """
    Store analyst feedback for the adaptive loop
    ---
    tags:
      - History
    parameters:
      - name: analysis_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        schema:
          properties:
            verdict:
              type: string
              enum: [correct, incorrect, too_aggressive, too_lenient]
            notes:
              type: string
    responses:
      200:
        description: Updated analysis document
    """
    body = request.get_json(silent=True) or {}
    verdict = str(body.get("verdict") or "").strip()
    notes = str(body.get("notes") or "")
    override = body.get("override_action") or None

    try:
        document = save_analyst_feedback(
            analysis_id,
            verdict,
            notes,
            override_action=override,
        )
    except ValueError as exc:
        raise APIError(message=str(exc), code="INVALID_FEEDBACK", status_code=400)

    try:
        if document is None:
            raise APIError(
                message="Analysis not found.",
                code="ANALYSIS_NOT_FOUND",
                status_code=404,
            )
        return jsonify({
            "status": "success",
            "request_id": current_request_id(),
            "analysis": document,
        })
    except APIError:
        raise
    except Exception as exc:
        return _mongo_error_response(exc)
