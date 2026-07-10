import os, random, json, bcrypt, datetime, time, string
from urllib.request import urlopen
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from urllib.parse import urlparse
from datetime import date
import openai

from database import SessionLocal, User, VirtualCard, Transaction, SquadPool, SquadContribution

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
client = openai.OpenAI(base_url="https://api.fireworks.ai/inference/v1", api_key=FIREWORKS_API_KEY)

app = FastAPI(title="PayEvery API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── Real-time Exchange Rates (1-hour cache) ──────────────────────────────────
_rate_cache: dict = {"ts": 0, "rates": {}}

def get_exchange_rates() -> dict:
    now = time.time()
    if now - _rate_cache["ts"] < 3600 and _rate_cache["rates"]:
        return _rate_cache["rates"]
    try:
        with urlopen("https://open.er-api.com/v6/latest/BDT", timeout=5) as r:
            data = json.loads(r.read())
        raw = data["rates"]
        bdt_per = {"BDT": 1.0, "USD": 1/raw["USD"], "EUR": 1/raw["EUR"], "GBP": 1/raw["GBP"], "INR": 1/raw["INR"]}
        _rate_cache["ts"] = now
        _rate_cache["rates"] = bdt_per
        print(f"[Rates] Updated: {bdt_per}")
        return bdt_per
    except Exception as e:
        print(f"[Rates] Fetch failed ({e}), using fallback.")
        return {"BDT": 1.0, "USD": 110.0, "EUR": 120.0, "GBP": 140.0, "INR": 1.30}

# ── Domain Lists ─────────────────────────────────────────────────────────────
SCAM_DOMAINS = [
    "scam.xxx", "pilosaleltd.xxx", "freemoney-generator.xxx",
    "get-rich-quick.biz", "fake-paypal.net", "bitcoin-doubler.io",
    "lottery-winner.click", "free-iphone.win", "virus-alert.info",
    "claimprize.online", "urgentbankverify.com", "phishing-bank.net",
    "creditcard-stolen.ru", "winmoney247.xyz", "account-suspended.tk",
]

TRUSTED_WHITELIST = [
    "google.com","youtube.com","microsoft.com","apple.com","github.com","gitlab.com",
    "aws.amazon.com","digitalocean.com","vercel.com","netlify.com","cloudflare.com",
    "firebase.google.com","supabase.com","heroku.com","render.com","railway.app",
    "openai.com","anthropic.com","fireworks.ai","huggingface.co","groq.com","mistral.ai",
    "netflix.com","spotify.com","disneyplus.com","hbomax.com","max.com","twitch.tv",
    "steampowered.com","epicgames.com","gog.com","roblox.com","ea.com","ubisoft.com",
    "amazon.com","amazon.co.uk","ebay.com","shopify.com","daraz.com.bd",
    "coursera.org","udemy.com","khanacademy.org","freecodecamp.org","codecademy.com",
    "paypal.com","stripe.com","bkash.com","nagad.com.bd",
    "linkedin.com","figma.com","notion.so","slack.com","discord.com",
    "squadpay.local","localhost","127.0.0.1",
]

TRUSTED_HIGH_LIMIT = [
    "google.com","microsoft.com","apple.com","aws.amazon.com","vercel.com",
    "netlify.com","github.com","openai.com","netflix.com","spotify.com",
    "steampowered.com","epicgames.com","amazon.com","ebay.com","shopify.com",
    "coursera.org","udemy.com","khanacademy.org","squadpay.local","localhost",
    "daraz.com.bd","linkedin.com","figma.com","notion.so","slack.com","discord.com",
]

# ── In-memory OTP Stores ─────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_pw(p: str) -> str:  return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
def verify_pw(p: str, h: str) -> bool: return bcrypt.checkpw(p.encode(), h.encode())

login_attempts:   dict = {}
login_otp_store:  dict = {}
payment_otp_store: dict = {}

# ── Schemas ──────────────────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    name: str; username: str; phone: str; password: str; pin: str
    bkash_number: str = ""; nagad_number: str = ""

class LoginRequest(BaseModel):    username: str; pin: str
class VerifyOTPRequest(BaseModel): username: str; otp: str
class OTPRequest(BaseModel):      username: str

class PaymentRequest(BaseModel):
    username: str; target_url: str; amount: float; currency: str
    pin: str = ""; otp: str = ""

class CardChargeRequest(BaseModel): card_number: str

class AddFundsRequest(BaseModel):
    username: str; amount: float; wallet: str = "bkash"; currency: str = "USD"

class CreatePoolRequest(BaseModel):
    leader_username: str
    target_url: str
    total_amount: float
    currency: str = "USD"
    description: str = ""

class ContributePoolRequest(BaseModel):
    pool_code: str
    contributor_username: str
    pin: str
    otp: str

class ExecutePoolRequest(BaseModel):
    pool_code: str
    leader_username: str
    pin: str
    otp: str

# ── Auth ─────────────────────────────────────────────────────────────────────
@app.get("/api/check-username")
def check_username(u: str, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.username == u.strip().lower()).first()
    return {"available": not bool(exists), "message": "Already taken" if exists else "Available"}

@app.post("/api/auth/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    uname = req.username.strip().lower()
    if db.query(User).filter(User.username == uname).first():
        raise HTTPException(400, "Username already exists")
    db.add(User(
        name=req.name.strip(), username=uname, phone=req.phone.strip(),
        password_hash=hash_pw(req.password), pin_hash=hash_pw(req.pin),
        bkash_balance=50000.0, nagad_balance=50000.0
    ))
    db.commit()
    return {"success": True, "message": "Account created! You received 50000 BDT bKash + 50000 BDT Nagad."}

@app.post("/api/auth/login-step1")
def login_step1(req: LoginRequest, db: Session = Depends(get_db)):
    key = req.username.strip().lower()
    attempts = login_attempts.get(key, 0)
    if attempts >= 3:
        raise HTTPException(403, "Account locked. Too many failed attempts.")
    user = db.query(User).filter(User.username == key).first()
    if not user or not verify_pw(req.pin, user.pin_hash):
        login_attempts[key] = attempts + 1
        raise HTTPException(401, f"Incorrect PIN or Username. {3-(attempts+1)} attempts left.")
    login_attempts[key] = 0
    otp = str(random.randint(100000, 999999))
    login_otp_store[key] = otp
    print(f"\n[Login OTP] User: {key} -> Code: {otp}\n")
    return {"status": "OTP_SENT", "phone": user.phone[-4:], "demo_otp": otp}

@app.post("/api/auth/login-step2")
def login_step2(req: VerifyOTPRequest):
    key = req.username.strip().lower()
    if login_otp_store.get(key) != req.otp:
        raise HTTPException(401, "Invalid OTP")
    del login_otp_store[key]
    return {"success": True, "username": key}

# ── Payment OTP ───────────────────────────────────────────────────────────────
@app.post("/api/payment/request-otp")
def request_payment_otp(req: OTPRequest, db: Session = Depends(get_db)):
    key = req.username.strip().lower()
    user = db.query(User).filter(User.username == key).first()
    if not user:
        raise HTTPException(404, "User not found")
    otp = str(random.randint(100000, 999999))
    payment_otp_store[key] = otp
    print(f"\n[Payment OTP] User: {key} -> Code: {otp}\n")
    return {"demo_otp": otp, "phone": user.phone[-4:]}

# ── URL Safety ────────────────────────────────────────────────────────────────
def check_url_safety(url: str) -> dict:
    url_lower = url.lower()
    if any(d in url_lower for d in SCAM_DOMAINS):
        return {"verdict": "SCAM", "score": 0, "reason": "Known scam domain blocked by PayEvery security"}
    if any(d in url_lower for d in TRUSTED_WHITELIST):
        return {"verdict": "SAFE", "score": 99, "reason": "Verified trusted domain in our security whitelist"}
    try:
        prompt = (
            f'Analyze this URL for security threats. Return ONLY valid JSON.\n'
            f'Format: {{"verdict":"SAFE","score":95,"reason":"one sentence"}}\n'
            f'verdict must be "SAFE" or "SCAM". score 0-100 (100=completely safe, 0=definite scam).\n'
            f'URL: \'{url}\' ->'
        )
        resp = client.chat.completions.create(
            model="accounts/fireworks/models/gemma-4-26b-a4b-it",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        raw = resp.choices[0].message.content.strip()
        s, e = raw.find('{'), raw.rfind('}') + 1
        if s >= 0 and e > s:
            result = json.loads(raw[s:e])
            result.setdefault("verdict", "SCAM")
            result.setdefault("score", 10)
            result.setdefault("reason", "AI analysis inconclusive")
            return result
        safe = '"SAFE"' in raw.upper()
        return {"verdict": "SAFE" if safe else "SCAM", "score": 70 if safe else 10, "reason": "AI fallback"}
    except Exception as ex:
        print(f"AI Error: {ex}")
        return {"verdict": "SCAM", "score": 0, "reason": "Security service unavailable — blocking for safety"}

@app.get("/api/check-url")
def check_url_endpoint(url: str):
    """Pre-check URL safety before payment — returns trust score without touching balance."""
    return check_url_safety(url)

# ── Single Payment ───────────────────────────────────────────────────────────
@app.post("/api/split-payment")
def process_payment(req: PaymentRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username.strip().lower()).first()
    if not user:
        raise HTTPException(404, "User not found")
    if req.pin and not verify_pw(req.pin, user.pin_hash):
        raise HTTPException(401, "Invalid PIN")
    key = req.username.strip().lower()
    if req.otp:
        expected = payment_otp_store.get(key)
        if not expected or expected != req.otp:
            raise HTTPException(401, "Invalid payment OTP. Please request a new OTP.")
        del payment_otp_store[key]
    ai = check_url_safety(req.target_url)
    if ai["verdict"] != "SAFE":
        raise HTTPException(403, f"SCAM Detected! Risk: {100-ai['score']}%. {ai['reason']}")
    rates = get_exchange_rates()
    cur = req.currency.upper()
    if cur not in rates:
        raise HTTPException(400, f"Currency '{cur}' not supported.")
    required_bdt = round(req.amount * rates[cur], 2)
    amount_usd   = required_bdt / rates["USD"]
    domain = urlparse(req.target_url).netloc.lower()
    is_trusted_whitelist = any(td in domain for td in TRUSTED_WHITELIST)

    if is_trusted_whitelist:
        if amount_usd > 150.0:
            raise HTTPException(403, "Trusted site maximum limit per transaction is $150.00.")
    else:
        daily_limit = 50.0
        today = date.today()
        txs_today = db.query(Transaction).filter(
            Transaction.user_id == user.id, Transaction.date == today
        ).all()
        
        spent = 0.0
        for tx in txs_today:
            tx_domain = urlparse(tx.merchant).netloc.lower()
            if not any(td in tx_domain for td in TRUSTED_WHITELIST):
                spent += tx.amount_usd
                
        if spent + amount_usd > daily_limit:
            raise HTTPException(403, f"AML Alert: Daily limit ${daily_limit} exceeded! Spent today: ${round(spent,2)}")
    if user.bkash_balance + user.nagad_balance < required_bdt:
        raise HTTPException(400, f"Insufficient funds. Need ৳{required_bdt}, have ৳{user.bkash_balance+user.nagad_balance}.")
    bkash_d = min(user.bkash_balance, required_bdt)
    nagad_d  = required_bdt - bkash_d
    user.bkash_balance = round(user.bkash_balance - bkash_d, 2)
    user.nagad_balance = round(user.nagad_balance - nagad_d, 2)
    card_number = f"{random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}"
    exp_m = (today.month % 12) + 1
    exp_y = today.year + (2 if exp_m == 1 else 1)
    expiry = f"{exp_m:02d}/{str(exp_y)[2:]}"
    cvv = f"{random.randint(100, 999)}"
    db.add(VirtualCard(user_id=user.id, card_number=card_number, status="ACTIVE"))
    db.add(Transaction(
        user_id=user.id, amount=req.amount, amount_usd=amount_usd,
        currency=cur, merchant=req.target_url, tx_type="SINGLE"
    ))
    db.commit()
    return {
        "status": "success", "merchant": req.target_url,
        "ai_safety_status": "Verified Safe by AI",
        "trust_score": ai["score"], "risk_reason": ai["reason"],
        "amount_bdt": required_bdt, "amount_requested": f"{req.amount} {cur}",
        "virtual_card": card_number, "expiry": expiry, "cvv": cvv
    }

# ── Squad Pay Pool Endpoints ──────────────────────────────────────────────────
def gen_pool_code() -> str:
    return "SQUAD-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.post("/api/squad/create-pool")
def create_pool(req: CreatePoolRequest, db: Session = Depends(get_db)):
    leader = db.query(User).filter(User.username == req.leader_username.strip().lower()).first()
    if not leader:
        raise HTTPException(404, "Leader user not found")
    ai = check_url_safety(req.target_url)
    rates = get_exchange_rates()
    cur = req.currency.upper()
    if cur not in rates:
        raise HTTPException(400, f"Currency '{cur}' not supported.")
    total_bdt = round(req.total_amount * rates[cur], 2)
    amount_usd = total_bdt / rates["USD"]

    domain = urlparse(req.target_url).netloc.lower()
    is_trusted_whitelist = any(td in domain for td in TRUSTED_WHITELIST)

    if is_trusted_whitelist:
        if amount_usd > 150.0:
            raise HTTPException(403, "Trusted site maximum limit per transaction is $150.00.")
    else:
        daily_limit = 50.0
        today = date.today()
        txs_today = db.query(Transaction).filter(
            Transaction.user_id == leader.id, Transaction.date == today
        ).all()
        
        spent = 0.0
        for tx in txs_today:
            tx_domain = urlparse(tx.merchant).netloc.lower()
            if not any(td in tx_domain for td in TRUSTED_WHITELIST):
                spent += tx.amount_usd
                
        if spent + amount_usd > daily_limit:
            raise HTTPException(403, f"AML Alert: Daily limit ${daily_limit} exceeded! Spent today: ${round(spent,2)}")

    # Generate unique pool code
    code = gen_pool_code()
    while db.query(SquadPool).filter(SquadPool.pool_code == code).first():
        code = gen_pool_code()
    pool = SquadPool(
        pool_code=code,
        leader_id=leader.id,
        target_url=req.target_url,
        total_amount=req.total_amount,
        currency=cur,
        total_bdt=total_bdt,
        collected_bdt=0.0,
        status="OPEN",
        description=req.description,
    )
    db.add(pool)
    db.commit()
    db.refresh(pool)
    return {
        "pool_code": code,
        "total_amount": req.total_amount,
        "currency": cur,
        "total_bdt": total_bdt,
        "collected_bdt": 0.0,
        "target_url": req.target_url,
        "description": req.description,
        "trust_score": ai["score"],
        "trust_reason": ai["reason"],
        "status": "OPEN",
    }

@app.get("/api/squad/pool/{pool_code}")
def get_pool(pool_code: str, db: Session = Depends(get_db)):
    pool = db.query(SquadPool).filter(SquadPool.pool_code == pool_code.upper()).first()
    if not pool:
        raise HTTPException(404, "Pool not found")
    leader = db.query(User).filter(User.id == pool.leader_id).first()
    contribs = db.query(SquadContribution).filter(SquadContribution.pool_id == pool.id).all()
    contrib_list = [{"username": c.username, "amount_bdt": c.amount_bdt, "paid_at": str(c.paid_at)} for c in contribs]
    rates = get_exchange_rates()
    return {
        "pool_code": pool.pool_code,
        "leader": leader.username if leader else "",
        "leader_name": leader.name if leader else "",
        "target_url": pool.target_url,
        "total_amount": pool.total_amount,
        "currency": pool.currency,
        "total_bdt": pool.total_bdt,
        "collected_bdt": pool.collected_bdt,
        "remaining_bdt": round(pool.total_bdt - pool.collected_bdt, 2),
        "remaining_amount": round((pool.total_bdt - pool.collected_bdt) / rates.get(pool.currency, 110.0), 2),
        "progress_pct": round(pool.collected_bdt / pool.total_bdt * 100, 1) if pool.total_bdt > 0 else 0,
        "status": pool.status,
        "description": pool.description,
        "contributions": contrib_list,
        "virtual_card": pool.virtual_card,
        "expiry": pool.expiry,
        "cvv": pool.cvv,
    }

@app.post("/api/squad/contribute")
def contribute_to_pool(req: ContributePoolRequest, db: Session = Depends(get_db)):
    pool = db.query(SquadPool).filter(SquadPool.pool_code == req.pool_code.upper()).first()
    if not pool:
        raise HTTPException(404, "Pool not found")
    if pool.status != "OPEN":
        raise HTTPException(400, f"Pool is {pool.status}. Cannot contribute.")
    user = db.query(User).filter(User.username == req.contributor_username.strip().lower()).first()
    if not user:
        raise HTTPException(404, "Contributor not found")
    if not verify_pw(req.pin, user.pin_hash):
        raise HTTPException(401, "Invalid PIN")
    # Verify OTP
    key = req.contributor_username.strip().lower()
    expected = payment_otp_store.get(key)
    if not expected or expected != req.otp:
        raise HTTPException(401, "Invalid OTP. Please request a new one.")
    del payment_otp_store[key]

    # Calculate how much they need to pay
    remaining_bdt = round(pool.total_bdt - pool.collected_bdt, 2)
    if remaining_bdt <= 0:
        raise HTTPException(400, "Pool is already fully funded!")
    # Contributor pays their share (up to remaining)
    share_bdt = min(remaining_bdt, user.bkash_balance + user.nagad_balance)
    if share_bdt <= 0:
        raise HTTPException(400, "Insufficient funds to contribute.")
    # Deduct from contributor
    bkash_d = min(user.bkash_balance, share_bdt)
    nagad_d  = share_bdt - bkash_d
    user.bkash_balance = round(user.bkash_balance - bkash_d, 2)
    user.nagad_balance = round(user.nagad_balance - nagad_d, 2)
    # Record contribution
    db.add(SquadContribution(pool_id=pool.id, user_id=user.id, username=user.username, amount_bdt=share_bdt))
    pool.collected_bdt = round(pool.collected_bdt + share_bdt, 2)
    if pool.collected_bdt >= pool.total_bdt:
        pool.status = "FUNDED"
    db.commit()
    return {
        "success": True,
        "contributed_bdt": share_bdt,
        "collected_bdt": pool.collected_bdt,
        "total_bdt": pool.total_bdt,
        "status": pool.status,
        "message": f"✅ Contributed ৳{share_bdt:.2f}! Pool is now {pool.status}."
    }

@app.post("/api/squad/execute")
def execute_pool_payment(req: ExecutePoolRequest, db: Session = Depends(get_db)):
    pool = db.query(SquadPool).filter(SquadPool.pool_code == req.pool_code.upper()).first()
    if not pool:
        raise HTTPException(404, "Pool not found")
    leader = db.query(User).filter(User.username == req.leader_username.strip().lower()).first()
    if not leader or leader.id != pool.leader_id:
        raise HTTPException(403, "Only the squad leader can execute the payment.")
    if pool.status not in ("OPEN", "FUNDED"):
        raise HTTPException(400, f"Pool cannot be executed. Status: {pool.status}")
    if not verify_pw(req.pin, leader.pin_hash):
        raise HTTPException(401, "Invalid PIN")
    key = req.leader_username.strip().lower()
    expected = payment_otp_store.get(key)
    if not expected or expected != req.otp:
        raise HTTPException(401, "Invalid OTP. Please request a new one.")
    del payment_otp_store[key]

    # Leader pays the remaining (if any)
    still_needed = round(pool.total_bdt - pool.collected_bdt, 2)
    if still_needed > 0:
        if leader.bkash_balance + leader.nagad_balance < still_needed:
            raise HTTPException(400, f"Leader needs ৳{still_needed} more but only has ৳{leader.bkash_balance + leader.nagad_balance:.2f}.")
        bkash_d = min(leader.bkash_balance, still_needed)
        nagad_d  = still_needed - bkash_d
        leader.bkash_balance = round(leader.bkash_balance - bkash_d, 2)
        leader.nagad_balance = round(leader.nagad_balance - nagad_d, 2)
        db.add(SquadContribution(pool_id=pool.id, user_id=leader.id, username=leader.username, amount_bdt=still_needed))
        pool.collected_bdt = pool.total_bdt

    # Security check
    ai = check_url_safety(pool.target_url)
    if ai["verdict"] != "SAFE":
        raise HTTPException(403, f"SCAM Detected on target URL! {ai['reason']}")

    # Generate the unified virtual card
    rates = get_exchange_rates()
    amount_usd = round(pool.total_bdt / rates.get("USD", 110.0), 4)
    today = date.today()
    card_number = f"{random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)} {random.randint(1000,9999)}"
    exp_m = (today.month % 12) + 1
    exp_y = today.year + (2 if exp_m == 1 else 1)
    expiry = f"{exp_m:02d}/{str(exp_y)[2:]}"
    cvv = f"{random.randint(100, 999)}"

    pool.status = "COMPLETED"
    pool.virtual_card = card_number
    pool.expiry = expiry
    pool.cvv = cvv

    db.add(VirtualCard(user_id=leader.id, card_number=card_number, status="ACTIVE"))
    db.add(Transaction(
        user_id=leader.id, amount=pool.total_amount, amount_usd=amount_usd,
        currency=pool.currency, merchant=pool.target_url, tx_type="SQUAD"
    ))
    db.commit()

    return {
        "status": "success",
        "pool_code": pool.pool_code,
        "virtual_card": card_number,
        "expiry": expiry,
        "cvv": cvv,
        "amount": pool.total_amount,
        "currency": pool.currency,
        "amount_bdt": pool.total_bdt,
        "amount_usd": amount_usd,
        "merchant": pool.target_url,
    }

@app.get("/api/squad/my-pools/{username}")
def get_my_pools(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username.strip().lower()).first()
    if not user:
        raise HTTPException(404, "User not found")
    rates = get_exchange_rates()
    # Pools I created
    led = db.query(SquadPool).filter(SquadPool.leader_id == user.id).order_by(SquadPool.id.desc()).all()
    # Pools I contributed to
    my_contrib_pool_ids = [c.pool_id for c in db.query(SquadContribution).filter(SquadContribution.user_id == user.id).all()]
    all_pools = {p.id: p for p in led}
    for pid in my_contrib_pool_ids:
        if pid not in all_pools:
            p = db.query(SquadPool).filter(SquadPool.id == pid).first()
            if p: all_pools[pid] = p
    result = []
    for p in sorted(all_pools.values(), key=lambda x: -x.id):
        ldr = db.query(User).filter(User.id == p.leader_id).first()
        result.append({
            "pool_code": p.pool_code,
            "description": p.description,
            "target_url": p.target_url,
            "total_amount": p.total_amount,
            "currency": p.currency,
            "total_bdt": p.total_bdt,
            "collected_bdt": p.collected_bdt,
            "progress_pct": round(p.collected_bdt / p.total_bdt * 100, 1) if p.total_bdt > 0 else 0,
            "status": p.status,
            "is_leader": ldr.username == username.strip().lower() if ldr else False,
            "leader": ldr.username if ldr else "",
            "date": str(p.date),
        })
    return result

# ── Other endpoints ───────────────────────────────────────────────────────────
@app.post("/api/charge-card")
def charge_card(req: CardChargeRequest, db: Session = Depends(get_db)):
    card = db.query(VirtualCard).filter(VirtualCard.card_number == req.card_number).first()
    if not card:                      raise HTTPException(404, "Invalid Card Number.")
    if card.status == "DESTROYED":    raise HTTPException(403, "Card already DESTROYED (single-use only).")
    card.status = "DESTROYED"
    db.commit()
    return {"status": "success", "message": "Payment successful! Card permanently DESTROYED."}

@app.post("/api/user/add-funds")
def add_funds(req: AddFundsRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username.strip().lower()).first()
    if not user: raise HTTPException(404, "User not found")
    rates = get_exchange_rates()
    amount_bdt = round(req.amount * rates.get(req.currency.upper(), 1.0), 2)
    if req.wallet == "nagad":
        user.nagad_balance = round(user.nagad_balance + amount_bdt, 2)
    else:
        user.bkash_balance = round(user.bkash_balance + amount_bdt, 2)
    db.commit()
    return {"success": True, "bkash": user.bkash_balance, "nagad": user.nagad_balance,
            "total": round(user.bkash_balance + user.nagad_balance, 2)}

@app.get("/api/users")
def get_all_users(db: Session = Depends(get_db)):
    colors = ["#1A56DB","#E02424","#046C4E","#8A2BE2","#D97706"]
    return [{"name": u.name, "username": u.username, "avatar": u.name[0], "color": random.choice(colors)}
            for u in db.query(User).all()]

@app.get("/api/user/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username.strip().lower()).first()
    if not user: raise HTTPException(404, "User not found")
    rates = get_exchange_rates()
    total = round(user.bkash_balance + user.nagad_balance, 2)
    return {"name": user.name, "username": user.username,
            "bkash": user.bkash_balance, "nagad": user.nagad_balance,
            "rocket": 0.0, "total": total,
            "total_usd": round(total / rates.get("USD", 110.0), 2),
            "exchange_rates": rates}

@app.get("/api/transactions/{username}")
def get_transactions(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username.strip().lower()).first()
    if not user: raise HTTPException(404, "User not found")
    txns = db.query(Transaction).filter(Transaction.user_id == user.id).order_by(Transaction.id.desc()).limit(100).all()
    return [{"id": t.id, "merchant": t.merchant, "amount": t.amount, "currency": getattr(t,"currency","BDT"),
             "amount_usd": round(t.amount_usd, 4), "status": t.status, "date": str(t.date),
             "tx_type": getattr(t, "tx_type", "SINGLE")} for t in txns]

# ── Admin: Refill All Users (except Sohel) ────────────────────────────────────
@app.post("/api/admin/refill-all")
def refill_all_users(db: Session = Depends(get_db)):
    """Refill every user's bKash and Nagad balance to 50000 BDT each, except user 'sohel'."""
    users = db.query(User).all()
    refilled = []
    skipped = []
    for u in users:
        if u.username == "sohel":
            skipped.append(u.username)
            continue
        u.bkash_balance = 50000.0
        u.nagad_balance = 50000.0
        refilled.append(u.username)
    db.commit()
    return {
        "success": True,
        "refilled": refilled,
        "skipped": skipped,
        "message": f"Refilled {len(refilled)} users to ৳50000 bKash + ৳50000 Nagad each. Skipped: {', '.join(skipped) if skipped else 'none'}."
    }