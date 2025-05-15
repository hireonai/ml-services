from fastapi import APIRouter

router = APIRouter(prefix="/cover-letter-generator", tags=["cover-letter-generator"])

router.get("/")


async def root():
    return {"message": "hello world"}
