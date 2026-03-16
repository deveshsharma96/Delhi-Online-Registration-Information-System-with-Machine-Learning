
# Delhi Property Scraper

A full-stack web application that automatically scrapes **Delhi property registration records** from the Delhi Government website and stores them in a **MySQL database**.

The system uses **FastAPI + Selenium + EasyOCR + React** to automate scraping and display results through a web interface.

---

# Features

• Automatic scraping of Delhi property records
• OCR based captcha solving using EasyOCR
• Manual captcha entry if OCR fails
• Data stored in MySQL database
• Resume scraping if backend stops
• WebSocket live scraper status updates
• React UI with filters for searching records

---

# Tech Stack

## Backend

* FastAPI
* Selenium
* EasyOCR
* MySQL
* OpenCV
* NumPy

## Frontend

* React
* Axios

---

# System Requirements

Before running the project install:

• Python **3.10+**
• Node.js **18+**
• MySQL Server
• Google Chrome

Check installation:

```bash
python --version
node -v
npm -v
```

---

# Project Structure

```
project/

backend/
│
├── main.py
├── scraper.py
├── requirements.txt
├── .env.example
└── captcha.png

frontend/
│
├── src/
│   ├── App.js
│   ├── App.css
│
├── package.json
```

---

# 1. Clone Project

```
git clone <repo-url>
cd project
```

---

# 2. Backend Setup

Go to backend folder:

```
cd backend
```

Install Python dependencies:

```
pip install -r requirements.txt
```

---

# 3. Environment Variables

Copy example file:

```
cp .env.example .env
```

Edit `.env` file:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=delhi_property
```

---

# 4. Database Setup

Create MySQL database:

```
CREATE DATABASE delhi_property;
```

Create table:

```
CREATE TABLE property_records (
id INT AUTO_INCREMENT PRIMARY KEY,

reg_no VARCHAR(50),
reg_date DATE,

first_party TEXT,
second_party TEXT,

property_address TEXT,

area VARCHAR(100),

deed_type VARCHAR(255),
property_type VARCHAR(255),

sro_name VARCHAR(255),
locality_name VARCHAR(255),

scrape_status VARCHAR(50)
);
```

---

# 5. Run Backend Server

Start FastAPI server:

```
uvicorn main:app --reload
```

---

# 6. Frontend Setup

Open new terminal and go to frontend folder:

```
cd frontend
```

Install dependencies:

```
npm install
```

Install axios if needed:

```
npm install axios
```

Start React application:

```
npm start
```

Frontend will run at:

```
http://localhost:3000
```

---

# 7. How to Use

1. Open the frontend UI
2. Select **SRO**
3. Select **Locality**
4. Click **Fetch Records**

If records are not present in the database, the scraper will automatically start.

---

# API Endpoints

| Endpoint          | Description            |
| ----------------- | ---------------------- |
| `/sro`            | Get list of SRO        |
| `/localities`     | Get list of localities |
| `/records`        | Fetch records          |
| `/start-scraper`  | Start scraper          |
| `/stop-scraper`   | Stop scraper           |
| `/captcha`        | Get captcha image      |
| `/submit-captcha` | Submit captcha         |

---

# Notes

• Chrome browser must be installed for Selenium to work.
• ChromeDriver is automatically installed using `webdriver-manager`.
• Do not upload `.env` to GitHub.

---

# Author
Devesh Sharma
=======
# Yuktic_DORIS
Delhi Property Scraper using FastAPI, Selenium, EasyOCR, React

