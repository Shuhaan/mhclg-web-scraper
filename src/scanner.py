import asyncio
import fitz
import os
import re
import json
import pandas as pd
import numpy as np


def count_unique_postcodes(text):
    # UK postcode regex pattern
    postcode_pattern = re.compile(
        r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b|\bGIR\s?0AA\b", re.IGNORECASE
    )
    # Find all postcodes in the text
    postcodes = postcode_pattern.findall(text)

    # Convert to a set to remove duplicates and count unique postcodes
    unique_postcodes = set(postcodes)

    return len(unique_postcodes)


async def process_pdf(file_path, include_patterns, exclude_patterns):
    # Get the base name of the file
    file_name_with_extension = os.path.basename(file_path)
    # Remove the extension from the file name
    file_name, _ = os.path.splitext(file_name_with_extension)

    project_data = {file_name: {"Category 3 claimants": 0, "Document data": np.nan}}

    try:
        # Open the PDF file with PyMuPDF
        pdf = fitz.open(file_path)
        pdf_length = len(pdf)

        if pdf_length == 1:
            print(f"{file_name} is archived. Skipping...")
            return {
                file_name: {"Category 3 claimants": np.nan, "Document data": "Archived"}
            }

        for page_number in range(pdf_length):
            page = pdf.load_page(page_number)
            text = page.get_text()
            lower_text = text.lower()
            page_postcode_total = count_unique_postcodes(text)

            # Initialise flags and data for the page
            page_data = {
                "page_number": page_number + 1,
                "postcode_count": page_postcode_total,
            }

            for pattern in exclude_patterns + include_patterns:
                page_data["contains_" + pattern.lower().replace(" ", "_")] = (
                    pattern.lower() in lower_text
                )

            if (
                page_data["postcode_count"] > 0
                and page_data["contains_category_3"]
                and (
                    page_data["contains_category_1"] or page_data["contains_category_2"]
                )
            ):
                print(f"{file_name} unable to process. Skipping...")
                return {
                    file_name: {
                        "Category 3 claimants": np.nan,
                        "Document data": "Unprocessed",
                    }
                }
            elif page_data["contains_category_3"]:
                project_data[file_name]["Category 3 claimants"] += page_postcode_total

        project_data[file_name]["Document data"] = "Processed"
        print(f"{file_name} has been processed")
        return project_data

    except Exception as e:
        print(f"Error processing {file_path}: {e}")


async def find_category_pages(include_patterns, exclude_patterns, directory):
    tasks = []

    # Iterate through all PDF files in the specified folder
    for file_name in os.listdir(directory):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(directory, file_name)
            tasks.append(process_pdf(file_path, include_patterns, exclude_patterns))

    # Run all tasks concurrently
    results = await asyncio.gather(*tasks)

    # Combine results from all PDFs
    combined_results = {}
    for result in results:
        if result:
            combined_results.update(result)

    return combined_results


# Example usage
async def main():
    include_patterns = ["Part 2", "Category 3"]
    exclude_patterns = ["Part 1", "Category 1", "Category 2"]
    directory = "data/book-of-references"

    project_category_3_claimants_dict = await find_category_pages(
        include_patterns, exclude_patterns, directory
    )

    # Path to your CSV file
    csv_file_path = "data/modified_projects.csv"
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path)

    # Create new columns for Category 3 claimants and processed data
    df["Category 3 claimants"] = df["Project reference"].map(
        lambda ref: project_category_3_claimants_dict.get(ref, {}).get(
            "Category 3 claimants"
        )
    )

    # Define function to process document data based on type
    def process_data(data):
        if isinstance(data, str):
            return data
        elif isinstance(data, list):
            return "processed"
        else:
            return None

    # Apply function to update the document data column
    df["Document Status"] = df["Project reference"].map(
        lambda ref: process_data(
            project_category_3_claimants_dict.get(ref, {}).get("Document data")
        )
    )
    # Save the DataFrame as a CSV file
    df.to_csv("data/final_projects.csv", index=False)
    print(f"DataFrame saved as: data/final_projects.csv")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
