# Project Requirements: Web Scraping and Financial Data Processing

**Overall Objective:**  
The goal of this project is to capture, process, and store data related to companies, NSDs (Sequential Document Numbers), and financial data from an online source. The system must update the data periodically, identifying and processing only new or modified information.

## 1. Company Data Capture
Company data will be captured in two stages:

1. **General Company List Capture:**
   - Navigate through the paginated webpage listing all companies.
   - Extract basic information (e.g., name, ID, industry) for each listed company.
   - Store the captured data for later comparison and updates.

2. **Company Detail Capture:**
   - From the general list, access individual company detail pages.
   - Extract detailed and specific data for each company (e.g., address, contacts, available financial data).
   - Merge new data with the existing database, intelligently avoiding duplicates and keeping the data updated.

## 2. NSD (Sequential Document Number) Data Capture
The NSD data will be captured with the following steps:

1. **Sequential NSD Capture:**
   - Extract a sequential list of NSDs published online, containing information such as the company name, submission date, and other relevant details.
   - Infer the latest available NSD using the following methodologies:
     - **Dynamic Gap Filling and Interpretation of Skips:** Implement a logic to cross-check captured NSDs with the subsequent unutilized NSD numbers, identifying possible skips in sequence and dynamically filling in gaps without needing to estimate large intervals.
     - **Adjustable Safety Margin:** Implement a variable safety margin that can be adjusted to ensure capture accuracy, factoring in patterns in the frequency and timing of NSD publications.

2. **Gap Filling and Interpretation of Skips:**
   - Develop logic to detect gaps in the sequential NSD numbers and intelligently infer whether these gaps are due to non-utilization or errors in capture.
   - Implement strategies to backfill these gaps by re-querying and ensuring no valid NSD is missed.

3. **Exception Handling and Re-querying:**
   - Include robust exception handling to manage scenarios where NSD capture fails or unexpected patterns are detected.
   - If an anomaly is detected (e.g., large gaps or unexpected sequence jumps), trigger a re-query of the NSD source to ensure the data is accurate and complete.
   - Implement notifications or alerts in case of recurring issues, so that these can be manually reviewed if needed.

## 3. Financial Data Capture and Processing
Financial data will be captured from the NSD details. Processing will be done as follows:

1. **Financial Data Capture:**
   - Access a specific URL linked to the NSD to extract financial data using XPATH.
   - Store the captured financial data in its raw form, preserving all versions and history.

2. **Version Control and Financial Data Updates:**
   - Implement a version control logic that ensures only the latest version of the financial data is marked as current.
   - The system should compare updated financial data with previous versions to identify and process new information.

3. **Reprocessing Financial Data:**
   - After financial data updates, specific mathematical operations must be performed to recalculate values based on quarterly financial statements.
   - For example:
     - **For accounts starting with '3' or '4':** The last quarter's value must be adjusted by subtracting the previous quarters' values from the December value.
     - **For accounts starting with '6' or '7':** All quarters' values must be adjusted similarly by subtracting the values of the preceding quarters.
     - If the account prefix is not in these categories, no adjustments are needed.

## 4. Periodic Updates and Data Comparison
- **Database Comparison:**
  - In all data capture stages, the system must compare captured data with the current database to identify new or modified information.
  - Only changes in data should trigger re-capture and reprocessing, minimizing redundancy and ensuring system efficiency.

- **Scheduled Captures and Processing:**
  - Data capture will be performed at irregular and random intervals to reflect online updates.
  - The system should be configured for automated data capture and processing, based on *on-demand* requests.

## 5. Additional Requirements and Clarifications

1. **Safety Margin for NSDs:**
   - The safety margin for NSD capture should be adjustable to account for variability in NSD publication frequency.

2. **Performance Considerations:**
   - The system must minimize rework during updates, focusing on efficient data processing and updating.

3. **Version Control for Financial Data:**
   - Only the latest version of financial data is relevant for updates, though previous versions should be maintained for comparison purposes.

4. **Mathematical Operations for Financial Data:**
   - Operations are specific to the type of financial statement, with different adjustments for different categories of accounts (e.g., last quarter adjustments for '3' and '4', full quarter adjustments for '6' and '7').

5. **Logging:**
   - Maintain logs of errors and successes to facilitate troubleshooting and ensure traceability of all operations.

6. **Code Stability:**
   - The code is to be delivered *as-is*, with no expectation of further changes or adjustments unless required by new updates from the data source.
