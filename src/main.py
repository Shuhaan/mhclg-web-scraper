from scraper import (
    scrape_project_csv,
    get_project_pdf_links,
    download_book_of_references,
)
import pandas as pd
import asyncio
import os


def main():
    # Scrape the project page to get the CSV file containing projects
    projects_url = "https://national-infrastructure-consenting.planninginspectorate.gov.uk/project-search"

    print(f"Scraping: {projects_url}")
    scrape_project_csv(projects_url)

    # Path to your CSV file
    csv_file_path = "data/projects.csv"

    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path)

    # Gather the links to the Book of References for each project
    project_pdf_link_dict = asyncio.run(get_project_pdf_links(df))

    # Download the Book of References for each project
    asyncio.run(download_book_of_references(project_pdf_link_dict))
    num_of_files = len(os.listdir("data/book-of-references"))
    print(f"Number of files downloaded: {num_of_files}")


if __name__ == "__main__":
    main()
