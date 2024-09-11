import pytest
import asyncio
import aiohttp
import pandas as pd
from unittest.mock import patch, AsyncMock
from scraper import get_project_pdf_links, process_project, fetch_page  # Replace with your actual module name

# Mock data for the test
mock_df = pd.DataFrame({
    "Project reference": ["project1", "project2"],
    "Project name": ["Project Name 1", "Project Name 2"]
})

@pytest.mark.asyncio
async def test_fetch_page():
    url = "https://example.com"
    html_content = "<html><a href='/book_of_reference.pdf'>Book of Reference</a></html>"

    # Mock aiohttp.ClientSession.get to return the test HTML content
    async with aiohttp.ClientSession() as session:
        mock_get = AsyncMock()
        mock_get.__aenter__.return_value.status = 200
        mock_get.__aenter__.return_value.text.return_value = html_content
        mock_get.__aenter__.return_value.raise_for_status = AsyncMock()  # Fix for raise_for_status warning

        with patch("aiohttp.ClientSession.get", return_value=mock_get):
            response = await fetch_page(session, url)
            assert response == html_content

@pytest.mark.skip
async def test_process_project():
    project_name = "Project Name 1"
    project_url = "https://example.com/project1/documents"
    json_data = {}

    html_content = "<html><a href='/book_of_reference_clean.pdf'>Book of Reference Clean</a></html>"

    async with aiohttp.ClientSession() as session:
        # Mock fetch_page to return a predefined HTML page content
        with patch("scraper.fetch_page", return_value=html_content):
            await process_project(session, project_name, project_url, json_data)

    # Check if the correct link is added to the json_data
    assert project_name in json_data
    assert json_data[project_name] == "/book_of_reference_clean.pdf".replace(" ", "%20")

@pytest.mark.skip
async def test_get_project_pdf_links(tmpdir):
    """Test the full async process of getting PDF links."""
    json_file_path = tmpdir.join("projects.json")
    
    html_content = "<html><a href='/book_of_reference_clean.pdf'>Book of Reference Clean</a></html>"

    # Mock aiohttp.ClientSession.get to return the HTML with a valid PDF link
    mock_get = AsyncMock()
    mock_get.__aenter__.return_value.status = 200
    mock_get.__aenter__.return_value.text.return_value = html_content
    mock_get.__aenter__.return_value.raise_for_status = AsyncMock()  # Fix for raise_for_status warning

    with patch("aiohttp.ClientSession.get", return_value=mock_get):
        # Run the asynchronous function
        await get_project_pdf_links(mock_df, file_path=json_file_path)

    # Check if the file was created and contains the correct data
    with open(json_file_path, "r", encoding="utf-8") as f:
        json_content = f.read()

    assert '"Project Name 1": "/book_of_reference_clean.pdf"' in json_content
    assert '"Project Name 2": "/book_of_reference_clean.pdf"' in json_content