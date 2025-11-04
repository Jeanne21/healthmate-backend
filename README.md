# 🩺 HealthMate Backend

The **HealthMate Backend** is built with **FastAPI** and serves as the backbone of the HealthMate MVP — an AI-powered mobile health assistant designed to improve access to healthcare management in rural areas.  
It enables users to track medications, appointments, and health measurements such as blood pressure and blood sugar, while providing reminders and health insights.

---

## 🚀 Features

- 🔐 **Authentication** – Signup, Login, and Session management
- 💊 **Medication Management** – Add, edit, and track medications and refill reminders
- 📅 **Appointment Management** – Schedule and receive reminders for appointments
- 💬 **AI Insights** – Process health data and generate meaningful insights
- 📸 **OCR Support** – Extract readings from images of measurement machines
- ☁️ **Firestore Integration** – Real-time database for scalable data storage
- 🧠 **Modular Architecture** – Clean separation of routers, models, and utilities
- 🧩 **CORS Configured** – Ready for connection with Flutter frontend

---

## 🧠 Tech Stack

| Component        | Technology                          |
| ---------------- | ----------------------------------- |
| **Framework**    | FastAPI                             |
| **Database**     | Firebase Firestore                  |
| **Server**       | Uvicorn                             |
| **Language**     | Python 3.12                         |
| **Hosting**      | Render                              |
| **AI Utilities** | (Planned) OCR and predictive models |

---

## 📂 Project Structure

```
HealthMate-backend/
├── app/
│   ├── main.py                # Entry point
│   ├── routers/               # API route definitions
│   ├── models/                # Pydantic models
│   ├── utils/                 # Helper and processing utilities
│   └── firebase_client.py     # Firestore client setup
├── requirements.txt           # Project dependencies
├── Procfile                   # Render startup command
├── .gitignore
└── README.md

```

> 📝 **Note:** Machine learning scripts and training data are excluded from this deployment version.


---

## ⚙️ Local Development Setup

Follow these steps to run the project locally.

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Jeanne21/HealthMate-backend.git
cd HealthMate-backend
```

### 2️⃣ Create and activate a virtual environment
```bash
python -m venv venv
venv\Scripts\activate     # On Windows
# OR
source venv/bin/activate  # On Mac/Linux
``` 

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Run the app
```bash
uvicorn app.main:app --reload
```

### 5️⃣ Access the API documentation

👉 http://127.0.0.1:8000/docs


## ☁️ Deployment on Render

1. Push your code to **GitHub**.
2. Go to [https://render.com](https://render.com) and log in with your GitHub account.
3. Click **“New +” → “Web Service”**.
4. Connect your repository and use the following settings:

| **Setting** | **Value** |
|--------------|-----------|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Environment** | Python 3.12 |

5. Click **Deploy**.

Once deployed, visit your documentation at:<br>
👉 **[https://healthmate-backend.onrender.com/docs](https://healthmate-backend.onrender.com/docs)**

---

### 🔧 Environment Variables

Make sure to set the following environment variables (locally or on Render):

| **Variable** | **Description** |
|---------------|----------------|
| `FIREBASE_PROJECT_ID` | Your Firebase project ID |
| `FIREBASE_PRIVATE_KEY` | Your Firebase service account private key |
| `FIREBASE_CLIENT_EMAIL` | Firebase client email |
| `FIREBASE_DATABASE_URL` | Firestore database URL |

> 💡 These can be stored in a `.env` file locally (never commit it to GitHub).

---

### 🔒 CORS Configuration

CORS is configured to support both local development and mobile testing environments:

```python
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:19006",  # React Native Expo default
    "*"  # For development purposes - restrict in production
]
````

Later, replace `"*"` with your live frontend domain for better security.

---

### 🧩 Next Steps

* Integrate Flutter frontend with the live backend API
* Connect OCR and predictive AI modules
* Add automated deployment workflows and monitoring

---

### 🧑‍💻 Author

**Jeanne Wanjiru**
👩🏽‍💻 Software Developer | Founder of HealthMate MVP
🌍 Based in Kenya

---

### 📜 License

This project is licensed under the **MIT License**.
Feel free to use, modify, and share with attribution.

> *“Empowering rural healthcare through technology and intelligent assistance.” 💙*

---

