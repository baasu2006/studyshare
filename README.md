# 📚 StudyShare

A full-stack web application where students can upload, share, and discover academic notes — with AI-powered explanations and YouTube resource suggestions for any topic.

---

## ✨ Features

- 🔐 **Authentication** — Email/password signup & login + Google OAuth 2.0
- 📤 **Upload Notes** — Share PDF, Word, and PowerPoint files with your class
- 📌 **Pin Notes** — Highlight important resources at the top of the feed
- 🔗 **Public Share Links** — Admin can generate shareable links accessible without login
- 🤖 **AI Explain** — Click any note to get an instant AI explanation (Summary, Key Concepts, Real-World Example) powered by Groq (Llama 3.1)
- 🎥 **YouTube Suggestions** — Get recommended video links alongside every AI explanation
- 🔍 **Instant Search** — Filter notes by title in real time
- 🗂️ **Subject Categories** — Organise notes by Mathematics, Networking, Physics, CS, and more
- 👑 **Admin Dashboard** — View all users, all notes, and a full login activity log (including Google sign-ins)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| Frontend | HTML, CSS, Vanilla JS |
| AI | Groq API (Llama 3.1 8B) |
| Video | YouTube Data API v3 |
| Auth | Flask Sessions + Google OAuth 2.0 |
| Storage | Local filesystem (upgradeable to MySQL/Oracle) |

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/studyshare.git
cd studyshare
```

### 2. Install dependencies
```bash
pip install flask werkzeug requests
```

### 3. Configure API keys

Open `app.py` and fill in the following at the top:

```python
GOOGLE_CLIENT_ID     = "your-google-client-id"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"
ANTHROPIC_API_KEY    = "gsk_your_groq_key"      # from console.groq.com (free)
YOUTUBE_API_KEY      = "your-youtube-api-key"   # from console.cloud.google.com
```

### 4. Run the app
```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000**

---

## 🔑 Default Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@studyshare.com | admin2026 |
| Student | student@test.com | password123 |

> ⚠️ Change these before deploying to production.

---

## 📁 Project Structure

```
studyshare/
├── app.py                  # Flask backend — routes, auth, AI logic
├── requirements.txt
├── uploads/                # Uploaded note files (auto-created)
├── templates/
│   ├── index.html          # Main dashboard
│   ├── login.html          # Login page
│   ├── signup.html         # Signup page
│   ├── admin.html          # Admin panel
│   └── share.html          # Public share link page
└── static/
    ├── style.css           # All styles
    └── script.js           # Search, AI modal, filter logic
```

---

## 🔗 Getting Free API Keys

| Key | Where to get | Cost |
|-----|-------------|------|
| Groq (AI) | [console.groq.com](https://console.groq.com) | Free, no card |
| Google OAuth | [console.cloud.google.com](https://console.cloud.google.com) → Credentials | Free |
| YouTube Data API | [console.cloud.google.com](https://console.cloud.google.com) → YouTube Data API v3 | Free (10,000 req/day) |

---

## 📸 Pages

| Page | Route |
|------|-------|
| Dashboard | `/` |
| Login | `/login` |
| Signup | `/signup` |
| Admin Panel | `/admin` |
| Public Note | `/share/<id>` |
| Test Groq Key | `/api/test-groq` |

---

## 🔮 Planned Improvements

- [ ] MySQL / PostgreSQL database integration
- [ ] Note previews in browser (PDF viewer)
- [ ] Comment and rating system per note
- [ ] Email notifications for new uploads
- [ ] Dark mode

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

> Built with ❤️ for students, by students.
