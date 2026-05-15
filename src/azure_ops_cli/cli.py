import argparse
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .const import API_VERSIONS, DEFAULT_ARM_HOST, DEFAULT_AUTHORITY_HOST, DEFAULT_SCOPE, ENV_ACCESS_TOKEN
from .transform import activity_log_filter, merge_query, normalize_collection, normalize_resource, parse_resource_id

class CliError(RuntimeError):
    pass

def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))

def request_json(method: str, url: str, headers: dict[str, str]) -> Any:
    try:
        with urlopen(Request(url=url, method=method, headers=headers), timeout=60) as response:
            text = response.read().decode("utf-8")
            return json.loads(text) if text else {"status": response.status}
    except HTTPError as exc:
        raise CliError(f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')}") from exc
    except URLError as exc:
        raise CliError(f"Request failed: {exc.reason}") from exc

def token(args: argparse.Namespace) -> str:
    direct = args.access_token or os.getenv(ENV_ACCESS_TOKEN)
    if direct:
        return direct
    tenant = args.tenant_id or os.getenv("AZURE_TENANT_ID")
    client = args.client_id or os.getenv("AZURE_CLIENT_ID")
    secret = args.client_secret or os.getenv("AZURE_CLIENT_SECRET")
    if not all([tenant, client, secret]):
        raise CliError("Set AZURE_ACCESS_TOKEN or AZURE_TENANT_ID, AZURE_CLIENT_ID and AZURE_CLIENT_SECRET.")
    body = urlencode({"client_id": client, "client_secret": secret, "grant_type": "client_credentials", "scope": args.scope}).encode("utf-8")
    req = Request(f"{args.authority_host.rstrip('/')}/{tenant}/oauth2/v2.0/token", method="POST", headers={"Content-Type": "application/x-www-form-urlencoded"}, data=body)
    try:
        with urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))["access_token"]
    except Exception as exc:
        raise CliError(f"Could not acquire Azure ARM token: {exc}") from exc

def arm_url(args: argparse.Namespace, path: str, api_version: str, query: dict[str, str] | None = None) -> str:
    url = path if path.startswith("https://") else f"{args.arm_host.rstrip('/')}{path if path.startswith('/') else '/' + path}"
    values = {"api-version": api_version}
    values.update(query or {})
    return merge_query(url, values)

def headers(args: argparse.Namespace) -> dict[str, str]:
    return {"Accept": "application/json", "Authorization": f"Bearer {token(args)}"}

def emit(args: argparse.Namespace, name: str, method: str, url: str, normalizer=None) -> int:
    request_plan = {"name": name, "method": method, "url": url}
    if args.dry_run:
        print_json({"requests": [request_plan]})
        return 0
    payload = request_json(method, url, headers(args))
    print_json(normalizer(payload) if normalizer else payload)
    return 0

def cmd_resources(args: argparse.Namespace) -> int:
    query = {"$filter": f"resourceType eq '{args.resource_type}'"} if args.resource_type else {}
    url = arm_url(args, f"/subscriptions/{args.subscription_id}/resources", API_VERSIONS["resources"], query)
    def normalize(payload: Any) -> dict[str, Any]:
        items = [normalize_resource(item) for item in normalize_collection(payload)]
        if args.name_contains:
            needle = args.name_contains.lower()
            items = [item for item in items if needle in str(item.get("name") or "").lower()]
        return {"count": len(items), "resources": items}
    return emit(args, "resources", "GET", url, normalize)

def cmd_appservice_show(args: argparse.Namespace) -> int:
    path = f"/subscriptions/{args.subscription_id}/resourceGroups/{args.resource_group}/providers/Microsoft.Web/sites/{args.name}"
    return emit(args, "appservice", "GET", arm_url(args, path, API_VERSIONS["web-sites"]), normalize_resource)

def cmd_appservice_config(args: argparse.Namespace) -> int:
    path = f"/subscriptions/{args.subscription_id}/resourceGroups/{args.resource_group}/providers/Microsoft.Web/sites/{args.name}/config/web"
    return emit(args, "appservice-config", "GET", arm_url(args, path, API_VERSIONS["web-config"]))

