"""
Routes must not block the event loop.

An `async def` route runs on the event loop, so any blocking call in it (the
database, the synchronous OpenAI client) stalls every other request until it
returns. On Render that includes the health check, and a stall past 5 seconds
gets the server restarted mid-run. Routes that only call blocking code are
plain `def`, which FastAPI runs on a worker thread.
"""

import ast
from pathlib import Path

ROUTES = Path(__file__).resolve().parents[1] / "app" / "api" / "routes"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _route_handlers():
    for path in sorted(ROUTES.glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if any(
                isinstance(d, ast.Call) and getattr(d.func, "attr", "") in HTTP_METHODS
                for d in node.decorator_list
            ):
                yield path.stem, node


def test_there_are_routes_to_check():
    assert len(list(_route_handlers())) > 20


def test_async_routes_await_something():
    idle = [
        f"{module}.{node.name}"
        for module, node in _route_handlers()
        if isinstance(node, ast.AsyncFunctionDef)
        and not any(isinstance(n, ast.Await) for n in ast.walk(node))
    ]
    assert idle == [], (
        "These async routes never await, so their blocking calls stall the "
        f"event loop; make them plain def: {idle}"
    )


def test_async_routes_call_services_through_a_thread():
    """In an async route, service calls are awaited or handed to asyncio.to_thread."""
    blocking = []
    for module, node in _route_handlers():
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        # Calls that are the awaited expression, or passed to to_thread, are fine.
        allowed = set()
        for n in ast.walk(node):
            if isinstance(n, ast.Await) and isinstance(n.value, ast.Call):
                allowed.add(id(n.value))
        for n in ast.walk(node):
            if not isinstance(n, ast.Call) or id(n) in allowed:
                continue
            name = ast.unparse(n.func)
            if name.endswith("_service") or "_service." in name or name in {
                "check_businesses",
                "save_places",
            }:
                blocking.append(f"{module}.{node.name}: {name}")
    assert blocking == [], f"Blocking calls made directly in async routes: {blocking}"
