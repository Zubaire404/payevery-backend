import os
from dotenv import load_dotenv

# .env ফাইল থেকে ডাটা লোড করবে
load_dotenv()

# সরাসরি স্ট্রিংয়ের বদলে os.getenv ব্যবহার করুন
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import random
from urllib.parse import urlparse
from datetime import date
from sqlalchemy import func
import openai # 🔴 NEW: Fireworks AI-এর মাধ্যমে Gemma ব্যবহারের জন্য

from database import SessionLocal, User, VirtualCard, Transaction

# 🔴 NEW: Fireworks AI Setup (Gemma মডেল ব্যবহার করার জন্য)
# fireworks.ai ওয়েবসাইট থেকে API Key এনে এখানে বসাবেন
FIREWORKS_API_KEY = ""
client = openai.OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key=FIREWORKS_API_KEY,
)

app = FastAPI(title="PayEvery Smart API (Gemma Powered)")

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


# 🔴 ULTIMATE FIX: Whitelisting + Few-Shot Prompting + Model Update
def check_url_safety(url: str) -> bool:
    try:
        url_lower = url.lower()
        
        # ১. Whitelist Check (AI-কে ডাকার আগেই ট্রাস্টেড সাইট চেক করা)
        trusted_domains = [
            "google.com", "youtube.com", "steampowered.com", "store.steampowered.com", "aws.com", "aws.amazon.com",
            "coursera.org", "udemy.com", "github.com", "openai.com", "canva.com",
            "linkedin.com", "notion.so", "digitalocean.com", "vercel.com", "jetbrains.com", "apple.com"
        ]
        
        # যদি লিংকটি আমাদের ট্রাস্টেড লিস্টের মধ্যে থাকে, তবে সরাসরি True রিটার্ন করবে
        if any(domain in url_lower for domain in trusted_domains):
            print(f"⚡ Bypassed AI: '{url}' is in Trusted Whitelist.")
            return True

        # ২. AI Check (নতুন লিঙ্ক বা সন্দেহজনক লিঙ্কের জন্য Few-Shot প্রম্পট)
        prompt = f"""Classify this URL as SAFE or SCAM. 
Respond with EXACTLY ONE WORD. Do not explain.

Examples:
URL: 'https://netflix.com' -> SAFE
URL: 'http://freemoney-generator.xxx' -> SCAM
URL: 'https://unknown-shop.biz' -> SCAM
URL: '{url}' -> """
        
        response = client.chat.completions.create(
          # 🔴 FIX: 404 এরর ঠিক করার জন্য মডেল আপডেট করে Gemma 4 করা হলো
          model="accounts/fireworks/models/gemma-4-26b-a4b-it", 
          messages=[{"role": "user", "content": prompt}],
          temperature=0.0 
        )
        
        # 🔴 NEW: ফিল্টার করার আগে জেমা ঠিক কী বলছে, সেটা সরাসরি টার্মিনালে প্রিন্ট করা
        raw_ai_response = response.choices[0].message.content
        print("\n" + "="*50)
        print(f"🕵️‍♂️ RAW GEMMA OUTPUT FOR '{url}':\n{raw_ai_response}")
        print("="*50 + "\n")
        
        result = raw_ai_response.strip().upper()
        
        # ৩. Smarter String Matching (যাতে ভুল করে SCAM না ধরে)
        if result.startswith("SAFE") or "SAFE" in result[:10]:
            return True
        else:
            return False 
            
    except Exception as e:
        print(f"AI Error: {e}")
        return False # নেটওয়ার্ক এরর হলে পেমেন্ট ব্লক করবে

    
@app.post("/api/split-payment")
def process_smart_payment(request: PaymentRequest, db: Session = Depends(get_db)):
    # ১. AI Security Check by Gemma
    is_safe = check_url_safety(request.target_url)
    if not is_safe:
        raise HTTPException(status_code=403, detail=f"Security Alert: '{request.target_url}' is a SCAM! Payment Blocked by Gemma.")

    user = db.query(User).filter(User.name == request.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    EXCHANGE_RATES = {"USD": 120.0, "EUR": 130.0, "INR": 1.45, "GBP": 150.0}
    user_currency = request.currency.upper()
    if user_currency not in EXCHANGE_RATES:
        raise HTTPException(status_code=400, detail=f"Currency '{user_currency}' is not supported.")

    # ২. কারেন্সি থেকে ডলারে কনভার্ট করা
    current_rate = EXCHANGE_RATES[user_currency]
    required_bdt = round(request.amount * current_rate, 2)
    amount_in_usd = required_bdt / EXCHANGE_RATES["USD"] 

    # ৩. ডোমেইন অনুযায়ী লিমিট সেট করা (আপনার AML লজিক)
    domain = urlparse(request.target_url).netloc.lower()
    # 🔴 NEW: Updated trusted domains for Students & Professionals
    trusted_domains = [
        "google.com", "steampowered.com", "store.steampowered.com", "aws.com", "aws.amazon.com",
        "coursera.org", "udemy.com", "github.com", "openai.com", "canva.com",
        "linkedin.com", "notion.so", "digitalocean.com", "vercel.com", "jetbrains.com"
    ]
    is_trusted = any(td in domain for td in trusted_domains)
    daily_limit = 150.0 if is_trusted else 50.0

    # ৪. আজকের মোট খরচের হিসাব বের করা (Anti-Money Laundering)
    today = date.today()
    today_spent = db.query(func.sum(Transaction.amount_usd)).filter(
        Transaction.user_id == user.id,
        Transaction.date == today
    ).scalar() or 0.0

    if today_spent + amount_in_usd > daily_limit:
        raise HTTPException(
            status_code=403, 
            detail=f"AML Alert: Daily limit exceeded! Trusted sites limit is $100, others $50. You already spent ${round(today_spent, 2)} today."
        )

    # ৫. ব্যালেন্স চেক এবং টাকা কাটা
    total_available_bdt = user.bkash_balance + user.nagad_balance
    if total_available_bdt < required_bdt:
        raise HTTPException(status_code=400, detail="Insufficient funds.")

    bkash_deduct, nagad_deduct, remaining_needed = 0.0, 0.0, required_bdt

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

    # ৬. ভার্চুয়াল কার্ড তৈরি করা
    card_number = f"X402-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
    new_card = VirtualCard(user_id=user.id, card_number=card_number, status="ACTIVE")
    db.add(new_card)

    # ৭. ট্রানজেকশনের ডলার ভ্যালু সেভ করা
    new_transaction = Transaction(
        user_id=user.id, 
        amount=request.amount, 
        amount_usd=amount_in_usd, 
        merchant=request.target_url
    )
    db.add(new_transaction)
    db.commit()

    return {
        "status": "success",
        "merchant": request.target_url,
        "ai_safety_status": "Verified Safe by Gemma",
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

# 🔴 FIX: ডেটাবেস থেকে সব ইউজারকে পাঠানোর API (Squad Pay এর জন্য)
@app.get("/api/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    colors = ["#1A56DB", "#E02424", "#046C4E", "#8A2BE2", "#D97706"]
    return [{"name": u.name, "avatar": u.name[0], "color": random.choice(colors)} for u in users]

# 🔴 FIX: ইউজারের রিয়েল-টাইম ব্যালেন্স পাঠানোর API
@app.get("/api/user/{username}")
def get_user_data(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "name": user.name,
        "bkash": user.bkash_balance,
        "nagad": user.nagad_balance,
        "rocket": 0.0, 
        "total": user.bkash_balance + user.nagad_balance
    }