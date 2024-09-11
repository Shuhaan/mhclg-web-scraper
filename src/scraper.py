import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import os


base_url = "https://national-infrastructure-consenting.planninginspectorate.gov.uk"


def scrape_download_file(base_url, file_name, endpoint="", directory="data"):
    """Scrape project CSV file from the given URL."""

    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        url = (
            f"{base_url}/{endpoint}"
            if endpoint and isinstance(endpoint, str)
            else base_url
        )
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
                href=lambda href: href,
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
                    with open(f"{directory}/{file_name}", "wb") as file:
                        file.write(file_response.content)
                    print(
                        f"{file_name} downloaded successfully and saved in directory: {directory}"
                    )
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


async def get_file_urls(base_url, name_url_dict, directory="data"):
    """Extract PDF links from the project pages and save to JSON asynchronously."""

    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_url_dict = {}

    async with aiohttp.ClientSession() as session:
        tasks = []
        for name, endpoint in name_url_dict.items():
            url = f"{base_url}/{endpoint}"
            tasks.append(process_file_page(session, name, url, file_url_dict))

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

    # Return dictionary containing the project names and their respective "Book of Reference" link
    return file_url_dict


async def process_file_page(session, name, url, file_url_dict):
    """Process each file page to extract the file link."""
    try:
        # Fetch the page content
        html_content = await fetch_page(session, url)

        if html_content:
            # Parse the page content using BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            # Attempt to find the file link with both conditions
            url_tag = soup.find(
                "a",
                href=lambda href: href
                and "Book of Reference" in href
                and "Clean" in href,
            ) or soup.find("a", href=lambda href: href and "Book of Reference" in href)

            # Process the found link if any
            if url_tag:
                # Normalise the URL by replacing spaces with "%20"
                file_url = url_tag.get("href").replace(" ", "%20")
                file_url_dict[name] = file_url
                print(f"File found for {name}")
            else:
                print(f"No file found for {name}")

    except Exception as e:
        print(f"Error occurred while processing {url}: {e}")


async def download_files(name_url_dict, directory="data/book-of-references"):
    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for name, url in name_url_dict.items():
            tasks.append(download_file(session, name, url, directory))

        await asyncio.gather(*tasks)  # Run all download tasks concurrently


async def download_file(session, name, link, directory="data/book-of-references"):
    """Download a single file asynchronously."""
    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                # Check for request errors
                response.raise_for_status()

                # Determine file extension
                content_type = response.headers.get("Content-Type", "")
                if "docx" in content_type or link.endswith(".docx"):
                    extension = "docx"
                else:
                    # Default to pdf if type is unknown
                    extension = "pdf"

                # Normalise file name
                file_name = name.lower().replace("/", " or ").replace(" ", "-")
                file_path = os.path.join(directory, f"{file_name}.{extension}")

                # Write the content to file
                with open(file_path, "wb") as f:
                    f.write(await response.read())

                print(
                    f"Successfully downloaded {name} file as {extension} in directory: {directory}"
                )
    except aiohttp.ClientError as e:
        print(f"Failed to download {name} from {link}: {e}")
    except Exception as e:
        print(f"An error occurred with {name}: {e}")
