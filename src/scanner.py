import asyncio
import fitz
import os
import re
import json
import pandas as pd
import numpy as np
from scipy import stats


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

    # Group by 'Application subsector' and count the number of applications
    grouped_projects = df[df['Document Status'] == 'Processed'].groupby('Application subsector').size().reset_index(name='Project count')

    # Initialize lists to store statistics for Category 3 claimants
    means = []
    variances = []
    ci_lower_bounds = []
    ci_upper_bounds = []

    # Calculate statistics for 'Category 3 claimants' for each subsector
    for subsector in grouped_projects['Application subsector']:
        subsector_data = df[(df['Application subsector'] == subsector) & (df['Document Status'] == 'Processed')]['Category 3 claimants']
        
        # Calculate mean and variance
        mean_claimants = subsector_data.mean()
        variance_claimants = subsector_data.var()

        # Confidence interval calculation
        confidence_level = 0.95
        n = len(subsector_data) - 1
        if n > 0:
            std_err = stats.sem(subsector_data)
            ci = stats.t.interval(confidence_level, n, loc=mean_claimants, scale=std_err)
        else:
            ci = (None, None)  # Handle cases where data is insufficient for CI
        
        # Append statistics to lists
        means.append(mean_claimants)
        variances.append(variance_claimants)
        ci_lower_bounds.append(ci[0])
        ci_upper_bounds.append(ci[1])

    # Add the calculated statistics to the grouped DataFrame
    grouped_projects['Mean'] = means
    grouped_projects['Variance'] = variances
    grouped_projects['CI lower bound'] = ci_lower_bounds
    grouped_projects['CI upper bound'] = ci_upper_bounds

    # Save the final DataFrame to CSV
    csv_file_path = 'data/subsector_statistics_with_claimants.csv'
    grouped_projects.to_csv(csv_file_path, index=False)

    print(f"CSV file created at: {csv_file_path}")


# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
