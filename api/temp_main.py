from fastapi import FastAPI
from .routes import products, test_endpoint

app = FastAPI()

# Incluir routers
app.include_router(products.router)
app.include_router(test_endpoint.router)

@app.get("/")
def read_root():
    return {"Hello": "World"}
