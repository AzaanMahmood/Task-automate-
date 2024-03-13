import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import csv
import psycopg2

load_dotenv()

# Function to save data from CSV to PostgreSQL database without duplicates
def save_csv_to_postgresql():

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

    # Create a cursor object
    cur = conn.cursor()

    # Read data from the CSV file and insert into the database
    with open("job_listings.csv", "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            job_title = row["Job Title"]
            company_name = row["Company Name"]
            job_link = row["Job Link"]
            try:
                # Check if the record already exists in the database
                cur.execute(
                    "SELECT 1 FROM rozee_data WHERE job_title = %s AND company_name = %s AND job_link = %s",
                    (job_title, company_name, job_link)
                )
                existing_record = cur.fetchone()

                # If the record doesn't exist, insert it into the database
                if not existing_record:
                    cur.execute(
                        "INSERT INTO rozee_data (job_title, company_name, job_link) VALUES (%s, %s, %s)",
                        (job_title, company_name, job_link)
                    )
                    conn.commit()
                    print("Inserted data successfully")
                else:
                    print("Skipped duplicate data")
            except Exception as e:
                print(e)

    # Close the cursor and connection
    cur.close()
    conn.close()

# Initialize Chrome driver
option = Options()
option.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=option)
driver.maximize_window()

# Login to the website
driver.get("https://www.rozee.pk/login")
username = os.getenv("ROZEE_EMAIL")
password = os.getenv("ROZEE_PASSWORD")
username_field = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.XPATH, "//input[@id='_email']")))
password_field = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.XPATH, "//input[@id='pwd']")))
username_field.send_keys(username)
password_field.send_keys(password)
login_button = WebDriverWait(driver, 30).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@id='submit_button']")))
login_button.click()

search_icon = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.XPATH, "//ul[@class='nav navbar-nav navbar-link navbar-right']/li[2]")))
search_icon.click()
search_bar = WebDriverWait(driver, 30).until(
    EC.presence_of_element_located((By.XPATH, "//input[@id='search']")))
search_bar.send_keys("Python")
search_bar.send_keys(Keys.RETURN)

try:
    html_content = driver.page_source

    soup = BeautifulSoup(html_content, 'html.parser')

    job_listings = soup.find_all('div', class_='job')

    a = {'Jobs': []}
    for job in job_listings:
        job_title_element = job.find('h3', class_='s-18')
        if job_title_element and job_title_element.a:
            job_title = job_title_element.a.text.strip()
        else:
            continue
        company_div = job.find('div', class_='cname')
        company_name = ' '.join([elem.text.strip() for elem in company_div.find_all('a')]) if company_div else 'N/A'

        job_link_element = job.find('h3', class_='s-18').find('a') if job_title_element else None
        job_link = f"https:{job_link_element['href']}" if job_link_element and 'href' in job_link_element.attrs else 'N/A'

        a['Jobs'].append({
            'Job Title': job_title,
            'Company Name': company_name,
            'Job Link': job_link
        })

        print(f"Job Title: {job_title}")
        print(f"Company Name: {company_name}")
        print(f"Job Link: {job_link}")
        print("-" * 50)

except TimeoutException:
    print("Timeout occurred. Failed to locate login or search elements.")
except Exception as e:
    print(e)
finally:
    driver.quit()

csv_file = 'job_listings.csv'
job_listings = a['Jobs']
field_names = ['Job Title', 'Company Name', 'Job Link']
with open(csv_file, 'w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=field_names)
    writer.writeheader()
    for job in job_listings:
        writer.writerow(job)

# Save job data from CSV to PostgreSQL database
save_csv_to_postgresql()
