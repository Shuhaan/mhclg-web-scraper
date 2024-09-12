import pandas as pd
import asyncio
import os
from scraper import (
    scrape_download_file,
    get_file_urls,
    download_files,
)
from scanner import count_postcodes, process_pdf, find_category_pages

base_url = "https://national-infrastructure-consenting.planninginspectorate.gov.uk"
file_endpoint = "project-search"


def main():
    # Scrape the project page to get the CSV file containing projects
    print(f"Scraping: {base_url}/{file_endpoint}")
    scrape_download_file(base_url, "projects.csv", endpoint=file_endpoint)

    # Path to your CSV file
    csv_file_path = "data/projects.csv"
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path)

    name_endpoint_dict = {}
    for index, row in df.iterrows():
        project_reference = row["Project reference"]
        project_endpoint = (
            f"projects/{project_reference}/documents?searchTerm=book+of+reference"
        )
        name_endpoint_dict[project_reference] = project_endpoint

    # Gather the links to the Book of References for each project
    project_pdf_link_dict = asyncio.run(get_file_urls(base_url, name_endpoint_dict))

    # Download the Book of References for each project
    asyncio.run(download_files(project_pdf_link_dict))
    num_of_files = len(os.listdir("data/book-of-references"))
    print(f"Number of files downloaded: {num_of_files}")


if __name__ == "__main__":
    main()
