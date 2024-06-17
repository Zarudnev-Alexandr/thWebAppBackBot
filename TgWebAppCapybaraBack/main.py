from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from src.routers.users import users_router

app = FastAPI(debug=True)

origins = ["http://localhost", "http://localhost:8080", "http://localhost:3000", "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def start():
    print("Поехали")


app.include_router(users_router, prefix="/api/users", tags=["Users"])
# app.include_router(shop_router, prefix="/api/shop", tags=["Shop"])

