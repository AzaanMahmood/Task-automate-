import os
from dotenv import load_dotenv
from selenium import webdriver
from job_search import login_to_website, search_for_jobs, extract_job_listings, save_to_csv, save_to_postgresql

load_dotenv()


def main():
    option = webdriver.ChromeOptions()
    option.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=option)
    driver.maximize_window()

    try:
        login_to_website(driver, os.getenv("ROZEE_EMAIL"), os.getenv("ROZEE_PASSWORD"))
        search_for_jobs(driver, "Python")
        job_data = extract_job_listings(driver)
        save_to_csv(job_data, "job_listings.csv")
        save_to_postgresql(job_data)
    except Exception as e:
        print("An error occurred:", e)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
