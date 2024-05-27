from playwright.sync_api import sync_playwright
import os
import time
from selectolax.parser import HTMLParser
from datetime import datetime
import pandas as pd
from init_db import create_database, is_job_scraped, mark_job_as_scraped
import argparse
import json
from bs4 import BeautifulSoup

SBR_WS_CDP = 'wss://brd-customer-hl_3404cc34-zone-scraping_browser1:1o78du21r9ka@brd.superproxy.io:9222'
# Function to read headers from JSON file
def read_headers_from_json(filename):
    with open(filename, 'r') as file:
        headers = json.load(file)
    return headers

# Example usage
headers = read_headers_from_json('Request_header.json')

def parse_selector(html,selector):
    soup = BeautifulSoup(html, 'html.parser')
    css_elements = soup.select(str(selector))
    return css_elements
def get_data(page, url):
    print("in get data")
    page.goto(url)
    # page.wait_for_load_state("networkidle")
    print(page.content())
    jobs = parse_selector(page.content(), "div.job_seen_beacon")
    next_page_link = parse_selector(page.content(), "a[aria-label='Next Page']")
    # jobs = page.query_selector_all("div.job_seen_beacon")
    # next_page_link = page.query_selector_all("a[aria-label='Next Page']")
    print(jobs)
    print(next_page_link)
    return jobs, next_page_link

# def get_data(page, url):
#     page.goto(url)

    # jobs = html.select("div.job_seen_beacon")
    # next_page_link = html.select("a[aria-label='Next Page']")
    # return jobs, next_page_link

def parse_html(job):

    html = HTMLParser(job)
    print("!!!!!!!!!!!!!!!")
    job_id = html.css("h2 > a")[0].attrs["data-jk"]
    title = html.css("h2 > a")[0].text()
    link = "https://www.indeed.com/viewjob?jk=" + html.css("h2 > a")[0].attrs["data-jk"]
    company_name = html.css("div.css-17fky0v.e37uo190")[0].text().split("\n")[0]
    location = html.css("div.css-17fky0v.e37uo190")[0].text().split("\n")[1]
    job = {
        "job_id": job_id,
        "title": title,
        "link": link,
        "company_name": company_name,
        "location": location
    }
    print(job)
    return job
def convert_to_df(data_list):
    df = pd.DataFrame(data_list)
    return df

def export_to_excel(excel_filename, df):
    if os.path.exists(excel_filename):
        existing_df = pd.read_excel(excel_filename, engine="openpyxl")
        updated_df = pd.concat([existing_df, df], ignore_index=True)
        updated_df.to_excel(excel_filename, index=False, engine="openpyxl")
    else:
        df.to_excel(excel_filename, index=False, engine="openpyxl")

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
    with sync_playwright() as p:
        # browser = p.chromium.connect_over_cdp(SBR_WS_CDP)
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        time_folder_path = create_folder_structure(keyword)
        excel_file_path = os.path.join(time_folder_path, f"00_{keyword}.xlsx")
        base_url = "https://www.indeed.com"
        url = f"{base_url}/jobs?q={keyword.replace(' ', '+')}"
        print(url)
        page_count = 0
        data_list = []

        try:
            while True:

                # time.sleep(1)
                jobs, next_page_link = get_data(page, url)
                for job in jobs:
                    # print(job)
                    parsed_data = parse_html(job)
                    job_id = parsed_data["job_id"]
                    if not is_job_scraped(job_id, keyword):
                        print(parsed_data)
                        data_list.append(parsed_data)
                        try:
                            data = get_desc(page, parsed_data["link"])
                        except Exception as e:
                            print(f"Error retrieving job description: {e}")
                            continue  # Skip to the next iteration of the loop
                        filename = os.path.join(time_folder_path, f"{job_id}.txt")
                        write_to_file(str(parse_html(job)) + "\n", filename)
                        write_to_file(data, filename)
                        mark_job_as_scraped(job_id, parsed_data["title"], parsed_data["link"], keyword)

                page_count += 1
                print("_" * 100)
                print(f"page count {page_count}")
                if not next_page_link or (max_pages and page_count >= max_pages):
                    break

                url = base_url + next_page_link[0].attrs["href"]


        except Exception as e:

            print(f"An error occurred: {e}")
            # Export data collected so far
            if data_list:
                data_frame = convert_to_df(data_list)

                export_to_excel(excel_file_path, data_frame)
            return

        if data_list:
            data_frame = convert_to_df(data_list)
            export_to_excel(excel_file_path, data_frame)

        print(len(data_list))


#
def get_desc(page, url, max_retries=4):
    retries = 0
    while retries < max_retries:
        try:
            time.sleep(2)
            page.goto(url)
            data = parse_selector(page.content(),"div.jobsearch-jobDescriptionText")
            if not data:
                raise Exception("No job description found....")
            return data[0].text
        except Exception as e:
            print(f"Error: {e}. Retrying after {5 ** retries} seconds...")
            time.sleep(5 ** retries)
            retries += 1
    # remove_job_from_db(job_id)

    raise Exception("Max retries exceeded")


def write_to_file(data, filename):
    with open(filename, "a+") as file:
        file.writelines(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape job data from Indeed")
    parser.add_argument("-k", "--keyword", type=str, required=True, help="Keyword for job search")
    parser.add_argument("-p", "--pages", type=int, default=None, help="Number of pages to scrape")
    args = parser.parse_args()
    main(args.keyword, args.pages)