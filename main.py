"""
Gaun Roots - Agricultural Platform Backend
A FastAPI application for connecting farmers with resources and disease detection
"""

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
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
import tensorflow as tf

# Load environment configuration
load_dotenv()

# Initialize the FastAPI application
app = FastAPI(
    title="Gaun Roots API",
    description="Backend services for agricultural community platform",
    version="1.0.0"
)

# Path configurations
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_PATH = os.path.join(BASE_DIR, "plant.keras")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Data file paths
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
ALERTS_FILE = os.path.join(DATA_DIR, "alert_registrations.json")
DISEASE_REPORTS_FILE = os.path.join(DATA_DIR, "disease_reports.json")

# Email configuration from environment
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
COMMUNITY_EMAIL = os.getenv('COMMUNITY_EMAIL')

# Plant disease model setup
plant_model = None
PLANT_CLASSES = ["diseased", "healthy"]


def initialize_plant_model():
    """Load the TensorFlow model for plant disease detection"""
    global plant_model
    if plant_model is not None:
        return plant_model
    
    if not os.path.exists(MODEL_PATH):
        print("Warning: Plant disease model file not found")
        return None
    
    try:
        plant_model = tf.keras.models.load_model(MODEL_PATH)
        print("Plant disease detection model loaded successfully")
        return plant_model
    except Exception as err:
        print(f"Failed to load plant model: {err}")
        return None


# Load model on startup
initialize_plant_model()

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic Models for Request Validation ---

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
    reporterPhone: str


class EmailAlert(BaseModel):
    email: str
    disease: Optional[str] = "Late Blight"
    crop: Optional[str] = "Tomato"
    location: Optional[str] = "Kathmandu Valley"


# --- Utility Functions ---

def read_json_file(filepath):
    """Read data from a JSON file, return empty list if file doesn't exist"""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as file:
        return json.load(file)


def write_json_file(filepath, data):
    """Write data to a JSON file with pretty formatting"""
    with open(filepath, "w") as file:
        json.dump(data, file, indent=2)


def prepare_image_for_prediction(image_data: str) -> np.ndarray:
    """
    Convert base64 image string to numpy array for model prediction
    Handles data URL format and resizes to model input size
    """
    # Strip data URL prefix if present
    if ',' in image_data:
        image_data = image_data.split(',')[1]
    
    # Decode and open image
    decoded_bytes = base64.b64decode(image_data)
    img = Image.open(BytesIO(decoded_bytes))
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Resize to model input dimensions
    img = img.resize((160, 160))
    
    # Convert to float array and add batch dimension
    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)
    
    return img_array


async def send_disease_alert_email(recipient: str, disease: str, crop: str, location: str) -> bool:
    """Send email notification about disease outbreak"""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("Email credentials not configured")
        return False
    
    try:
        subject = f"Crop Disease Alert: {disease} detected in {crop}"
        body = f"""
Disease Alert Notification - Gaun Roots

A disease outbreak has been reported in your area.

Disease: {disease}
Affected Crop: {crop}
Location: {location}

Please inspect your crops immediately and take necessary preventive measures.

Stay safe,
Gaun Roots Team
        """
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"Alert email sent to {recipient}")
        return True
        
    except Exception as err:
        print(f"Email sending failed: {err}")
        return False


async def alert_nearby_farmers(location: str, disease: str, crop: str):
    """Notify registered farmers about disease outbreak in their area"""
    notifications_sent = 0
    
    try:
        if COMMUNITY_EMAIL:
            success = await send_disease_alert_email(COMMUNITY_EMAIL, disease, crop, location)
            if success:
                notifications_sent += 1
                print(f"Community notification sent to {COMMUNITY_EMAIL}")
        
        return notifications_sent
    except Exception as err:
        print(f"Farmer notification error: {err}")
        return 0


# --- Alert System Endpoints ---

