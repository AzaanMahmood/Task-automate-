import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import csv
import psycopg2

def login_to_website(driver, email, password):
    driver.get("https://www.rozee.pk/login")
    username_field = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='_email']")))
    password_field = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='pwd']")))
    username_field.send_keys(email)
    password_field.send_keys(password)
    login_button = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//button[@id='submit_button']")))
    login_button.click()

def search_for_jobs(driver, keyword):
    search_icon = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//ul[@class='nav navbar-nav navbar-link navbar-right']/li[2]")))
    search_icon.click()
    search_bar = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='search']")))
    search_bar.send_keys(keyword)
    search_bar.send_keys(Keys.RETURN)

def extract_job_listings(driver):
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    job_listings = soup.find_all('div', class_='job')
    job_data = []
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
        job_data.append({"Job Title": job_title, "Company Name": company_name, "Job Link": job_link})
    return job_data

def save_to_csv(job_data, file_path):
    field_names = ['Job Title', 'Company Name', 'Job Link']
    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(job_data)

def save_to_postgresql(job_data):
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cur = conn.cursor()
    for job in job_data:
        try:
            # Check if the record already exists in the database
            cur.execute(
                "SELECT 1 FROM rozee_data WHERE job_title = %s AND company_name = %s AND job_link = %s",
                (job['Job Title'], job['Company Name'], job['Job Link'])
            )
            existing_record = cur.fetchone()

            # If the record doesn't exist, insert it into the database
            if not existing_record:
                cur.execute(
                    "INSERT INTO rozee_data (job_title, company_name, job_link) VALUES (%s, %s, %s)",
                    (job['Job Title'], job['Company Name'], job['Job Link'])
                )
                conn.commit()
                print("Inserted data successfully")
            else:
                print("Skipped duplicate data")
        except psycopg2.Error as e:
            print("Error inserting data:", e)
    cur.close()
    conn.close()
