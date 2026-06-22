
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import random


from google import genai

from database import SessionLocal, User, VirtualCard, Transaction

# ২. নতুন নিয়মে Gemini Client সেটআপ (আপনার API Key এখানে দিন)
GEMINI_API_KEY = "YOUR_API_KEY_HERE"
client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(title="PayEvery Smart API")

# CORS setup 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class PaymentRequest(BaseModel):
    username: str
    target_url: str
    amount: float
    currency: str

class CardChargeRequest(BaseModel):
    card_number: str

# ৩. নতুন নিয়মে এআই স্ক্যানার ফাংশন আপডেট করা হলো
def check_url_safety(url: str) -> bool:
    try:
        prompt = f"Is the website '{url}' generally considered a safe, legitimate merchant (like steam, epicgames, roblox, amazon), or is it a known scam/phishing/fake site? Answer with ONLY one word: SAFE or SCAM."
        
        
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        result = response.text.strip().upper()
        return "SAFE" in result
    except Exception as e:
        print(f"AI Error: {e}")
        return True

@app.post("/api/split-payment")
def process_smart_payment(request: PaymentRequest, db: Session = Depends(get_db)):
    is_safe = check_url_safety(request.target_url)
    if not is_safe:
        raise HTTPException(status_code=403, detail=f"Security Alert: '{request.target_url}' is a SCAM! Payment Blocked.")

    user = db.query(User).filter(User.name == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    EXCHANGE_RATES = {"USD": 120.0, "EUR": 130.0, "INR": 1.45, "GBP": 150.0}
    user_currency = request.currency.upper()
    if user_currency not in EXCHANGE_RATES:
        raise HTTPException(status_code=400, detail=f"Currency '{user_currency}' is not supported.")

    current_rate = EXCHANGE_RATES[user_currency]
    required_bdt = round(request.amount * current_rate, 2)

    total_available_bdt = user.bkash_balance + user.nagad_balance
    if total_available_bdt < required_bdt:
        raise HTTPException(status_code=400, detail="Insufficient funds.")

    bkash_deduct = 0.0
    nagad_deduct = 0.0
    remaining_needed = required_bdt

    if user.bkash_balance >= remaining_needed:
        bkash_deduct = remaining_needed
        remaining_needed = 0.0
    else:
        bkash_deduct = user.bkash_balance
        remaining_needed -= bkash_deduct

    if remaining_needed > 0.0:
        nagad_deduct = remaining_needed
        remaining_needed = 0.0

    user.bkash_balance = round(user.bkash_balance - bkash_deduct, 2)
    user.nagad_balance = round(user.nagad_balance - nagad_deduct, 2)

    card_number = f"X402-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
    new_card = VirtualCard(user_id=user.id, card_number=card_number, status="ACTIVE")
    db.add(new_card)

    new_transaction = Transaction(user_id=user.id, amount=request.amount, merchant=request.target_url)
    db.add(new_transaction)

    db.commit()

    return {
        "status": "success",
        "merchant": request.target_url,
        "ai_safety_status": "Verified Safe",
        "amount_requested": f"{request.amount} {user_currency}",
        "virtual_card": card_number,
        "message": "Send this card number to /api/charge-card to complete payment."
    }

@app.post("/api/charge-card")
def charge_virtual_card(request: CardChargeRequest, db: Session = Depends(get_db)):
    card = db.query(VirtualCard).filter(VirtualCard.card_number == request.card_number).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Invalid Card Number.")
    
    if card.status == "DESTROYED":
        raise HTTPException(
            status_code=403, 
            detail="Transaction Failed: This is a single-use burner card and has already been DESTROYED."
        )
    
    card.status = "DESTROYED"
    db.commit()
    
    return {
        "status": "success",
        "message": "Payment Successful! The burner card has been permanently DESTROYED."
    }