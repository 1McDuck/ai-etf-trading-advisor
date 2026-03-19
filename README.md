# AI ETF Financial Advisor Bot

A regime-aware sector ETF allocation system which combines unsupervised market regime detection (GMM)
with a supervised ETF ranking (Random Forest) and the web interface

## Requirements
- python 3.10+
- Node.js

## Setup and run

### 1 Clone repository
- git clone https://github.com/1McDuck/ai-etf-trading-advisor.git
- cd ai-etf-trading-advisor

### 2 Backend

- cd webapp/backent
- python -m venv venv
- venv/Scripts/activate
- pip install -r requirements.txt
- cd ..//..
- python -m uvicorn webapp.backend.main:app --host 127.0.0.1 --port 8000

### 3 Frontend

- cd webapp/frontend
- npm install
- npm run dev

### 4 Open the app
- http://localhost:3000
