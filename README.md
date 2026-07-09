# PayEvery 🚀
**Bridging Local Wallets to Global Tech Innovation with AI-Driven Security**

*   **Frontend Application :** https://github.com/Zubaire404/payevery-fontend
*   **Backend :** https://github.com/Zubaire404/payevery-backend

## 📖 Project Overview
In South Asian nations like Bangladesh and Pakistan, major global payment networks and gateways like PayPal are completely unavailable. Furthermore, less than 5% of bank cards possess dual-currency/dollar endorsement capabilities, locking out the general youth. Thousands of talented student developers and freelancers cannot purchase essential global tech resources, subscription SaaS, server hosting, or crucial API credits required to learn or build global startups.

**PayEvery** is a local-to-global payment gateway built to democratize technology access. We enable users to generate instant virtual dollar cards funded directly through ubiquitous local Mobile Financial Services (MFS) like bKash and Nagad. By leveraging the power of AMD Developer Cloud and Google Gemma 4 AI, PayEvery ensures that every transaction is seamlessly fast and protected from malicious phishing scams in real-time.

---

## ✨ Key Features
*   **On-Demand Virtual Cards:** Generate disposable, secure international virtual cards with precise limits for quick checkouts[cite: 3].
*   **Squad Pay (Dynamic Split Payments):** A group funding layer enabling multiple student developers to pool local MFS money together to purchase shared development tools, APIs, or team subscriptions seamlessly[cite: 3].
*   **Zero-Trust Payment Gateway (AI Security):** Before virtual card authorization, PayEvery's backend automatically parses the target checkout URL[cite: 3]. Gemma evaluates the endpoint’s integrity and instantly blocks malicious platforms, ensuring user capital is 100% safe[cite: 3].

----

## ⚠️ Limitations (Hackathon Scope)
As this project was developed within the strict timeframe of the AMD Developer Hackathon Act-II, the current build has a few limitations:
*   **Simulated Card Generation:** Due to financial regulations and the lack of live banking API licenses, the virtual cards generated in the frontend are dummy/simulated data used for proof-of-concept (POC) purposes. No real monetary deduction occurs.
*   **Hardcoded MFS Integrations:** The connections to local mobile wallets (like bKash/Nagad) bypass OTP authentication for the sake of the live demo.
*   **Mocked Checkout Environment:** The AI scam detection currently runs via terminal/input prompts rather than intercepting a live payment gateway's backend payload.

---

## 🚀 Future Implementation & Progression
Our vision extends far beyond this hackathon. The progression roadmap for PayEvery includes:
1.  **AI-Driven AML Compliance:** Implementing velocity tracking and anti-money laundering pattern detection natively in the backend[cite: 3].
2.  **Cross-Border Freelance Invoicing:** Enabling international clients to settle global invoices instantly into a virtual merchant layer that auto-routes funds back into local MFS accounts[cite: 3].
3.  **Live Financial Integration:** Partnering with local banks to acquire virtual BIN (Bank Identification Number) access for legally generating real Visa/Mastercard virtual cards.
4.  **Regional Scale:** Expanding the local-to-global payment pipeline to underserved tech hubs across South Asia and Africa[cite: 3].

---

## ❓ Q&A: Problems & Solutions

**Q: Why focus on local mobile wallets (MFS) instead of banks?**
**A:** In emerging economies, a massive portion of the youth and student population is unbanked but uses mobile wallets daily. Integrating MFS removes bureaucratic banking hurdles, ensuring absolute financial inclusion for next-gen innovators[cite: 3].

**Q: How does the Squad Pay feature actually solve a real-world problem?**
**A:** AI models, cloud hosting, and pro subscriptions are expensive. If a team of developers wants to buy a shared API key, Squad Pay allows them to pool their local currency into a single requested amount. The system merges this balance and generates a single virtual card for the checkout, making collaborative purchases effortless.

**Q: Why do you need AMD Cloud and Gemma 4 for a payment app?**
**A:** Malicious actors deploy lookalike phishing forms, copycat payment portals, and scam links to steal funds from naive users[cite: 3]. Scanning checkouts in real-time requires a massive LLM (Gemma 4 Multimodal Mixture-of-Experts)[cite: 3]. Running this locally would cause massive latency, resulting in payment timeouts. AMD GPU Cloud Instances ensure high-speed, zero-latency inference, keeping the transaction smooth and safe.

**Q: Are the virtual cards generated in this repo real?**
**A:** No. The current repository contains a hackathon-ready demo. The UI and backend logic are fully functional, but it generates mock virtual cards for demonstration purposes without executing real fiat currency routing.
---

## 🛠️ Tech Stack
*   **Frontend:** Next.js & Tailwind CSS (High-performance, secure, responsive application layout)[cite: 3]
*   **Backend:** Python (FastAPI) providing asynchronous high-throughput transaction and API routing[cite: 3]
*   **AI Infrastructure:** Google Gemma 4 26B Model accessed via high-speed serverless/dedicated endpoints on Fireworks.ai[cite: 3]
*   **Compute Host:** Powered and deployed smoothly inside the AMD Developer Cloud architecture[cite: 3]

---

## 🚀 Getting Started

To run the development server of the frontend locally, follow these steps:

1. Clone the repository and navigate to the project folder.
2. Install the dependencies:
```bash
npm install
# or
yarn install
