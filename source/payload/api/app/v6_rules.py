from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import UTC, datetime, timedelta
from typing import Any, Iterable, Mapping


RULE_SCHEMA_VERSION = "6.0.0"
MAX_RULE_DEPTH = 12
MAX_RULE_NODES = 500
MAX_GROUP_CHILDREN = 100
MAX_SEQUENCE_STEPS = 20
MAX_WINDOW_HOURS = 24 * 365 * 5

CONDITION_OPERATORS = {
    "eq",
    "ne",
    "contains",
    "not_contains",
    "in",
    "not_in",
    "gt",
    "gte",
    "lt",
    "lte",
    "exists",
    "regex",
    "within_hours",
    "overlaps_text",
}
COMPARATORS = {"eq", "ne", "gt", "gte", "lt", "lte"}
CORRELATION_MODES = {"count", "sequence", "absence", "trend"}
FIELD_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,159}$")


class RuleValidationError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def rule_sha256(tree: Mapping[str, Any]) -> str:
    normalized = validate_rule_tree(tree)
    return hashlib.sha256(canonical_json(normalized).encode("utf-8")).hexdigest()


def _strict_keys(node: Mapping[str, Any], allowed: set[str], path: str) -> None:
    unknown = set(node) - allowed
    if unknown:
        raise RuleValidationError(f"{path}: champs inconnus: {sorted(unknown)}")


