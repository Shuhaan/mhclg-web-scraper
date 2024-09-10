import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

base_url = "https://national-infrastructure-consenting.planninginspectorate.gov.uk"


def scrape_project_csv(url, file_path="data/projects.csv"):
    """Scrape blog links from a given page."""
    try:
        # Step 1: Fetch the HTML content of the page
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Step 2: Parse the page content using BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            # Step 3: Find the <a> tag with the download link
            download_link = soup.find(
                "a",
                download=True,
                href=lambda href: href and "/api/applications-download" in href,
            )

            if download_link:
                # Extract the href value (relative URL)
                file_url = download_link.get("href")

                # Step 4: Construct the full URL
                full_file_url = base_url + file_url

                # Step 5: Download the file
                file_response = requests.get(full_file_url)

                # Step 6: Save the file locally
                if file_response.status_code == 200:
                    with open(file_path, "wb") as file:
                        file.write(file_response.content)
                    print(f"File downloaded successfully and saved as {file_path}")
                else:
                    print(
                        f"Failed to download the file. Status code: {file_response.status_code}"
                    )
            else:
                print("Download link not found.")
        else:
            print(
                f"Failed to retrieve the webpage. Status code: {response.status_code}"
            )

        return

    except Exception as e:
        print(f"Error occurred while processing {url}: {e}")
        return None


if __name__ == "__main__":
    # Scrape the project page to get csv file containing projects
    projects_url = f"{base_url}/project-search"

    print(f"Scraping: {projects_url}")
    scrape_project_csv(projects_url)

    # Path to your CSV file
    csv_file_path = "data/projects.csv"

    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path)


