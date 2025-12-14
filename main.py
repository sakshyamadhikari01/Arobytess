from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
import base64
import numpy as np
from io import BytesIO
from PIL import Image


import tensorflow as tf

app = FastAPI(title="Gaun Roots API")


MODEL_PATH = os.path.join(os.path.dirname(__file__), "plant.keras")
plant_model = None
CLASS_NAMES = ["diseased", "healthy"]  # Based on binary classification from notebook

def load_model():
    global plant_model
    if plant_model is None and os.path.exists(MODEL_PATH):
        try:
            plant_model = tf.keras.models.load_model(MODEL_PATH)
            print("Plant disease model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
    return plant_model

load_model()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
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

class UserCreate(BaseModel):
    name: str
    type: str

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

class ImageData(BaseModel):
    image: str

def preprocess_image(image_data: str) -> np.ndarray:
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    
    image_bytes = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_bytes))
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    image = image.resize((160, 160))
    
    img_array = np.array(image, dtype=np.float32)
    
    img_array = np.expand_dims(img_array, axis=0)
    
    return img_array

@app.post("/api/predict")
async def predict_plant_disease(data: ImageData):
    """Predict if plant is healthy or diseased"""
    model = load_model()
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    try:
        processed_image = preprocess_image(data.image)
        
        prediction = model.predict(processed_image, verbose=0)
        confidence = float(prediction[0][0])
        
        is_healthy = confidence >= 0.5
        
        return {
            "prediction": "healthy" if is_healthy else "diseased",
            "confidence": confidence if is_healthy else (1 - confidence),
            "raw_score": confidence
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.post("/api/users/register")
def register_user(user: UserCreate):
    users = load_data(USERS_FILE)
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

@app.get("/api/products")
def get_products():
    return load_data(PRODUCTS_FILE)

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

@app.get("/")
async def serve_home():
    return FileResponse(os.path.join(BASE_DIR, "templates", "home.html"))

@app.get("/{page}.html")
async def serve_page(page: str):
    file_path = os.path.join(BASE_DIR, "templates", f"{page}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Page not found")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
