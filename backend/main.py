
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

import os
import mysql.connector
from dotenv import load_dotenv

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from fastapi import WebSocket

clients = []
SCRAPER_STATUS = "Select SRO"

SCRAPER_RUNNING = False
SCRAPER_STOPPED = False

import asyncio

async def broadcast_status(message):
    global SCRAPER_STATUS
    SCRAPER_STATUS = message

    for client in clients:
        await client.send_text(message)
        
        

# scraper function
from scraper import start_scraper


SCRAPER_STATUS = "Idle"

# ---------------------------------------------------
# ENV
# ---------------------------------------------------

load_dotenv()


# ---------------------------------------------------
# FASTAPI
# ---------------------------------------------------



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------
# SELENIUM (START ONCE)
# ---------------------------------------------------

driver = None
wait = None


@app.on_event("startup")
def start_browser():

    global driver, wait

    print("\nStarting Selenium Browser...\n")

    # chrome_options = Options()
    # chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    chrome_options = Options()

    # Run Chrome in background (no popup)
    chrome_options.add_argument("--headless=new")

    # Required for stable headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Prevent automation detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Prevent some crashes
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
        

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    driver.get("https://esearch.delhigovt.nic.in/Complete_search_without_regyear.aspx")

    wait = WebDriverWait(driver, 30)

    wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//select[contains(@id,'ddl_sro')]")
        )
    )

    print("Website opened and SRO dropdown loaded")


# ---------------------------------------------------
# REQUEST MODEL
# ---------------------------------------------------

class ScraperRequest(BaseModel):
    sro_name: str
    locality_name: str


# ---------------------------------------------------
# HOME
# ---------------------------------------------------

@app.get("/")
def home():
    return {"message": "Delhi Property Scraper API Running"}



@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    try:
        while True:
            await websocket.receive_text()  # keep connection alive
    except:
        clients.remove(websocket)


@app.get("/status")
def get_status():
    global SCRAPER_STATUS
    return {"status": SCRAPER_STATUS}


# ---------------------------------------------------
# GET SRO LIST
# ---------------------------------------------------

@app.get("/sro")
def get_sro():

    print("\nGET /sro\n")

    dropdown = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//select[contains(@id,'ddl_sro')]")
        )
    )

    options = dropdown.find_elements(By.TAG_NAME, "option")

    sro_list = []

    print("Available SRO:\n")

    for i, opt in enumerate(options):

        txt = opt.text.strip()

        print(i, txt)

        if txt and "Select" not in txt:
            sro_list.append(txt)

    print("\n----------------------------------\n")

    return sro_list


# ---------------------------------------------------
# GET LOCALITIES
# ---------------------------------------------------

@app.get("/localities")
def get_localities(sro_name: str):

    print("\nSRO selected:", sro_name)

    sro_dropdown = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//select[contains(@id,'ddl_sro')]")
        )
    )

    Select(sro_dropdown).select_by_visible_text(sro_name)

    locality_dropdown = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//select[contains(@id,'ddl_loc')]")
        )
    )

    options = locality_dropdown.find_elements(By.TAG_NAME, "option")

    locality_list = []

    print("\nGET /localities\n")
    print("Available Localities:\n")

    counter = 1

    for opt in options:

        txt = opt.text.strip()

        if txt and "Select" not in txt and "*" not in txt:

            print(counter, "-", txt)

            locality_list.append(txt)

            counter += 1

    print("\n----------------------------------\n")

    return locality_list






# ---------------------------------------------------
# START SCRAPER
# ---------------------------------------------------

@app.post("/start-scraper")
async def start_scraper_api(data: ScraperRequest):

    await broadcast_status("Auto captcha detection start")

    import threading

 
    global SCRAPER_RUNNING
    global SCRAPER_STOPPED

    if SCRAPER_RUNNING:
        return {"status": "Scraper already running"}

    SCRAPER_RUNNING = True
    SCRAPER_STOPPED = False

    def run_scraper():
        global SCRAPER_RUNNING
        try:
            start_scraper(driver, data.sro_name, data.locality_name)
        finally:
            SCRAPER_RUNNING = False

    threading.Thread(target=run_scraper).start()

    return {"status": "Scraper started"}



@app.post("/stop-scraper")
async def stop_scraper():

    global SCRAPER_RUNNING
    global SCRAPER_STOPPED

    SCRAPER_STOPPED = True
    SCRAPER_RUNNING = False

    await broadcast_status("Scraper stopped. You can start a new search.")

    return {"status": "Scraper stopped"}


# ---------------------------------------------------
# CAPTCHA IMAGE
# ---------------------------------------------------

@app.get("/captcha")
def get_captcha():

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    captcha_path = os.path.join(BASE_DIR, "captcha.png")

    if os.path.exists(captcha_path):
        return FileResponse(captcha_path)

    return Response(status_code=204)


