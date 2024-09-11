import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import os


# Create the directory if it doesn't exist
if not os.path.exists("data"):
    os.makedirs("data")

base_url = "https://national-infrastructure-consenting.planninginspectorate.gov.uk"


def scrape_project_csv(url, file_path="data/projects.csv"):
    """Scrape project CSV file from the given URL."""
    try:
        # Fetch the HTML content of the page
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the page content using BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the <a> tag with the download link
            download_link = soup.find(
                "a",
                download=True,
                href=lambda href: href and "/api/applications-download" in href,
            )

            if download_link:
                # Extract the href value (relative URL)
                file_url = download_link.get("href")
                # Construct the full URL
                full_file_url = base_url + file_url
                # Download the file
                file_response = requests.get(full_file_url)

                # Save the file locally
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

    except Exception as e:
        print(f"Error occurred while processing {url}: {e}")


async def fetch_page(session, url):
    """Fetch the HTML content of a page asynchronously."""
    try:
        async with session.get(url) as response:
            response.raise_for_status()  # Raise an error for bad responses
            return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


async def get_project_pdf_links(df, file_path="data/projects.json"):
    """Extract PDF links from the project pages and save to JSON asynchronously."""
    json_data = {}

    async with aiohttp.ClientSession() as session:
        tasks = []
        for index, row in df.iterrows():
            project_reference = row["Project reference"]
            project_name = row["Project name"]
            project_url = f"{base_url}/projects/{project_reference}/documents?searchTerm=book+of+reference"

            tasks.append(process_project(session, project_name, project_url, json_data))

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

    # Save the extracted PDF links to a JSON file
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)
        print(f"Data has been written to {file_path}")


async def process_project(session, project_name, project_url, json_data):
    """Process each project page to extract the PDF link."""
    try:
        # Fetch the page content
        html_content = await fetch_page(session, project_url)

        if html_content:
            # Parse the page content using BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            # Attempt to find the PDF link with both conditions
            pdf_link = soup.find(
                "a",
                href=lambda href: href
                and "Book of Reference" in href
                and "Clean" in href,
            ) or soup.find("a", href=lambda href: href and "Book of Reference" in href)

            # Process the found link if any
            if pdf_link:
                # Normalise the URL by replacing spaces with "%20"
                file_url = pdf_link.get("href").replace(" ", "%20")
                json_data[project_name] = file_url
                print(f"PDF link found for {project_name}")
            else:
                print(f"No PDF link found for {project_name}")

    except Exception as e:
        print(f"Error occurred while processing {project_url}: {e}")
