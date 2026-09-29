from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
# from routers import upload_router, search_router # To be created

app = FastAPI(title="Sankhya Comparador de Dados API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API Backend is running"}

# app.include_router(search_router.router, prefix="/api/v1")
# app.include_router(upload_router.router, prefix="/api/v1")