# ---------------------------------------------------
# CAPTCHA SUBMIT
# ---------------------------------------------------

@app.post("/submit-captcha")
def submit_captcha(data: dict):

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    captcha_file = os.path.join(BASE_DIR, "captcha_input.txt")

    with open(captcha_file, "w") as f:
        f.write(data["captcha"])

    return {"status": "captcha received"}





def check_scrape_status(sro_name, locality_name):

    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

    cursor = db.cursor()

    cursor.execute("""
        SELECT scrape_status
        FROM property_records
        WHERE sro_name=%s AND locality_name=%s
        ORDER BY id DESC
        LIMIT 1
    """,(sro_name, locality_name))

    row = cursor.fetchone()

    db.close()

    if not row:
        return "NOT_STARTED"

    return row[0]

# ---------------------------------------------------
# FETCH DATABASE RECORDS
# ---------------------------------------------------

@app.get("/records")
def get_records(
    sro_name: str,
    locality_name: str,
    year: str = None,
    month_from: str = None,
    month_to: str = None,
    first_party: str = None,
    second_party: str = None,
    address: str = None,
    pincode: str = None,
    min_area: str = None,
    max_area: str = None,
    property_type: str = None
):

    global SCRAPER_RUNNING
    global SCRAPER_STOPPED

    # Check if data already exists
    status = check_scrape_status(sro_name, locality_name)

    if status == "NOT_STARTED":

        asyncio.run(
            broadcast_status("No data available in DB, starting scraping")
        )

               
        
       

        if not SCRAPER_RUNNING:

            SCRAPER_RUNNING = True
            SCRAPER_STOPPED = False

            def run_scraper():
                global SCRAPER_RUNNING
                
                
                try:
                    start_scraper(driver, sro_name, locality_name)
                finally:
                    SCRAPER_RUNNING = False

            import threading
            threading.Thread(target=run_scraper).start()

        return []

    elif status == "IN_PROGRESS":

        asyncio.run(
            broadcast_status(
                "Scraping previously interrupted. Resuming scraping..."
            )
        )

        if not SCRAPER_RUNNING:

            SCRAPER_RUNNING = True
            SCRAPER_STOPPED = False

            def run_scraper():
                global SCRAPER_RUNNING
                try:
                    start_scraper(driver, sro_name, locality_name)
                finally:
                    SCRAPER_RUNNING = False

            import threading
            threading.Thread(target=run_scraper).start()

    elif status == "COMPLETED":

        asyncio.run(
            broadcast_status(
                "Fetching data of this SRO and locality. Completed data stored in DB"
            )
        )
        


        


    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

    cursor = db.cursor(dictionary=True)

    query = """
    SELECT *
    FROM property_records
    WHERE sro_name=%s
    AND locality_name=%s
    AND reg_no IS NOT NULL
    """

    params = [sro_name, locality_name]

    # YEAR
    if year:
        query += " AND reg_date IS NOT NULL AND YEAR(reg_date)=%s"
        params.append(year)

    # MONTH RANGE FILTER
    # MONTH RANGE FILTER
    if month_from and month_to:
        query += " AND reg_date IS NOT NULL AND MONTH(reg_date) BETWEEN %s AND %s"
        params.append(month_from)
        params.append(month_to)

    elif month_from:
        query += " AND reg_date IS NOT NULL AND MONTH(reg_date) >= %s"
        params.append(month_from)

    elif month_to:
        query += " AND reg_date IS NOT NULL AND MONTH(reg_date) <= %s"
        params.append(month_to)

    # FIRST PARTY
    if first_party and first_party.strip() != "":
        query += " AND first_party LIKE %s"
        params.append("%" + first_party + "%")

    # SECOND PARTY
    if second_party and second_party.strip() != "":
        query += " AND second_party LIKE %s"
        params.append("%" + second_party + "%")

    # ADDRESS
    if address and address.strip() != "":
        query += " AND property_address LIKE %s"
        params.append("%" + address + "%")

    # PINCODE
    if pincode and pincode.strip() != "":
        query += " AND property_address LIKE %s"
        params.append("%" + pincode + "%")

    # AREA
    if min_area and min_area.strip() != "":
        query += " AND area >= %s"
        params.append(float(min_area))

    if max_area and max_area.strip() != "":
        query += " AND area <= %s"
        params.append(float(max_area))

    # PROPERTY TYPE
    if property_type and property_type.strip() != "":
        query += " AND property_type LIKE %s"
        params.append("%" + property_type + "%")

    query += " ORDER BY reg_date DESC, id DESC"

    cursor.execute(query, params)

    rows = cursor.fetchall()

    db.close()

    return rows 