def _positive_number(value: Any, path: str, *, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuleValidationError(f"{path}: nombre attendu")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise RuleValidationError(f"{path}: valeur strictement positive attendue")
    if maximum is not None and number > maximum:
        raise RuleValidationError(f"{path}: valeur supérieure à {maximum}")
    return number


def _validate_filter(node: Any, path: str, depth: int, counter: list[int]) -> dict[str, Any]:
    normalized = _validate_node(node, path, depth, counter)
    if _contains_correlation(normalized):
        raise RuleValidationError(f"{path}: une corrélation ne peut pas être imbriquée dans un filtre d'événement")
    return normalized


def _validate_node(node: Any, path: str, depth: int, counter: list[int]) -> dict[str, Any]:
    if not isinstance(node, Mapping):
        raise RuleValidationError(f"{path}: objet JSON attendu")
    if depth > MAX_RULE_DEPTH:
        raise RuleValidationError(f"{path}: profondeur maximale {MAX_RULE_DEPTH} dépassée")
    counter[0] += 1
    if counter[0] > MAX_RULE_NODES:
        raise RuleValidationError(f"règle: nombre maximal de nœuds {MAX_RULE_NODES} dépassé")

    node_type = node.get("type")
    if node_type == "group":
        _strict_keys(node, {"type", "operator", "children"}, path)
        operator = str(node.get("operator", "")).upper()
        if operator not in {"AND", "OR"}:
            raise RuleValidationError(f"{path}.operator: AND ou OR attendu")
        children = node.get("children")
        if not isinstance(children, list) or not 1 <= len(children) <= MAX_GROUP_CHILDREN:
            raise RuleValidationError(
                f"{path}.children: entre 1 et {MAX_GROUP_CHILDREN} éléments attendus"
            )
        return {
            "type": "group",
            "operator": operator,
            "children": [
                _validate_node(child, f"{path}.children[{index}]", depth + 1, counter)
                for index, child in enumerate(children)
            ],
        }

    if node_type == "condition":
        _strict_keys(node, {"type", "field", "op", "value"}, path)
        field = node.get("field")
        operator = node.get("op")
        if not isinstance(field, str) or not FIELD_PATTERN.fullmatch(field):
            raise RuleValidationError(f"{path}.field: chemin de champ invalide")
        if operator not in CONDITION_OPERATORS:
            raise RuleValidationError(f"{path}.op: opérateur non pris en charge")
        if operator != "exists" and "value" not in node:
            raise RuleValidationError(f"{path}.value: valeur requise")
        if operator == "within_hours":
            if field != "occurred_at":
                raise RuleValidationError(f"{path}.field: occurred_at requis pour within_hours")
            _positive_number(node.get("value"), f"{path}.value", maximum=MAX_WINDOW_HOURS)
        if operator == "overlaps_text" and not isinstance(node.get("value"), list):
            raise RuleValidationError(f"{path}.value: liste requise pour overlaps_text")
        return {"type": "condition", "field": field, "op": operator, "value": node.get("value")}

    if node_type == "correlation":
        mode = node.get("mode")
        if mode not in CORRELATION_MODES:
            raise RuleValidationError(f"{path}.mode: mode de corrélation non pris en charge")

        if mode == "count":
            _strict_keys(node, {"type", "mode", "window_hours", "filter", "comparator", "threshold"}, path)
            window = _positive_number(node.get("window_hours"), f"{path}.window_hours", maximum=MAX_WINDOW_HOURS)
            comparator = node.get("comparator", "gte")
            if comparator not in COMPARATORS:
                raise RuleValidationError(f"{path}.comparator: comparateur invalide")
            threshold = _positive_number(node.get("threshold"), f"{path}.threshold")
            result: dict[str, Any] = {
                "type": "correlation",
                "mode": "count",
                "window_hours": window,
                "comparator": comparator,
                "threshold": threshold,
            }
            if node.get("filter") is not None:
                result["filter"] = _validate_filter(node["filter"], f"{path}.filter", depth + 1, counter)
            return result

        if mode == "sequence":
            _strict_keys(node, {"type", "mode", "window_hours", "steps"}, path)
            window = _positive_number(node.get("window_hours"), f"{path}.window_hours", maximum=MAX_WINDOW_HOURS)
            steps = node.get("steps")
            if not isinstance(steps, list) or not 2 <= len(steps) <= MAX_SEQUENCE_STEPS:
                raise RuleValidationError(
                    f"{path}.steps: entre 2 et {MAX_SEQUENCE_STEPS} étapes attendues"
                )
            return {
                "type": "correlation",
                "mode": "sequence",
                "window_hours": window,
                "steps": [
                    _validate_filter(step, f"{path}.steps[{index}]", depth + 1, counter)
                    for index, step in enumerate(steps)
                ],
            }

        if mode == "absence":
            _strict_keys(node, {"type", "mode", "window_hours", "expected"}, path)
            window = _positive_number(node.get("window_hours"), f"{path}.window_hours", maximum=MAX_WINDOW_HOURS)
            if node.get("expected") is None:
                raise RuleValidationError(f"{path}.expected: filtre requis")
            return {
                "type": "correlation",
                "mode": "absence",
                "window_hours": window,
                "expected": _validate_filter(node["expected"], f"{path}.expected", depth + 1, counter),
            }

        _strict_keys(
            node,
            {
                "type",
                "mode",
                "field",
                "filter",
                "aggregation",
                "current_window_hours",
                "baseline_window_hours",
                "reference",
                "baseline_value",
                "comparator",
                "threshold",
            },
            path,
        )
        field = node.get("field")
        aggregation = node.get("aggregation", "mean")
        reference = node.get("reference", "rolling")
        comparator = node.get("comparator", "gte")
        if aggregation not in {"mean", "sum", "min", "max", "count"}:
            raise RuleValidationError(f"{path}.aggregation: agrégation invalide")
        if aggregation != "count" and (not isinstance(field, str) or not FIELD_PATTERN.fullmatch(field)):
            raise RuleValidationError(f"{path}.field: champ numérique requis")
        if reference not in {"rolling", "fixed"}:
            raise RuleValidationError(f"{path}.reference: rolling ou fixed attendu")
        if comparator not in COMPARATORS:
            raise RuleValidationError(f"{path}.comparator: comparateur invalide")
        current_window = _positive_number(
            node.get("current_window_hours"), f"{path}.current_window_hours", maximum=MAX_WINDOW_HOURS
        )
        baseline_window = _positive_number(
            node.get("baseline_window_hours", current_window),
            f"{path}.baseline_window_hours",
            maximum=MAX_WINDOW_HOURS,
        )
        baseline_value = node.get("baseline_value")
        if reference == "fixed" and (isinstance(baseline_value, bool) or not isinstance(baseline_value, (int, float))):
            raise RuleValidationError(f"{path}.baseline_value: référence fixe numérique requise")
        threshold = node.get("threshold", 0)
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(float(threshold)):
            raise RuleValidationError(f"{path}.threshold: seuil numérique attendu")
        result = {
            "type": "correlation",
            "mode": "trend",
            "field": field,
            "aggregation": aggregation,
            "current_window_hours": current_window,
            "baseline_window_hours": baseline_window,
            "reference": reference,
            "comparator": comparator,
            "threshold": float(threshold),
        }
        if reference == "fixed":
            result["baseline_value"] = float(baseline_value)
        if node.get("filter") is not None:
            result["filter"] = _validate_filter(node["filter"], f"{path}.filter", depth + 1, counter)
        return result

    raise RuleValidationError(f"{path}.type: group, condition ou correlation attendu")


def validate_rule_tree(tree: Mapping[str, Any]) -> dict[str, Any]:
    return _validate_node(tree, "rule", 0, [0])


def _contains_correlation(node: Mapping[str, Any]) -> bool:
    if node.get("type") == "correlation":
        return True
    return any(_contains_correlation(child) for child in node.get("children", []))


def _event_time(event: Mapping[str, Any]) -> datetime:
    value = event.get("occurred_at")
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("Chaque événement doit posséder occurred_at")
    return result.replace(tzinfo=UTC) if result.tzinfo is None else result.astimezone(UTC)


def _resolve_field(event: Mapping[str, Any], path: str) -> tuple[bool, Any]:
    current: Any = event
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def _compare(left: Any, operator: str, right: Any) -> bool:
    if operator == "exists":
        return bool(left) is bool(right) if isinstance(right, bool) else left is not None
    if operator in {"gt", "gte", "lt", "lte"}:
        left_number, right_number = _numeric(left), _numeric(right)
        if left_number is None or right_number is None:
            return False
        return {
            "gt": left_number > right_number,
            "gte": left_number >= right_number,
            "lt": left_number < right_number,
            "lte": left_number <= right_number,
        }[operator]
    if operator == "eq":
        return left == right
    if operator == "ne":
        return left != right
    if operator in {"in", "not_in"}:
        if not isinstance(right, (list, tuple, set)):
            return False
        matched = left in right if not isinstance(left, (list, tuple, set)) else bool(set(left) & set(right))
        return matched if operator == "in" else not matched
    if operator in {"contains", "not_contains"}:
        if isinstance(left, str):
            matched = str(right).casefold() in left.casefold()
        elif isinstance(left, (list, tuple, set)):
            matched = right in left
        else:
            matched = False
        return matched if operator == "contains" else not matched
    if operator == "regex":
        if not isinstance(right, str) or len(right) > 300:
            return False
        try:
            return re.search(right, str(left), flags=re.IGNORECASE) is not None
        except re.error:
            return False
    if operator == "overlaps_text":
        if not isinstance(right, (list, tuple, set)):
            return False
        observed_text = " ".join(str(item) for item in left) if isinstance(left, (list, tuple, set)) else str(left)
        observed_text = observed_text.casefold()
        return any(str(item).casefold() in observed_text for item in right)
    return False


def _condition_result(
    node: Mapping[str, Any], event: Mapping[str, Any], now: datetime
) -> tuple[bool, dict[str, Any]]:
    exists, observed = _resolve_field(event, str(node["field"]))
    operator = str(node["op"])
    if operator == "within_hours" and exists:
        try:
            observed_at = _event_time({"occurred_at": observed})
            matched = now - timedelta(hours=float(node["value"])) <= observed_at <= now
        except (TypeError, ValueError):
            matched = False
    else:
        matched = exists == bool(node.get("value", True)) if operator == "exists" else exists and _compare(observed, operator, node.get("value"))
    return matched, {
        "type": "condition",
        "field": node["field"],
        "op": operator,
        "expected": node.get("value"),
        "observed": observed if exists else None,
        "field_exists": exists,
        "matched": matched,
    }


def _window(events: Iterable[Mapping[str, Any]], now: datetime, hours: float) -> list[Mapping[str, Any]]:
    start = now - timedelta(hours=hours)
    return sorted(
        (event for event in events if start <= _event_time(event) <= now),
        key=_event_time,
    )


def _aggregate(values: list[float], operation: str) -> float | None:
    if operation == "count":
        return float(len(values))
    if not values:
        return None
    if operation == "mean":
        return sum(values) / len(values)
    if operation == "sum":
        return sum(values)
    if operation == "min":
        return min(values)
    return max(values)


def _event_matches_filter(node: Mapping[str, Any], event: Mapping[str, Any]) -> bool:
    matched, _ = _evaluate_node(node, event, [event], _event_time(event))
    return matched


def _correlation_result(
    node: Mapping[str, Any],
    event: Mapping[str, Any],
    events: list[Mapping[str, Any]],
    now: datetime,
) -> tuple[bool, dict[str, Any]]:
    mode = node["mode"]
    if mode == "count":
        candidates = _window(events, now, float(node["window_hours"]))
        if node.get("filter"):
            candidates = [item for item in candidates if _event_matches_filter(node["filter"], item)]
        count = len(candidates)
        matched = _compare(count, str(node["comparator"]), node["threshold"])
        return matched, {
            "type": "correlation",
            "mode": mode,
            "matched": matched,
            "count": count,
            "threshold": node["threshold"],
            "event_ids": [str(item.get("id", item.get("external_id", ""))) for item in candidates[:100]],
        }

    if mode == "sequence":
        candidates = _window(events, now, float(node["window_hours"]))
        positions: list[int] = []
        cursor = 0
        for step in node["steps"]:
            found = None
            while cursor < len(candidates):
                if _event_matches_filter(step, candidates[cursor]):
                    found = cursor
                    cursor += 1
                    break
                cursor += 1
            if found is None:
                return False, {"type": "correlation", "mode": mode, "matched": False, "positions": positions}
            positions.append(found)
        selected = [candidates[index] for index in positions]
        return True, {
            "type": "correlation",
            "mode": mode,
            "matched": True,
            "event_ids": [str(item.get("id", item.get("external_id", ""))) for item in selected],
        }

    if mode == "absence":
        candidates = _window(events, now, float(node["window_hours"]))
        found = [item for item in candidates if _event_matches_filter(node["expected"], item)]
        matched = not found
        return matched, {
            "type": "correlation",
            "mode": mode,
            "matched": matched,
            "observed_count": len(found),
            "window_hours": node["window_hours"],
        }

    current_start = now - timedelta(hours=float(node["current_window_hours"]))
    baseline_start = current_start - timedelta(hours=float(node["baseline_window_hours"]))
    filtered = [item for item in events if not node.get("filter") or _event_matches_filter(node["filter"], item)]

    def values_between(start: datetime, end: datetime) -> list[float]:
        selected = [item for item in filtered if start <= _event_time(item) <= end]
        if node["aggregation"] == "count":
            return [1.0 for _ in selected]
        values = []
        for item in selected:
            exists, value = _resolve_field(item, str(node["field"]))
            number = _numeric(value) if exists else None
            if number is not None:
                values.append(number)
        return values

    current_value = _aggregate(values_between(current_start, now), str(node["aggregation"]))
    reference_value = (
        float(node["baseline_value"])
        if node["reference"] == "fixed"
        else _aggregate(values_between(baseline_start, current_start), str(node["aggregation"]))
    )
    if current_value is None or reference_value is None:
        return False, {
            "type": "correlation",
            "mode": mode,
            "matched": False,
            "reason": "insufficient_data",
            "current": current_value,
            "reference": reference_value,
        }
    variation = current_value - reference_value
    matched = _compare(variation, str(node["comparator"]), node["threshold"])
    return matched, {
        "type": "correlation",
        "mode": mode,
        "matched": matched,
        "current": current_value,
        "reference": reference_value,
        "variation": variation,
        "threshold": node["threshold"],
    }


def _evaluate_node(
    node: Mapping[str, Any],
    event: Mapping[str, Any],
    events: list[Mapping[str, Any]],
    now: datetime,
) -> tuple[bool, dict[str, Any]]:
    if node["type"] == "condition":
        return _condition_result(node, event, now)
    if node["type"] == "correlation":
        return _correlation_result(node, event, events, now)
    results = [_evaluate_node(child, event, events, now) for child in node["children"]]
    matched = all(item[0] for item in results) if node["operator"] == "AND" else any(item[0] for item in results)
    return matched, {
        "type": "group",
        "operator": node["operator"],
        "matched": matched,
        "children": [item[1] for item in results],
    }


def evaluate_rule(
    tree: Mapping[str, Any],
    event: Mapping[str, Any],
    events: Iterable[Mapping[str, Any]],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    normalized = validate_rule_tree(tree)
    evaluation_time = now or datetime.now(UTC)
    evaluation_time = evaluation_time.replace(tzinfo=UTC) if evaluation_time.tzinfo is None else evaluation_time.astimezone(UTC)
    history = list(events)
    matched, proof = _evaluate_node(normalized, event, history, evaluation_time)
    return {
        "schema_version": RULE_SCHEMA_VERSION,
        "matched": matched,
        "evaluated_at": evaluation_time.isoformat(),
        "rule_sha256": hashlib.sha256(canonical_json(normalized).encode("utf-8")).hexdigest(),
        "events_examined": len(history),
        "proof": proof,
    }


def legacy_signal_rule_tree(rule: Mapping[str, Any]) -> dict[str, Any]:
    children: list[dict[str, Any]] = [
        {"type": "condition", "field": "severity", "op": "gte", "value": float(rule.get("min_severity", 0))},
        {"type": "condition", "field": "confidence", "op": "gte", "value": float(rule.get("min_confidence", 0))},
    ]
    locations = list(rule.get("locations") or [])
    themes = list(rule.get("themes") or [])
    if locations:
        children.append({"type": "condition", "field": "locations", "op": "overlaps_text", "value": locations})
    if themes:
        children.append({"type": "condition", "field": "themes", "op": "overlaps_text", "value": themes})
    lookback_hours = int(rule.get("lookback_hours", 168))
    children.append(
        {"type": "condition", "field": "occurred_at", "op": "within_hours", "value": lookback_hours}
    )
    return validate_rule_tree({"type": "group", "operator": "AND", "children": children})
