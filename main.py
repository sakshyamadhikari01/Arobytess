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
import smtplib
from email.mime.text import MIMEText
import tensorflow as tf

app = FastAPI()

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_PATH = os.path.join(BASE_DIR, "plant.keras")

os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, "users.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
ALERTS_FILE = os.path.join(DATA_DIR, "alert_registrations.json")
DISEASE_REPORTS_FILE = os.path.join(DATA_DIR, "disease_reports.json")

EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
COMMUNITY_EMAIL = os.getenv('COMMUNITY_EMAIL')

plant_model = None
PLANT_CLASSES = ["diseased", "healthy"]


def initialize_plant_model():
    global plant_model
    if plant_model is not None:
        return plant_model
    
    if not os.path.exists(MODEL_PATH):
        return None
    
    try:
        plant_model = tf.keras.models.load_model(MODEL_PATH)
        return plant_model
    except Exception:
        return None

initialize_plant_model()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserCreate(BaseModel):
    name: str
    type: str

class UserLogin(BaseModel):
    name: str
    type: str

class UserUpdate(BaseModel):
    credits: Optional[int] = None
    friends: Optional[list] = None
    tokens: Optional[int] = None


class TokenPurchase(BaseModel):
    quantity: int

class ProductCreate(BaseModel):
    name: str
    price: float
    description: str
    type: str
    phone: str

class ImageData(BaseModel):
    image: str

class AlertRegistration(BaseModel):
    farmerName: str
    phoneNumber: str
    cropTypes: str
    alertRadius: int

class DiseaseReport(BaseModel):
    diseaseName: str
    cropType: str
    severity: str
    description: Optional[str] = None
    location: Optional[str] = "Bharatpur"

class EmailAlert(BaseModel):
    email: str
    disease: Optional[str] = "Late Blight"
    crop: Optional[str] = "Tomato"
    location: Optional[str] = "Kathmandu Valley"

def read_json_file(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as file:
        return json.load(file)

def write_json_file(filepath, data):
    with open(filepath, "w") as file:
        json.dump(data, file, indent=2)

def prepare_image_for_prediction(image_data: str) -> np.ndarray:
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    
    decoded_bytes = base64.b64decode(image_data)
    img = Image.open(BytesIO(decoded_bytes))
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    img = img.resize((160, 160))
    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)
    
    return img_array


async def send_disease_alert_email(recipient: str, disease: str, crop: str, location: str) -> bool:
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return False
    
    try:
        subject = f"Crop Disease Alert: {disease} detected in {crop}"
        body = f"""Disease Alert Notification - Gaun Roots

A disease outbreak has been reported in your area.
Disease: {disease}
Affected Crop: {crop}
Location: {location}

Please inspect your crops immediately and take necessary preventive measures.

Stay safe,
Gaun Roots Team"""
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception:
        return False

async def alert_nearby_farmers(location: str, disease: str, crop: str):
    notifications_sent = 0
    
    try:
        if COMMUNITY_EMAIL:
            success = await send_disease_alert_email(COMMUNITY_EMAIL, disease, crop, location)
            if success:
                notifications_sent += 1
        
        return notifications_sent
    except Exception:
        return 0

