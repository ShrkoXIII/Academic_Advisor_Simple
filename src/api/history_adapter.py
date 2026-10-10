"""Read-only aggregate checks; finalization and lineage are separate attestations."""
from src.recommendation.history_update import normalize_history_delta, DELTA_ID_COLUMNS
from .validation import ApiError, ValidationResult, identifier, part


def adapt_history_delta(request, *, manager=None):
    result = ValidationResult(checks={"aggregates": "unavailable", "lineage": "unavailable",
                                      "finalization": "unavailable"})
    try:
        cutoff = part(request.get("part_id"))
        rows = request.get("rows")
        if not isinstance(rows, list):
            raise ApiError("INVALID_DELTA", "Aggregate rows are required.")
        for row in rows:
            if not isinstance(row, dict):
                raise ApiError("INVALID_DELTA", "Aggregate rows must be records.")
            for key in DELTA_ID_COLUMNS:
                identifier(row.get(key), key)
        payload = {"delta_part": cutoff, "aggregates": rows}
        try:
            delta = normalize_history_delta(payload, require_finalized=False)
        except ValueError:
            raise ApiError("INVALID_DELTA", "Aggregate schema or sums violate the history contract.") from None
        result.checks["aggregates"] = "verified"
        proof = request.get("finalization")
        if proof is not None:
            if not isinstance(proof, dict) or part(proof.get("finalized_part_id")) != cutoff:
                raise ApiError("FINALIZATION_CONFLICT", "Finalization attestation must identify this semester.")
            identifier(proof.get("approval_reference"), "approval_reference")
            result.checks["finalization"] = "admin_attested"
            payload["finalized"] = True
        result.summary = {"delta_part": cutoff, "delta_sha256": delta.delta_sha256,
                          "row_count": len(delta.rows), "published": False, "activated": False}
        result.normalized = delta
        if manager is not None:
            try:
                preview = manager.preview_delta(history_payload=payload)
            except ValueError:
                raise ApiError("DELTA_CONFLICT", "Delta conflicts with recorded lineage or semester order.", status_code=409) from None
            result.summary.update({key: preview[key] for key in
                                   ("status", "history_as_of_part", "base_history_sha256")})
            result.checks["lineage"] = "verified"
    except ApiError as error:
        result.add(error)
    return result
