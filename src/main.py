from scraper import scrape_project_csv, get_project_pdf_links
import pandas as pd
import asyncio


def main():
    # Scrape the project page to get the CSV file containing projects
    projects_url = "https://national-infrastructure-consenting.planninginspectorate.gov.uk/project-search"

    print(f"Scraping: {projects_url}")
    scrape_project_csv(projects_url)

    # Path to your CSV file
    csv_file_path = "data/projects.csv"

    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path)

    asyncio.run(get_project_pdf_links(df))


if __name__ == "__main__":
    main()
