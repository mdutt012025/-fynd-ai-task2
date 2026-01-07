Two-Dashboard AI Feedback System
A production-ready web application with User and Admin dashboards for collecting and analyzing customer reviews using AI.
🎯 Features
User Dashboard

⭐ Submit reviews with 1-5 star ratings
💬 Get instant AI-generated responses
🎨 Beautiful, responsive UI
✅ Real-time validation and feedback
📱 Mobile-friendly design

Admin Dashboard

📊 Real-time statistics and metrics
📝 Live-updating list of all submissions
🤖 AI-generated summaries for each review
💡 Recommended business actions
🏷️ Filter by star rating
⏰ Auto-refreshing every 5 seconds

🏗️ Architecture
Task 2 System
├── Backend (FastAPI + Supabase)
│   ├── Review submission handling
│   ├── LLM integration (Gemini API)
│   ├── Database persistence
│   └── API endpoints
├── User Frontend (React + Vite)
│   ├── Review submission form
│   ├── AI response display
│   └── Success/error states
└── Admin Frontend (React + Vite)
    ├── Dashboard with stats
    ├── Filterable review list
    └── Real-time data refresh

    📋 Project Structure
fynd-ai-task2/
├── backend/
│   ├── src/
│   │   └── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── Procfile
│   └── vercel.json
├── frontend-user/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
├── frontend-admin/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
└── README.md
