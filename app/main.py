from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    is_offer: Optional[bool] = None
    

@app.get("/")
def read_root():
    return {"Hello": "World"}
    

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    """
    What happens when we add a docstring to this function?
    """
    return {"item_id": item_id, "q": q}
    

@app.post("/items")
def new_item(item: Item):
    return {"item_name": item.name, "item_id": item_id}
    