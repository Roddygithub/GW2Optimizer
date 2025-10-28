"""Script to list all available API routes."""

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.main import app

def list_routes():
    """List all available API routes."""
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append({
                "path": route.path,
                "name": route.name,
                "methods": route.methods,
            })
    
    # Sort routes by path
    routes.sort(key=lambda x: x["path"])
    
    print("\nAvailable API routes:")
    print("-" * 80)
    for route in routes:
        print(f"{route['path']} - {route['name']} - {route['methods']}")
    print("-" * 80)
    print(f"Total routes: {len(routes)}")

if __name__ == "__main__":
    list_routes()
