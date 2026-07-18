"""lrn main app"""

from fastapi import FastAPI

from lrn.errors import handlers
from lrn.routes import api_router
from lrn.state import lifespan

app = FastAPI(title="lrn", lifespan=lifespan)
app.include_router(api_router)
for exc_class, handler in handlers.items():
    app.add_exception_handler(exc_class, handler)
