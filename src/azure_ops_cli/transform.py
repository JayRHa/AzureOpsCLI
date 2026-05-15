from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

def merge_query(url_or_path: str, values: dict[str, str]) -> str:
    if not values:
        return url_or_path
    parts = urlsplit(url_or_path)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(values)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

def parse_resource_id(resource_id: str) -> dict[str, str | None]:
    parts = [part for part in resource_id.strip("/").split("/") if part]
    lowered = [part.lower() for part in parts]
    result = {"subscription_id": None, "resource_group": None, "provider": None, "resource_type": None, "name": None}
    if "subscriptions" in lowered and lowered.index("subscriptions") + 1 < len(parts):
        result["subscription_id"] = parts[lowered.index("subscriptions") + 1]
    if "resourcegroups" in lowered and lowered.index("resourcegroups") + 1 < len(parts):
        result["resource_group"] = parts[lowered.index("resourcegroups") + 1]
    if "providers" in lowered:
        index = lowered.index("providers")
        if index + 3 < len(parts):
            result["provider"] = parts[index + 1]
            result["resource_type"] = "/".join(parts[index + 2:-1])
            result["name"] = parts[-1]
    return result

def normalize_resource(raw: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_resource_id(str(raw.get("id") or ""))
    return {"id": raw.get("id"), "name": raw.get("name") or parsed["name"], "type": raw.get("type"), "location": raw.get("location"), "resource_group": parsed["resource_group"], "subscription_id": parsed["subscription_id"], "tags": raw.get("tags") or {}}

def normalize_collection(payload: Any) -> list[Any]:
    if isinstance(payload, dict) and isinstance(payload.get("value"), list):
        return payload["value"]
    return payload if isinstance(payload, list) else []

def activity_log_filter(since_hours: int, resource_group: str | None = None, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc).replace(microsecond=0)
    timestamp = now - timedelta(hours=since_hours)
    clauses = [f"eventTimestamp ge '{timestamp.isoformat().replace('+00:00', 'Z')}'"]
    if resource_group:
        clauses.append(f"resourceGroupName eq '{resource_group}'")
    return " and ".join(clauses)