@app.post("/api/register-alerts")
async def register_for_alerts(registration: AlertRegistration):
    try:
        alerts = read_json_file(ALERTS_FILE)
        
        existing_reg = None
        for alert in alerts:
            if alert["phoneNumber"] == registration.phoneNumber:
                existing_reg = alert
                break
        
        detected_location = "Bharatpur"
        
        if existing_reg:
            existing_reg.update(registration.model_dump())
            existing_reg["location"] = detected_location
            existing_reg["updatedAt"] = "2024-12-14T00:00:00Z"
            result = existing_reg
        else:
            new_reg = registration.model_dump()
            new_reg["id"] = len(alerts) + 1
            new_reg["location"] = detected_location
            new_reg["registeredAt"] = "2024-12-14T00:00:00Z"
            new_reg["isActive"] = True
            alerts.append(new_reg)
            result = new_reg
        
        write_json_file(ALERTS_FILE, alerts)
        
        return {
            "success": True,
            "message": f"Alert registration successful for {detected_location}",
            "registration": result
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Registration error: {str(err)}")


@app.post("/api/report-disease")
async def report_disease(report: DiseaseReport):
    try:
        reports = read_json_file(DISEASE_REPORTS_FILE)
        
        detected_location = "Bharatpur"
        
        new_report = report.model_dump()
        new_report["id"] = len(reports) + 1
        new_report["location"] = detected_location
        new_report["reportedAt"] = "2024-12-14T00:00:00Z"
        new_report["status"] = "pending_verification"
        
        reports.append(new_report)
        write_json_file(DISEASE_REPORTS_FILE, reports)
        
        farmers_notified = await alert_nearby_farmers(
            detected_location, 
            report.diseaseName, 
            report.cropType
        )
        
        return {
            "success": True,
            "message": f"Disease report submitted for {detected_location}",
            "report": new_report,
            "notified_farmers": farmers_notified
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Report submission error: {str(err)}")


@app.post("/api/send-alert")
async def send_alert(alert: EmailAlert):
    try:
        success = await send_disease_alert_email(
            alert.email, 
            alert.disease, 
            alert.crop, 
            alert.location
        )
        
        if success:
            return {
                "success": True,
                "message": f"Alert sent to {alert.email}",
                "details": {
                    "email": alert.email,
                    "disease": alert.disease,
                    "crop": alert.crop,
                    "location": alert.location
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Email delivery failed")
            
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Alert error: {str(err)}")


@app.post("/api/send-community-alert")
async def send_community_alert():
    try:
        demo_data = {
            "disease": "Late Blight",
            "crop": "Tomato",
            "location": "Bharatpur"
        }
        
        notifications = await alert_nearby_farmers(
            demo_data["location"],
            demo_data["disease"],
            demo_data["crop"]
        )
        
        return {
            "success": True,
            "message": "Community alert broadcast complete",
            "notifications_sent": notifications
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Community alert error: {str(err)}")


@app.get("/api/recent-alerts")
async def get_recent_alerts(location: Optional[str] = None):
    try:
        reports = read_json_file(DISEASE_REPORTS_FILE)
        
        if location:
            reports = [r for r in reports if location.lower() in r["location"].lower()]
        
        sorted_reports = sorted(reports, key=lambda x: x["reportedAt"], reverse=True)[:10]
        
        return {
            "success": True,
            "alerts": sorted_reports
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alerts: {str(err)}")

@app.post("/api/predict")
async def predict_plant_disease(data: ImageData):
    model = initialize_plant_model()
    if model is None:
        raise HTTPException(status_code=500, detail="Disease detection model unavailable")
    
    try:
        processed_img = prepare_image_for_prediction(data.image)
        prediction = model.predict(processed_img, verbose=0)
        confidence_score = float(prediction[0][0])
        is_healthy = confidence_score >= 0.5
        
        return {
            "prediction": "healthy" if is_healthy else "diseased",
            "confidence": confidence_score if is_healthy else (1 - confidence_score),
            "raw_score": confidence_score
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(err)}")

<<<<<<< Updated upstream
=======

# --- User Management Endpoints ---

def get_current_month():
    """Get current month in YYYY-MM format"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m")


def check_and_reset_monthly_tokens(user):
    """Check if user needs monthly token reset (5 free tokens)"""
    current_month = get_current_month()
    last_reset = user.get("lastTokenReset", "")
    
    if last_reset != current_month:
        user["tokens"] = 5  # Free monthly tokens
        user["lastTokenReset"] = current_month
        return True
    return False


>>>>>>> Stashed changes
@app.post("/api/users/register")
def register_user(user: UserCreate):
    users = read_json_file(USERS_FILE)
    
    for u in users:
        if u["name"].lower() == user.name.lower() and u["type"] == user.type:
            raise HTTPException(status_code=400, detail="User already exists")
    
    new_user = {
        "id": len(users) + 1,
        "name": user.name,
        "type": user.type,
        "credits": 0,
        "friends": [],
        "tokens": 5,  # Free 5 tokens on registration
        "lastTokenReset": get_current_month()
    }
    users.append(new_user)
    write_json_file(USERS_FILE, users)
    return new_user

@app.post("/api/users/login")
def login_user(user: UserLogin):
    users = read_json_file(USERS_FILE)
    
    for i, u in enumerate(users):
        if u["name"].lower() == user.name.lower() and u["type"] == user.type:
            # Check and reset monthly tokens if needed
            if check_and_reset_monthly_tokens(users[i]):
                write_json_file(USERS_FILE, users)
            return users[i]
    
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    users = read_json_file(USERS_FILE)
    
    for u in users:
        if u["id"] == user_id:
            return u
    
    raise HTTPException(status_code=404, detail="User not found")

@app.put("/api/users/{user_id}")
def update_user(user_id: int, update: UserUpdate):
    users = read_json_file(USERS_FILE)
    
    for i, u in enumerate(users):
        if u["id"] == user_id:
            if update.credits is not None:
                users[i]["credits"] = update.credits
            if update.friends is not None:
                users[i]["friends"] = update.friends
            if update.tokens is not None:
                users[i]["tokens"] = update.tokens
            write_json_file(USERS_FILE, users)
            return users[i]
    
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/api/users/{user_id}/add-credits")
def add_credits(user_id: int, amount: int):
    users = read_json_file(USERS_FILE)
    
    for i, u in enumerate(users):
        if u["id"] == user_id:
            current_credits = users[i].get("credits", 0)
            users[i]["credits"] = current_credits + amount
            write_json_file(USERS_FILE, users)
            return users[i]
    
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/api/users/{user_id}/add-friend")
def add_friend(user_id: int, friend_name: str):
    users = read_json_file(USERS_FILE)
    
    for i, u in enumerate(users):
        if u["id"] == user_id:
            if "friends" not in users[i]:
                users[i]["friends"] = []
            if friend_name not in users[i]["friends"]:
                users[i]["friends"].append(friend_name)
            write_json_file(USERS_FILE, users)
            return users[i]
    
    raise HTTPException(status_code=404, detail="User not found")

<<<<<<< Updated upstream
=======

# --- Token System Endpoints ---

TOKEN_PRICE = 49.99  # Rs per token


@app.get("/api/users/{user_id}/tokens")
def get_user_tokens(user_id: int):
    """Get user's current token balance"""
    users = read_json_file(USERS_FILE)
    
    for i, u in enumerate(users):
        if u["id"] == user_id:
            # Check and reset monthly tokens if needed
            if check_and_reset_monthly_tokens(users[i]):
                write_json_file(USERS_FILE, users)
            return {
                "tokens": users[i].get("tokens", 0),
                "lastReset": users[i].get("lastTokenReset", ""),
                "pricePerToken": TOKEN_PRICE
            }
    
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/api/users/{user_id}/purchase-tokens")
def purchase_tokens(user_id: int, purchase: TokenPurchase):
    """Purchase additional tokens (Rs 49.99 per token)"""
    if purchase.quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    
    users = read_json_file(USERS_FILE)
    
    for i, u in enumerate(users):
        if u["id"] == user_id:
            current_tokens = users[i].get("tokens", 0)
            users[i]["tokens"] = current_tokens + purchase.quantity
            write_json_file(USERS_FILE, users)
            
            total_cost = purchase.quantity * TOKEN_PRICE
            return {
                "success": True,
                "message": f"Purchased {purchase.quantity} token(s) for Rs {total_cost:.2f}",
                "tokens": users[i]["tokens"],
                "totalCost": total_cost
            }
    
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/api/users/{user_id}/use-token")
def use_token(user_id: int):
    """Consume one token for a scan"""
    users = read_json_file(USERS_FILE)
    
    for i, u in enumerate(users):
        if u["id"] == user_id:
            # Check and reset monthly tokens if needed
            check_and_reset_monthly_tokens(users[i])
            
            current_tokens = users[i].get("tokens", 0)
            if current_tokens < 1:
                raise HTTPException(
                    status_code=402, 
                    detail="Insufficient tokens. Please purchase more tokens to continue scanning."
                )
            
            users[i]["tokens"] = current_tokens - 1
            write_json_file(USERS_FILE, users)
            
            return {
                "success": True,
                "remainingTokens": users[i]["tokens"]
            }
    
    raise HTTPException(status_code=404, detail="User not found")


# --- Product Management Endpoints ---

>>>>>>> Stashed changes
@app.get("/api/products")
def get_products():
    return read_json_file(PRODUCTS_FILE)

@app.get("/api/products/seller/{seller_id}")
def get_seller_products(seller_id: int):
    products = read_json_file(PRODUCTS_FILE)
    return [p for p in products if p["seller_id"] == seller_id]

@app.post("/api/products")
def create_product(product: ProductCreate, seller_id: int, seller_name: str):
    products = read_json_file(PRODUCTS_FILE)
    
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
    write_json_file(PRODUCTS_FILE, products)
    return new_product

@app.delete("/api/products/{product_id}")
def delete_product(product_id: int):
    products = read_json_file(PRODUCTS_FILE)
    products = [p for p in products if p["id"] != product_id]
    write_json_file(PRODUCTS_FILE, products)
    return {"message": "Product removed successfully"}

@app.post("/api/products/{product_id}/view")
def increment_view(product_id: int):
    products = read_json_file(PRODUCTS_FILE)
    
    for i, p in enumerate(products):
        if p["id"] == product_id:
            products[i]["views"] = products[i].get("views", 0) + 1
            write_json_file(PRODUCTS_FILE, products)
            return products[i]
    
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
