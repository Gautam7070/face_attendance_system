# 📸 IntelliFace: Enterprise Attendance System

A professional, real-time face recognition attendance system featuring **Anti-Spoofing 2.0**, a **Premium Analytics Dashboard**, and **Instant WhatsApp Alerts**. Optimized for high-speed performance and commercial-grade security.

---

## ✨ Features

- **🚀 Async Performance**: Real-time 30FPS webcam feed using background thread AI processing. No UI lag.
- **🛡️ Anti-Spoofing 2.0**: Intelligent liveness detection using 3D relative nose-to-jaw ratios to prevent photo/video spoofing.
- **📈 Premium Dashboard**: Beautiful Streamlit interface with interactive **Plotly** charts (scroll-to-zoom, hover analytics).
- **📲 WhatsApp Alerts**: Real-time "Punch-In/Out" notifications sent via Twilio to your phone.
- **⚡ Burst Registration**: One-click automatic capture of 20 biometric frames for fast and accurate enrollment.
- **🔐 Multi-Interface**: Desktop GUI (CustomTkinter), Admin API (FastAPI), and Web Dashboard.

---

## 🚀 Getting Started

### 1. Installation
```bash
# Create and activate environment
python -m venv env
.\env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. WhatsApp Setup (Optional)
1. Get your **ACCOUNT_SID** and **AUTH_TOKEN** from [Twilio](https://www.twilio.com/).
2. Update `alerts/whatsapp.py` with your credentials and phone number.
3. Test it: `python test_whatsapp.py`

---

## 💻 Running the System

### **The Master Control (Recommended)**
Double-click **`start.bat`** to access the one-click menu:
1. **Desktop GUI**: For daily attendance and enrollment.
2. **Admin API**: To power external integrations.
3. **Web Dashboard**: View analytics and attendance trends.

---

## 🏢 System Components

### 1. Graphical User Interface (GUI)
Run `python gui/app.py` or `run_gui.bat`.
- **Fluid Scanner**: Features high-speed async recognition.
- **Liveness Gate**: Requires a "Blink" or "Head Turn" challenge to record attendance.
- **Auto-Cooldown**: Prevents duplicate entries within 1 hour.

### 2. Admin API (Backend)
Run `uvicorn api.main:app --reload`.
- Fully documented at `http://127.0.0.1:8000/docs`.
- Manage identities and logs via secure REST endpoints.

### 3. Web Dashboard (Analytics)
Run `streamlit run dashboard/dashboard.py`.
- Interactive attendance trends.
- Modern glassmorphism UI.

---

## 📁 Project Structure
- `api/`: FastAPI backend and database logic.
- `gui/`: Premium CustomTkinter desktop application.
- `dashboard/`: Streamlit web visualization.
- `security/`: Advanced Liveness Detection algorithms.
- `alerts/`: Twilio WhatsApp notification service.
- `data/`: Central biometric storage (`encodings.pkl`).
- `attendance/`: Secure attendance logs (`attendance.csv`).

---

## 🛠️ Tech Stack
- **Python 3.10+**
- **FastAPI / Streamlit / CustomTkinter**
- **Face Recognition / MediaPipe / OpenCV**
- **Twilio API (WhatsApp)**
- **Plotly (Interactive Analytics)**

---

## 👤 Author
Developed by **Gautam** 🚀