@app.post("/api/register-alerts")
async def register_for_alerts(registration: AlertRegistration):
    """Register a farmer for disease alert notifications"""
    try:
        alerts = read_json_file(ALERTS_FILE)
        
        # Check for existing registration
        existing_reg = None
        for alert in alerts:
            if alert["phoneNumber"] == registration.phoneNumber:
                existing_reg = alert
                break
        
        # Auto-detect location for demo
        detected_location = "Kathmandu Valley"
        
        if existing_reg:
            # Update existing registration
            existing_reg.update(registration.dict())
            existing_reg["location"] = detected_location
            existing_reg["updatedAt"] = "2024-12-14T00:00:00Z"
            result = existing_reg
        else:
            # Create new registration
            new_reg = registration.dict()
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
    """Submit a disease outbreak report and notify nearby farmers"""
    try:
        reports = read_json_file(DISEASE_REPORTS_FILE)
        
        detected_location = "Kathmandu Valley"
        
        new_report = report.dict()
        new_report["id"] = len(reports) + 1
        new_report["location"] = detected_location
        new_report["reportedAt"] = "2024-12-14T00:00:00Z"
        new_report["status"] = "pending_verification"
        
        reports.append(new_report)
        write_json_file(DISEASE_REPORTS_FILE, reports)
        
        # Notify farmers in the area
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
    """Send a disease alert email to a specific address"""
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
    """Send a demo community-wide disease alert"""
    try:
        demo_data = {
            "disease": "Late Blight",
            "crop": "Tomato",
            "location": "Kathmandu Valley"
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
    """Fetch recent disease alerts, optionally filtered by location"""
    try:
        reports = read_json_file(DISEASE_REPORTS_FILE)
        
        # Filter by location if specified
        if location:
            reports = [r for r in reports if location.lower() in r["location"].lower()]
        
        # Sort by date and limit to 10 most recent
        sorted_reports = sorted(reports, key=lambda x: x["reportedAt"], reverse=True)[:10]
        
        return {
            "success": True,
            "alerts": sorted_reports
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve alerts: {str(err)}")


# --- Plant Disease Detection Endpoint ---

@app.post("/api/predict")
async def predict_plant_disease(data: ImageData):
    """Analyze plant image and predict disease status"""
    model = initialize_plant_model()
    if model is None:
        raise HTTPException(status_code=500, detail="Disease detection model unavailable")
    
    try:
        # Prepare image for model
        processed_img = prepare_image_for_prediction(data.image)
        
        # Run prediction
        prediction = model.predict(processed_img, verbose=0)
        confidence_score = float(prediction[0][0])
        
        # Interpret results (threshold at 0.5)
        is_healthy = confidence_score >= 0.5
        
        return {
            "prediction": "healthy" if is_healthy else "diseased",
            "confidence": confidence_score if is_healthy else (1 - confidence_score),
            "raw_score": confidence_score
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(err)}")


# --- User Management Endpoints ---

@app.post("/api/users/register")
def register_user(user: UserCreate):
    """Create a new user account"""
    users = read_json_file(USERS_FILE)
    
    # Check if user already exists
    for u in users:
        if u["name"].lower() == user.name.lower() and u["type"] == user.type:
            raise HTTPException(status_code=400, detail="User already exists")
    
    new_user = {
        "id": len(users) + 1,
        "name": user.name,
        "type": user.type,
        "credits": 0,
        "friends": []
    }
    users.append(new_user)
    write_json_file(USERS_FILE, users)
    return new_user


@app.post("/api/users/login")
def login_user(user: UserLogin):
    """Authenticate and return user data"""
    users = read_json_file(USERS_FILE)
    
    for u in users:
        if u["name"].lower() == user.name.lower() and u["type"] == user.type:
            return u
    
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    """Retrieve user profile by ID"""
    users = read_json_file(USERS_FILE)
    
    for u in users:
        if u["id"] == user_id:
            return u
    
    raise HTTPException(status_code=404, detail="User not found")


@app.put("/api/users/{user_id}")
def update_user(user_id: int, update: UserUpdate):
    """Update user profile data"""
    users = read_json_file(USERS_FILE)
    
    for i, u in enumerate(users):
        if u["id"] == user_id:
            if update.credits is not None:
                users[i]["credits"] = update.credits
            if update.friends is not None:
                users[i]["friends"] = update.friends
            write_json_file(USERS_FILE, users)
            return users[i]
    
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/api/users/{user_id}/add-credits")
def add_credits(user_id: int, amount: int):
    """Add credits to user account"""
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
    """Add a friend to user's friend list"""
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


# --- Product Management Endpoints ---

@app.get("/api/products")
def get_products():
    """Get all available products"""
    return read_json_file(PRODUCTS_FILE)


@app.get("/api/products/seller/{seller_id}")
def get_seller_products(seller_id: int):
    """Get products listed by a specific seller"""
    products = read_json_file(PRODUCTS_FILE)
    return [p for p in products if p["seller_id"] == seller_id]


@app.post("/api/products")
def create_product(product: ProductCreate, seller_id: int, seller_name: str):
    """Create a new product listing"""
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
    """Remove a product listing"""
    products = read_json_file(PRODUCTS_FILE)
    products = [p for p in products if p["id"] != product_id]
    write_json_file(PRODUCTS_FILE, products)
    return {"message": "Product removed successfully"}


@app.post("/api/products/{product_id}/view")
def increment_view(product_id: int):
    """Increment view count for a product"""
    products = read_json_file(PRODUCTS_FILE)
    
    for i, p in enumerate(products):
        if p["id"] == product_id:
            products[i]["views"] = products[i].get("views", 0) + 1
            write_json_file(PRODUCTS_FILE, products)
            return products[i]
    
    raise HTTPException(status_code=404, detail="Product not found")


# --- Static File Serving ---

@app.get("/")
async def serve_home():
    """Serve the home page"""
    return FileResponse(os.path.join(BASE_DIR, "templates", "home.html"))


@app.get("/{page}.html")
async def serve_page(page: str):
    """Serve HTML pages dynamically"""
    file_path = os.path.join(BASE_DIR, "templates", f"{page}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Page not found")


# Mount static files directory
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


# Run server when executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
