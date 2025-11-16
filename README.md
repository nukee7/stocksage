# StockSage
Understood — here is a clean, professional, project-focused README.md ONLY about your StockSage project, with no academic explanation, no unrelated topics, and fully aligned with your project’s codebase (GitHub: nukee7/stocksage).

TEAM MEMBERS:
NIKHIL KUMAR 23BDS038
PRADNESH FERNANDEZ A 23BDS044
PALAK GUPTA 23BDS042
VAIBHAV SHARMA 23BDS066
SHIVANSH SHUKLA 23BDS054


⸻

 StockSage — AI-Powered Portfolio Manager & Financial Assistant

StockSage is an end-to-end financial analytics system that combines live market data, personal portfolio management, stock prediction models, and a LangChain-powered AI chatbot into a single unified platform.

The system has a FastAPI backend, Streamlit/React frontend, and support for ML model training, live stock fetching, and context-aware AI interactions.

⸻

 Features

✅ Portfolio Management
	•	Add / sell stocks
	•	Live price updates
	•	Auto-calculated PnL, PnL%, weights
	•	Total portfolio value calculations
	•	Cash balance tracking
	•	Fully persistent state

✅ AI Chatbot (LangChain Agent)
	•	Financial Q&A
	•	Fetch stock prices
	•	Fetch portfolio stats
	•	Explain financial terms
	•	Use backend tools via LangChain agents
	•	Conversational memory

✅ Prediction Engine
	•	REST endpoints for:
	•	Creating ML models
	•	Uploading datasets
	•	Training stocks prediction models
	•	Supports custom NN architectures
	•	Supports checkpointing
	•	Automatic early stopping
	•	Versioned training pipelines

✅ Full Frontend Interface
	•	Portfolio dashboard
	•	AI chatbot UI
	•	Prediction model trainer UI
	•	Clean, responsive cards and metrics
	•	Axios-based API communication

⸻

 Project Structure

stocksage/
│── backend/
│   ├── main.py               # FastAPI entry point
│   ├── routes/               # API endpoints
│   ├── service/              # Portfolio logic, ML services
│   ├── model/                # Models + prediction NN classes
│   ├── utils/                # Helpers, calculations, validation
│   ├── langchain_core/       # Chatbot agent, tools, chains
│   └── data/                 # Datasets, checkpoints
│
│── frontend/
│   ├── main.py               # Streamlit entry
│   ├── pages/                # UI pages (portfolio, chatbot)
│   ├── components/           # Reusable components
│   └── assets/
│
└── README.md


⸻

⚙️ Backend Architecture

🔧 FastAPI Services

The backend exposes multiple REST endpoints:

Portfolio Endpoints

GET  /portfolio/holdings
GET  /portfolio/value
POST /portfolio/add
POST /portfolio/remove

Prediction Endpoints

POST /create_model
POST /upload_dataset
POST /start_training
GET  /training_status

AI Chatbot Endpoint

POST /chatbot/query


⸻

🌐 Frontend Architecture

Streamlit Pages
	•	Portfolio Dashboard
	•	AI Chatbot
	•	Stock Prediction Trainer

Key Frontend Technologies
	•	Streamlit (UI)
	•	React (for isolated components if used)
	•	Axios / fetch API
	•	Recharts / Plotly
	•	State management (session_state)

⸻

🔁 System Data Flow

1️⃣ Portfolio Flow

User Action → Streamlit → FastAPI → Portfolio Model → Yahoo Finance → 
Recalculate Portfolio → Return Updated Values → UI Refresh

2️⃣ Chatbot Flow

User Query → Streamlit → FastAPI → LangChain Agent →
Tool Executor (Portfolio / Stock Price Fetch) →
LLM Response → Streamlit Output

3️⃣ Model Training Flow

User Inputs → Streamlit → FastAPI ML Engine →
Model Creation + Dataset Upload →
Training Loop → Checkpoints Saved →
Training Status Returned to User


⸻

🔮 Key Modules Overview

📊 Portfolio Module

Located in: backend/service/portfolio_service.py
	•	Maintains holdings
	•	Updates stock prices using yFinance
	•	Computes:
	•	Market value
	•	PnL
	•	PnL%
	•	Weight allocation
	•	Ensures consistent calculations for frontend dashboard

⸻

🤖 LangChain Chatbot

Located in: backend/langchain_core/
	•	Custom tools for:
	•	Fetching portfolio value
	•	Fetching stock price
	•	Generating explanations
	•	Agent with:
	•	Memory
	•	Function calling
	•	Tool routing

⸻

🧠 Prediction Engine

Located in: backend/model/

Supports:
	•	Custom neural networks
	•	Multi-layer architectures
	•	Hidden layers
	•	Loss tracking
	•	Early stopping
	•	Checkpoint saving

Endpoints allow uploading datasets and triggering training.

⸻

💻 Installation Guide

1. Clone Repo

git clone https://github.com/nukee7/stocksage.git
cd stocksage


⸻

🖥 Backend Setup (FastAPI)

2. Create Virtual Environment

python3 -m venv stsenv
source stsenv/bin/activate

3. Install Dependencies

pip install -r backend/requirements.txt

4. Run Backend

uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload


⸻

🎨 Frontend Setup (Streamlit/React)

5. Install Frontend Dependencies

If Streamlit:

cd frontend
pip install -r requirements.txt
streamlit run main.py

If React:

cd frontend
npm install
npm start


⸻

 Testing API Endpoints

Example: Create Model

curl -X POST http://localhost:8001/create_model \
-H "Content-Type: application/json" \
-d '{"input_dim":4,"hidden_layers":[8,8],"output_dim":1}'

Example: Upload Dataset

curl -X POST http://localhost:8001/upload_dataset \
-H "Content-Type: application/json" \
-d '[
  [[0.3,0.1,-0.2,-0.4],[1]],
  [[-0.5,0.2,0.1,-0.3],[0]]
]'

Example: Start Training

curl -X POST http://localhost:8001/start_training \
-H "Content-Type: application/json" \
-d '{
  "max_epochs": 20,
  "stop_loss": 0.001,
  "checkpoint_interval": 5,
  "version": "demo1"
}'


⸻

 Dashboard Preview

Your README can optionally include screenshots:
	•	Portfolio Table
	•	P&L KPIs
	•	Chatbot UI
	•	Training Graph

(You can send images and I’ll embed them.)

⸻

 Tech Stack

Frontend
	•	Streamlit
	•	React (optional components)
	•	Plotly / Recharts
	•	Axios

Backend
	•	FastAPI
	•	Pydantic
	•	LangChain
	•	yfinance
	•	Numpy / Pandas
	•	PyTorch / TensorFlow (depending on your model)

⸻

 Future Enhancements
	•	WebSockets for real-time price streaming
	•	User authentication
	•	Multi-portfolio support
	•	Portfolio rebalancing engine
	•	Risk scoring model

⸻

 Conclusion

StockSage demonstrates a complete end-to-end financial intelligence system combining:
✔ API engineering
✔ Machine learning
✔ Real-time data fetching
✔ State management
✔ Agentic AI design
✔ Full-stack architecture