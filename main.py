import os
import random
import time
from datetime import datetime
import pandas as pd
from init_db import create_database, is_job_scraped, mark_job_as_scraped
import argparse
import logging
from bs4 import BeautifulSoup
from curl_cffi import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


browser_opt = ["chrome104","chrome107","chrome110","chrome116","chrome119","chrome120","safari15_3","safari15_5","safari17_0"]
def parse_selector(html,selector):
    soup = BeautifulSoup(html, 'html.parser')
    css_elements = soup.select(str(selector))
    return css_elements
def get_data(session, url, max_retries=4):
    retries = 0
    while retries < max_retries:
        time.sleep(1)
        try:
            r = session.get(url, impersonate=random.choice(browser_opt), timeout=10)
            log_http_error(r, url, retries, page="Landing_page")
            logger.info(f"Landing page URL status code: {r}")
            print(r.text)
            r.raise_for_status()

            # jobs = r.content.find("div.job_seen_beacon")
            jobs = parse_selector(r.content, "div.job_seen_beacon")
            next_page_link = parse_selector(r.content, "a[aria-label='Next Page']")
            if not jobs:
                raise Exception("No job data found....")
            return jobs, next_page_link
        except Exception as e:
            logger.error(f"Error: {e}. Retrying after {5 ** retries} seconds... for {url}")
            time.sleep(5 ** retries)
            retries += 1
    raise Exception("Max retries exceeded")

def parse_html(html):

    job = {
        "job_id": html.select("h2 > a")[0].attrs["data-jk"],
        "title": html.select("h2 > a")[0].text,
        "link": "https://www.indeed.com/viewjob?jk="
                + html.select("h2 > a")[0].attrs["data-jk"],
        "company_name": html.select("span.css-92r8pb.eu4oa1w0")[0].text,
        "location": html.select("div.css-1p0sjhy.eu4oa1w0")[0].text
    }
    # print("No error")
    return job


def convert_to_df(data_list):
    df = pd.DataFrame(data_list)
    return df

def export_to_excel(excel_filename, df):
    if os.path.exists(excel_filename):
        # Append to existing Excel file
        existing_df = pd.read_excel(excel_filename, engine="openpyxl")
        updated_df = pd.concat([existing_df, df], ignore_index=True)
        updated_df.to_excel(excel_filename, index=False, engine="openpyxl")
        # print(f'Data saved to {excel_filename}')
    else:
        # Create a new Excel file
        df.to_excel(excel_filename, index=False, engine="openpyxl")
        # print(f'Excel file created at {os.path.abspath(excel_filename)}')


def create_folder_structure(keyword):
    now = datetime.now()
    date_folder = now.strftime("%Y%m%d")
    time_folder = now.strftime("%H_%M_%S")

    output_folder = "Output"
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    keyword_folder = os.path.join(output_folder, keyword.replace(" ", "_"))
    date_folder_path = os.path.join(keyword_folder, date_folder)
    time_folder_path = os.path.join(date_folder_path, time_folder)

    for folder_path in [keyword_folder, date_folder_path, time_folder_path]:
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

    return time_folder_path

def main(keyword, max_pages=None):
    create_database()
    session = requests.Session(impersonate=random.choice(browser_opt))
    time_folder_path = create_folder_structure(keyword)
    excel_file_path = os.path.join(time_folder_path, f"00_{keyword}.xlsx")
    base_url = "https://www.indeed.com"
    url = f"{base_url}/jobs?q={keyword.replace(' ', '+')}"
    logger.info(url)
    page_count = 0
    data_list = []

    try:
        while True:
            t1 = time.time()
            # time.sleep(1)
            jobs, next_page_link = get_data(session, url)
            for job in jobs:
                # print(job)
                parsed_data = parse_html(job)
                job_id = parsed_data["job_id"]
                if not is_job_scraped(job_id, keyword):
                    logger.info(parsed_data)
                    data_list.append(parsed_data)
                    try:
                        data = get_desc(session, parsed_data["link"])
                    except Exception as e:
                        logger.error(f"Error retrieving job description: {e}")
                        continue  # Skip to the next iteration of the loop
                    filename = os.path.join(time_folder_path, f"{job_id}.txt")
                    write_to_file(str(parse_html(job)) + "\n", filename)
                    write_to_file(data, filename)
                    mark_job_as_scraped(job_id, parsed_data["title"], parsed_data["link"], keyword)
            t2 = time.time()
            print(calculate_time(t1, t2))
            page_count += 1
            logger.info("_" * 100)
            logger.info(f"page count {page_count}")
            if not next_page_link or (max_pages and page_count >= max_pages):
                break

            url = base_url + next_page_link[0].attrs["href"]


    except Exception as e:

        logger.error(f"An error occurred: {e}")
        # Export data collected so far
        if data_list:
            data_frame = convert_to_df(data_list)

            export_to_excel(excel_file_path, data_frame)
        return

    if data_list:
        data_frame = convert_to_df(data_list)
        export_to_excel(excel_file_path, data_frame)

    logger.info(f"len of data list: {len(data_list)}")

def calculate_time(t1,t2):
    return t2-t1
def get_desc(session, url, max_retries=4):
    retries = 0
    while retries < max_retries:
        t1 = time.time()
        try:
            time.sleep(2)
            r = session.get(url,impersonate=random.choice(browser_opt))
            log_http_error(r, url, retries, page="JOB_URL")
            logger.info(f"Job URL status code: {r}")
            r.raise_for_status()
            data = parse_selector(r.content,"div.jobsearch-jobDescriptionText")
            if not data:
                raise Exception("No job description found....")
            t2 = time.time()
            print(calculate_time(t1,t2))
            return data[0].text
        except Exception as e:
            logger.error(f"Error: {e}. Retrying after {5 ** retries} seconds... For {url}")
            time.sleep(5 ** retries)
            retries += 1
    # remove_job_from_db(job_id)

    raise Exception("Max retries exceeded")

def log_http_error(r, url, retry, page):
    if r.status_code == 403:
        with open(f"403_log_{page}.txt", "a+") as f:
            logger.info("Logging HTTP error")
            f.write(f"url: {url} -> 403 -> retry: {retry}\n")
def write_to_file(data, filename):
    with open(filename, "a+") as file:
        file.writelines(data)


if __name__ == "__main__":
    # For Testing -----------------------------------------------------------------
    # keywords = ["Electrical engineer",'python developer', 'automation engineer', 'embedded developer', "QA engineer", "Android developer"]
    # for key in keywords:
    #     try:
    #         main(keyword=key)
    #     except:
    #         continue
    # For Testing -----------------------------------------------------------------

    parser = argparse.ArgumentParser(description="Scrape job data from Indeed")
    parser.add_argument("-k", "--keyword", type=str, required=True, help="Keyword for job search")
    parser.add_argument("-p", "--pages", type=int, default=None, help="Number of pages to scrape")
    args = parser.parse_args()
    main(args.keyword, args.pages)