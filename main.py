from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import csv
import psycopg2

# Function to find job data from the website
def find_job():
    Jobs = WebDriverWait(driver, 30).until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@class='job ']//div[@class='jobt float-left']//h3[@class='s-18']/a/bdi")))
    total_occurrences = len(
        driver.find_elements(By.XPATH, "//div[@class='job ']//div[@class='jobt float-left']//h3[@class='s-18']/a")) + 1
    for j in range(1, total_occurrences):
        job_title = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, f"(//div[@class='job ']/div[@class='jcont'])[{j}]")))
        job_link = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
            (By.XPATH, f"(//div[@class='job ']//div[@class='jobt float-left']//h3[@class='s-18']/a)[{j}]")))
        job_link = job_link.get_attribute('href')
        job_data.append({"Job": job_title.text, "Link": job_link})

# Function to save data from CSV to PostgreSQL database
def save_csv_to_postgresql():
    # Database connection information
    username_db = 'postgres'
    password_db = '1234'
    hostname_db = 'localhost'
    port_db = '5432'
    database_name_db = 'db'

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        dbname=database_name_db,
        user=username_db,
        password=password_db,
        host=hostname_db,
        port=port_db
    )

    # Create a cursor object
    cur = conn.cursor()

    # Read data from the CSV file and insert into the database
    with open("job_data.csv", "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            job_title = row["Job"]
            job_link = row["Link"]
            try:
                # Check if the link already exists in the database
                cur.execute("SELECT job_link FROM job_data WHERE job_link = %s", (job_link,))
                existing_link = cur.fetchone()

                # If the link doesn't exist, insert the job data into the database
                if not existing_link:
                    cur.execute(
                        "INSERT INTO job_data (job_title, job_link) VALUES (%s, %s)",
                        (job_title, job_link)
                    )
                    conn.commit()
                    print(f"Inserted: {job_title} - {job_link}")
                else:
                    print(f"Skipped duplicate link: {job_link}")
            except Exception as e:
                print(e)

    # Close the cursor and connection
    cur.close()
    conn.close()

# Configure Chrome options
option = Options()
option.add_experimental_option("detach", True)

# Initialize Chrome driver
driver = webdriver.Chrome(options=option)
driver.maximize_window()

# Open the website and login
driver.get("https://www.rozee.pk/login")
username = "shaharmeer01@gmail.com"
password = "80yar11dy"
username_field = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.XPATH, "//input[@id='_email']")))
password_field = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.XPATH, "//input[@id='pwd']")))
username_field.send_keys(username)
password_field.send_keys(password)
login_button = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@id='submit_button']")))
login_button.click()

# Search for jobs
search_icon = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.XPATH, "//ul[@class='nav navbar-nav navbar-link navbar-right']/li[2]")))
search_icon.click()
search_bar = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.XPATH, "//input[@id='search']")))
search_bar.send_keys("Python")
search_bar.send_keys(Keys.RETURN)

# Find and collect job data
job_data = []
pagination = len(driver.find_elements(By.XPATH, "(//ul[@class='pagination radius0 float-right ml20 s-14'])[1]/li"))
find_job()
for i in range(2, pagination + 1):
    if i == 3:
        continue
    next = driver.find_element(By.XPATH,
                               f"((//ul[@class='pagination radius0 float-right ml20 s-14'])[1]/li)[{i}]")
    if next:
        next.click()
        find_job()
    else:
        break

# Save collected job data to a CSV file
with open("job_data.csv", "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["Job", "Link"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in job_data:
        writer.writerow(row)

# Save job data from CSV to PostgreSQL database
save_csv_to_postgresql()

# Close the driver
driver.quit()
