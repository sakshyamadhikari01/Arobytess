from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os

app = FastAPI(title="Gaun Roots API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data storage (using JSON files for simplicity)
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")

def load_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return []

def save_data(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

# Models
class UserCreate(BaseModel):
    name: str
    type: str  # farmer, vet, seller

class UserLogin(BaseModel):
    name: str
    type: str

class UserUpdate(BaseModel):
    credits: Optional[int] = None
    friends: Optional[list] = None

class ProductCreate(BaseModel):
    name: str
    price: float
    description: str
    type: str
    phone: str

# User endpoints
@app.post("/api/users/register")
def register_user(user: UserCreate):
    users = load_data(USERS_FILE)
    
    # Check if user exists
    existing = next((u for u in users if u["name"].lower() == user.name.lower() and u["type"] == user.type), None)
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    new_user = {
        "id": len(users) + 1,
        "name": user.name,
        "type": user.type,
        "credits": 0,
        "friends": []
    }
    users.append(new_user)
    save_data(USERS_FILE, users)
    return new_user

@app.post("/api/users/login")
def login_user(user: UserLogin):
    users = load_data(USERS_FILE)
    existing = next((u for u in users if u["name"].lower() == user.name.lower() and u["type"] == user.type), None)
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    return existing

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    users = load_data(USERS_FILE)
    user = next((u for u in users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/api/users/{user_id}")
def update_user(user_id: int, update: UserUpdate):
    users = load_data(USERS_FILE)
    user_idx = next((i for i, u in enumerate(users) if u["id"] == user_id), None)
    if user_idx is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if update.credits is not None:
        users[user_idx]["credits"] = update.credits
    if update.friends is not None:
        users[user_idx]["friends"] = update.friends
    
    save_data(USERS_FILE, users)
    return users[user_idx]

@app.post("/api/users/{user_id}/add-credits")
def add_credits(user_id: int, amount: int):
    users = load_data(USERS_FILE)
    user_idx = next((i for i, u in enumerate(users) if u["id"] == user_id), None)
    if user_idx is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    users[user_idx]["credits"] = users[user_idx].get("credits", 0) + amount
    save_data(USERS_FILE, users)
    return users[user_idx]

@app.post("/api/users/{user_id}/add-friend")
def add_friend(user_id: int, friend_name: str):
    users = load_data(USERS_FILE)
    user_idx = next((i for i, u in enumerate(users) if u["id"] == user_id), None)
    if user_idx is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if "friends" not in users[user_idx]:
        users[user_idx]["friends"] = []
    
    if friend_name not in users[user_idx]["friends"]:
        users[user_idx]["friends"].append(friend_name)
    
    save_data(USERS_FILE, users)
    return users[user_idx]

# Product endpoints
@app.get("/api/products")
def get_products():
    products = load_data(PRODUCTS_FILE)
    return products

@app.get("/api/products/seller/{seller_id}")
def get_seller_products(seller_id: int):
    products = load_data(PRODUCTS_FILE)
    return [p for p in products if p["seller_id"] == seller_id]

@app.post("/api/products")
def create_product(product: ProductCreate, seller_id: int, seller_name: str):
    products = load_data(PRODUCTS_FILE)
    
    new_product = {
        "id": len(products) + 1,
        "seller_id": seller_id,
        "seller_name": seller_name,
        "name": product.name,
        "price": product.price,
        "description": product.description,
        "type": product.type,
        "phone": product.phone,
        "views": 0
    }
    products.append(new_product)
    save_data(PRODUCTS_FILE, products)
    return new_product

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int):
    products = load_data(PRODUCTS_FILE)
    products = [p for p in products if p["id"] != product_id]
    save_data(PRODUCTS_FILE, products)
    return {"message": "Product deleted"}

@app.post("/api/products/{product_id}/view")
def increment_view(product_id: int):
    products = load_data(PRODUCTS_FILE)
    product_idx = next((i for i, p in enumerate(products) if p["id"] == product_id), None)
    if product_idx is not None:
        products[product_idx]["views"] = products[product_idx].get("views", 0) + 1
        save_data(PRODUCTS_FILE, products)
        return products[product_idx]
    raise HTTPException(status_code=404, detail="Product not found")

# Serve static files
app.mount("/", StaticFiles(directory="..", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
