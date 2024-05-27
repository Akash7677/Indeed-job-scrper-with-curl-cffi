
# Indeed-job-scrper-with-curl-cffi
A Indeed Job scraper using curl-cffi
=======
# Indeed Job Scraper

This project is an Indeed Job Scraper that allows you to search for jobs based on keywords and scrape the relevant data, including job title, company name, location, and description. The scraped data is then saved to an Excel file and a text file for easy access and analysis.

## Features

* Search for jobs on Indeed using keywords
* Scrape job data, including title, company name, location, and description
* Save scraped data to an Excel file and a text file
* Automatically skip scraped jobs and mark them as scraped in a database
* Automatic creation of a folder structure for storing the scraped data
* Retry mechanism with exponential backoff for handling requests errors

## Requirements

* Python 3.x
* pandas
* requests
* BeautifulSoup
* logging
* argparse
* curl-cffi

## Usage

To use the Indeed Job Scraper, simply run the `main.py` script with the following command-line arguments:

* `-k`, `--keyword`: The keyword to search for jobs on Indeed (required)
* `-p`, `--pages`: The number of pages to scrape (optional, default is None)

For example, to search for Python developer jobs and scrape the first 5 pages of results, you would run the following command:

```
python main.py -k "python developer" -p 5
```

The scraped data will be saved to an Excel file and a text file in a folder structure based on the current date and time.

## How it works

The Indeed Job Scraper uses the requests library to send HTTP requests to Indeed and the BeautifulSoup library to parse the HTML content of the response. The `get_data` function is responsible for sending the requests and handling any errors or retries. The `parse_html` function is responsible for extracting the relevant job data from the HTML content.

The scraped data is then saved to an Excel file using the pandas library and a text file using the built-in `write_to_file` function. The `create_folder_structure` function is responsible for creating a folder structure based on the current date and time.

The `is_job_scraped` and `mark_job_as_scraped` functions are responsible for skipping scraped jobs and marking them as scraped in a SQLite database using the `init_db.py` script.

The `read_headers_from_json` function is responsible for reading the custom headers from a JSON file, and the `impersonate` parameter in the `requests.Session` function is responsible for using a random browser option from the `browser_opt` list for improved scraping success.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
