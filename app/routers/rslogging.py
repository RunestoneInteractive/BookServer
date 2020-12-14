from fastapi import APIRouter

router = APIRouter(
    prefix="/logger",
    tags=["logger"]
)

@router.get("/bookevent", tags=["logger"])
async def log_book_event():
    return {"hello": "world"}
    
