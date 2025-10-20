## Routes Module

Use this package to group related FastAPI routers. Each submodule should expose
an `APIRouter` that is registered in `main.py` so the endpoints become active.

#### Conventions

- Keep routers small and focused on a single feature or resource.
- Add a short module docstring describing the endpoints in the router.
- Remember to import the router in `main.py` and include it on the main FastAPI app.