def cmd_deployments(args: argparse.Namespace) -> int:
    path = f"/subscriptions/{args.subscription_id}/resourceGroups/{args.resource_group}/providers/Microsoft.Resources/deployments"
    return emit(args, "deployments", "GET", arm_url(args, path, API_VERSIONS["deployments"], {"$top": str(args.top)}))

def cmd_activity_log(args: argparse.Namespace) -> int:
    path = f"/subscriptions/{args.subscription_id}/providers/Microsoft.Insights/eventtypes/management/values"
    return emit(args, "activity-log", "GET", arm_url(args, path, API_VERSIONS["activity-log"], {"$filter": activity_log_filter(args.since_hours, args.resource_group)}))

def cmd_health(args: argparse.Namespace) -> int:
    if not parse_resource_id(args.resource_id)["subscription_id"]:
        raise CliError("--resource-id must be a full Azure resource ID.")
    path = f"{args.resource_id.rstrip('/')}/providers/Microsoft.ResourceHealth/availabilityStatuses/current"
    return emit(args, "resource-health", "GET", arm_url(args, path, API_VERSIONS["resource-health"]))

def cmd_request(args: argparse.Namespace) -> int:
    return emit(args, "request", args.method, arm_url(args, args.path, args.api_version))

def add_auth(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--access-token", help=f"Access token. Defaults to {ENV_ACCESS_TOKEN}.")
    parser.add_argument("--tenant-id", help="Tenant ID. Defaults to AZURE_TENANT_ID.")
    parser.add_argument("--client-id", help="Client ID. Defaults to AZURE_CLIENT_ID.")
    parser.add_argument("--client-secret", help="Client secret. Defaults to AZURE_CLIENT_SECRET.")
    parser.add_argument("--scope", default=DEFAULT_SCOPE)
    parser.add_argument("--authority-host", default=DEFAULT_AUTHORITY_HOST)
    parser.add_argument("--arm-host", default=DEFAULT_ARM_HOST)

def add_subscription(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--subscription-id", required=True)

def add_appservice(parser: argparse.ArgumentParser) -> None:
    add_subscription(parser)
    parser.add_argument("--resource-group", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--dry-run", action="store_true")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agent-friendly Azure operations CLI for resource, deployment and health evidence.")
    add_auth(parser)
    subs = parser.add_subparsers(dest="command", required=True)
    resources = subs.add_parser("resources", help="List Azure resources in a subscription.")
    add_subscription(resources)
    resources.add_argument("--resource-type")
    resources.add_argument("--name-contains")
    resources.add_argument("--dry-run", action="store_true")
    resources.set_defaults(func=cmd_resources)
    appservice = subs.add_parser("appservice", help="Inspect Azure App Service state.")
    app_subs = appservice.add_subparsers(dest="appservice_command", required=True)
    show = app_subs.add_parser("show", help="Show an App Service resource.")
    add_appservice(show)
    show.set_defaults(func=cmd_appservice_show)
    config = app_subs.add_parser("config", help="Show App Service web configuration.")
    add_appservice(config)
    config.set_defaults(func=cmd_appservice_config)
    deployments = subs.add_parser("deployments", help="List resource group deployments.")
    add_subscription(deployments)
    deployments.add_argument("--resource-group", required=True)
    deployments.add_argument("--top", type=int, default=25)
    deployments.add_argument("--dry-run", action="store_true")
    deployments.set_defaults(func=cmd_deployments)
    activity = subs.add_parser("activity-log", help="Read Azure Activity Log management events.")
    add_subscription(activity)
    activity.add_argument("--resource-group")
    activity.add_argument("--since-hours", type=int, default=24)
    activity.add_argument("--dry-run", action="store_true")
    activity.set_defaults(func=cmd_activity_log)
    health = subs.add_parser("health", help="Read Azure Resource Health for one resource.")
    health.add_argument("--resource-id", required=True)
    health.add_argument("--dry-run", action="store_true")
    health.set_defaults(func=cmd_health)
    request = subs.add_parser("request", help="Execute a custom ARM request by path and api-version.")
    request.add_argument("--method", choices=["GET", "POST", "PATCH", "PUT", "DELETE"], default="GET")
    request.add_argument("--path", required=True)
    request.add_argument("--api-version", required=True)
    request.add_argument("--dry-run", action="store_true")
    request.set_defaults(func=cmd_request)
    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (CliError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")

if __name__ == "__main__":
    sys.exit(main())
