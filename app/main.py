import json
import os
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware


def load_routes_config(config_path: Union[str, Path]) -> List[Dict[str, Any]]:
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Routes config not found at: {config_file}")
    with config_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "routes" in data:
        routes = data["routes"]
    elif isinstance(data, list):
        routes = data
    else:
        raise ValueError("Invalid routes config format. Expected list or object with 'routes' key.")
    if not isinstance(routes, list):
        raise ValueError("Invalid routes config format: 'routes' must be a list.")
    return routes


def create_app() -> FastAPI:
    app = FastAPI(title="VulnLab Dynamic Router", version="0.1.0")

    # Enable permissive CORS to simplify testing in labs
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    routes_file = os.environ.get("ROUTES_FILE", str(Path(__file__).parent / "routes.json"))
    routes: List[Dict[str, Any]] = []
    try:
        routes = load_routes_config(routes_file)
    except Exception as e:
        # Expose a simple endpoint to report configuration loading issues
        @app.get("/__config_error__")
        def config_error() -> Dict[str, str]:
            return {"error": f"Failed to load routes config: {e}"}
        return app

    def register_route(
        path: str,
        method: str = "GET",
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        html_output: Optional[str] = None,
        text_output: Optional[str] = None,
        json_output: Optional[Union[Dict[str, Any], List[Any], str, int, float, bool, None]] = None,
        content_type: Optional[str] = None,
    ) -> None:
        norm_method = method.upper()
        allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
        if norm_method not in allowed_methods:
            norm_method = "GET"

        # Determine content and media type
        body: Union[str, bytes]
        media_type: str
        if html_output is not None:
            body = html_output
            media_type = "text/html"
        elif text_output is not None:
            body = text_output
            media_type = "text/plain"
        elif json_output is not None:
            # Keep raw JSON as body text to avoid FastAPI auto-serialization changing formatting
            if isinstance(json_output, (dict, list)):
                body = json.dumps(json_output)
            else:
                body = json.dumps(json_output)
            media_type = "application/json"
        else:
            body = ""
            media_type = "text/plain"

        if content_type:
            media_type = content_type

        async def handler() -> Response:
            return Response(content=body, status_code=status_code, media_type=media_type, headers=headers)

        app.add_api_route(path, handler, methods=[norm_method])

    root_html_output: Optional[str] = None
    # Register all configured routes
    for route in routes:
        if not isinstance(route, dict):
            continue
        path = route.get("route") or route.get("path") or "/"
        method = str(route.get("method", "GET")).upper()
        if path == "/" and method == "GET":
            root_html_output = route.get("html_output")
            continue
        register_route(
            path=path,
            method=method,
            status_code=int(route.get("status_code", 200)),
            headers=route.get("headers"),
            html_output=route.get("html_output"),
            text_output=route.get("text_output"),
            json_output=route.get("json_output"),
            content_type=route.get("content_type"),
        )

    @app.get("/__health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    def index() -> Response:
        # Build a clickable map of all GET routes currently registered.
        links: List[str] = []
        seen_paths = set()
        for r in app.routes:
            path = getattr(r, "path", None)
            methods = getattr(r, "methods", set())
            if not path or "GET" not in methods or path in seen_paths:
                continue
            seen_paths.add(path)
            links.append(f'<li><a href="{escape(path)}">{escape(path)}</a></li>')

        intro = root_html_output or "<h1>VulnLab Dynamic Router</h1>"
        page = (
            f"{intro}\n"
            "<h2>Route map</h2>\n"
            "<ul>\n"
            f"{''.join(links)}\n"
            "</ul>\n"
        )
        return Response(content=page, media_type="text/html")

    return app


app = create_app()

