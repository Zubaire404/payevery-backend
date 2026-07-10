# PayEvery 💳 — AI-Powered International Payments for Bangladesh

> **Breaking the payment wall for 170 million people.**

[![Live Demo](https://img.shields.io/badge/🚀%20Live%20Demo-PayEvery-blue?style=for-the-badge)](https://payevery-fontend.onrender.com)
[![Backend API](https://img.shields.io/badge/API%20Docs-FastAPI-green?style=for-the-badge)](https://payevery-backend.onrender.com/docs)
[![Demo Video](https://img.shields.io/badge/🎬%20Watch%20Demo%20Video-OneDrive-red?style=for-the-badge)](https://1drv.ms/v/c/31d7390ef0504f11/IQBSWyXTqqmTSIVAC0va5F1sAe3iwJziCZx60ueBzsf0aEQ?e=vueR33)
[![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](#)

---

## 🎯 The Problem

Bangladesh has **170 million people** but faces a critical international payment gap:

- ❌ **PayPal** — not available in Bangladesh
- ❌ **Stripe** — not available in Bangladesh
- 💳 Only **~2.7 million** people have dual-currency cards (out of 170M)
- 📱 **65M+ bKash** and **30M+ Nagad** users have no way to pay international services
- 👩‍💻 **650,000+ freelancers** and students cannot buy SaaS tools, AI subscriptions, cloud hosting

## 💡 The Solution

**PayEvery** bridges Bangladesh's local mobile wallets (bKash, Nagad) to the global digital economy by generating **one-time virtual dollar cards** funded directly from local wallet balances.

No bank account. No foreign card. Just your phone.

---

## ✨ Key Features

### 🔐 Secure AI Checkout (Dashboard)
- Enter any merchant URL
- AI scans the domain for scams — real-time **Trust Score (0–100)**
- Scam domains are blocked automatically
- Suspicious domains (< 60 score) trigger a warning
- Authenticate with **4-digit PIN + 6-digit OTP**
- Instant one-time **Virtual Dollar Card** generated (card number, expiry, CVV)
- Card **self-destructs** after single use

### ⚡ Squad Pay
- Create a **payment pool** for a group (e.g., $30 GitHub Copilot split 3 ways)
- Share unique pool code (`SQUAD-XXXXXX`) with teammates
- Each member contributes their share from their local wallet
- Squad Leader **executes** → ONE unified virtual card generated for the full amount
- Full progress tracking and contribution history

### 🤖 Chrome Extension
- Automatically detects payment forms on any website
- Checks site trust score in real-time
- Auto-fills card number, expiry, and CVV with one click

### 🛡️ Security
- **AI-powered** URL trust scoring (Fireworks AI / Gemma-4)
- Two-factor authentication (PIN + OTP) on every payment
- **Anti-Money Laundering (AML)** daily limits per user
- Single-use cards — no re-use possible
- Known scam domain blacklist

---

## 🤖 Powered by AMD Compute + Fireworks AI (Gemma Bonus Prize)

PayEvery's AI-powered merchant safety engine runs on **AMD compute** via the **Fireworks AI** platform, using **Google's Gemma 4** model.

| AI Component | Detail |
|---|---|
| **Model** | `accounts/fireworks/models/gemma-4-26b-a4b-it` |
| **Platform** | Fireworks AI (AMD-powered inference) |
| **Task** | Real-time merchant URL safety analysis |
| **Output** | Trust Score (0–100) + verdict (SAFE/SCAM) + human-readable reason |
| **Trigger** | Every payment attempt — no cached answers, always live inference |

> This project qualifies for the **AMD Hackathon Gemma Bonus Prize** — using `gemma-4-26b-a4b-it`, one of the official qualifying models.

---

## 🏗️ Full Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, Tailwind CSS, TypeScript |
| **Backend** | FastAPI (Python), SQLite, SQLAlchemy |
| **AI Model** | **Gemma-4-26b-a4b-it** via Fireworks AI (AMD compute) |
| **Auth** | bcrypt password hashing, 2FA OTP |
| **Exchange Rates** | open.er-api.com (real-time, 1-hour cache) |
| **Extension** | Chrome Extension Manifest V3 |
| **Deployment** | Render (backend + frontend, public URLs) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- A [Fireworks AI](https://fireworks.ai) API key

### Backend Setup
```bash
cd "AMD hackathon"
python -m venv env
env\Scripts\activate          # Windows
pip install -r requirements.txt

# Add your API key
echo "FIREWORKS_API_KEY=your_key_here" > .env

# Start the server
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

### Frontend Setup
```bash
cd "Font-End/payevery-custom"
npm install
npm run dev
```

Open **https://payevery-fontend.onrender.com**

### Demo Accounts
| Username | PIN | Balance |
|---|---|---|
| `sohel` | `1234` | ৳100,000 |
| `ratul` | `1234` | ৳100,000 |
| `rifat` | `1234` | ৳100,000 |
| `hasan` | `1234` | ৳100,000 |

---

## 📱 Use Cases

1. **SaaS Subscriptions** — Figma, Notion, Adobe, Canva Pro
2. **AI Tools** — ChatGPT Plus, Claude Pro, Midjourney
3. **Cloud Hosting** — AWS, DigitalOcean, Vercel Pro
4. **Education** — Coursera, Udemy, LinkedIn Learning
5. **Developer Tools** — GitHub Copilot, JetBrains, VS Code
6. **Team Software** — Slack Pro, Linear, Notion Teams
7. **Games** — Steam, Epic Games, PlayStation
8. **VPN** — NordVPN, ExpressVPN, ProtonVPN
9. **Media** — Shutterstock, Envato Elements
10. **APIs** — OpenAI credits, Google AI credits

---

## 🗂️ Project Structure

```
payevery-backend/
├── main.py              # FastAPI application + all endpoints
├── database.py          # SQLAlchemy models (User, Card, Transaction, SquadPool)
├── requirements.txt
└── .env                 # FIREWORKS_API_KEY

payevery-frontend/
├── app/
│   ├── login/           # 2-step login (PIN + OTP)
│   ├── signup/          # Registration + free ৳2000 wallet credit
│   ├── dashboard/       # Single payment + payment history
│   ├── squad-pay/       # Collaborative payment pooling
│   └── components/
│       └── PaymentModal.tsx  # 3D virtual card display

payevery-extension/
├── manifest.json        # Chrome Extension MV3
├── popup.html           # Extension UI
├── popup.js             # Extension logic
└── content.js           # Auto-fill injection
```

---

## 🌐 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/signup` | Create account (+ ৳50,000 bKash, ৳50,000 Nagad) |
| `POST` | `/api/auth/login-step1` | Verify PIN → send OTP |
| `POST` | `/api/auth/login-step2` | Verify OTP → login |
| `GET` | `/api/check-url?url=` | AI trust score for a URL |
| `POST` | `/api/split-payment` | Execute payment → generate virtual card |
| `GET` | `/api/user/{username}` | Get balance & exchange rates |
| `GET` | `/api/transactions/{username}` | Payment history |
| `POST` | `/api/squad/create-pool` | Create squad payment pool |
| `GET` | `/api/squad/pool/{code}` | Get pool status & contributors |
| `POST` | `/api/squad/contribute` | Contribute to a pool |
| `POST` | `/api/squad/execute` | Execute pool → generate card |
| `GET` | `/api/squad/my-pools/{username}` | All pools for a user |

---

## 🏆 Built For

**AMD Developer Hackathon ACT II — Track 3: Unicorn (Open Innovation)**  
Solving financial exclusion for Bangladesh's 170 million people through AI-powered fintech, using AMD compute and the Gemma-4 model.

### 🌐 Repositories & Deployment
- **Frontend App:** https://payevery-fontend.onrender.com (Repo: [payevery-fontend](https://github.com/Zubaire404/payevery-fontend))
- **Backend API:** https://payevery-backend.onrender.com/docs (Repo: [payevery-backend](https://github.com/Zubaire404/payevery-backend))
- **Chrome Extension:** [payevery-extension](https://github.com/Zubaire404/payevery-extension)

### 🌍 Vision
PayEvery is a blueprint for financial inclusion across South and Southeast Asia. Bangladesh is Phase 1. Pakistan, Nepal, Myanmar, and dozens of other markets face the exact same payment wall — 300M+ more potential users.

---

*PayEvery — Powered by AMD. Built for the 95 million.*
