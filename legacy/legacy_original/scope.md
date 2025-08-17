# Project Scope: Web Scraping and Financial Data Processing

## **1. Objective**
The **Finance Ledger Yearly (FLY)** project is designed to **capture, process, and store** financial data related to **companies, NSDs (Sequential Document Numbers), corporate events, and stock market data**. The system ensures **periodic updates** by identifying and processing only **new or modified** data.

## **2. Data Capture Overview**
The system extracts data from various online sources using **web scraping** and **automated data processing**. It is structured into the following main components:

1. **CompanyData Information Scraping** (Handled by `company_data_processor.py`)
2. **NSD Data Scraping** (Handled by `nsd_processor.py`)
3. **Financial Statements Extraction & Processing** (Handled by `statements_processor.py` and `intel_processor.py`)
4. **Corporate Events Data Extraction** (Handled by `corporate_events_processor.py`)
5. **Stock Market & Historical Data Processing** (Handled by `market_processor.py`, `historical_stock_url_processor.py`, `stock_processor.py`)

---

## **3. Data Collection and Processing Workflow**

### **3.1 CompanyData Data Capture**
**Modules:** `company_data_processor.py`
- **General CompanyData List Extraction:**
  - Navigate paginated company listings.
  - Extract **basic metadata** (e.g., name, ticker, industry).
  - Store extracted data in the `tbl_company_data_info` table.

- **CompanyData Detail Extraction:**
  - Fetch **detailed financial and governance information**.
  - Scrape **CNPJ, sector, subsector, listing type, and trading details**.
  - Merge with existing data, ensuring **no duplication**.

---

### **3.2 NSD Data Capture**
**Modules:** `nsd_processor.py`
- **Sequential NSD Capture:**
  - Extract published **NSD numbers, submission dates, and company associations**.
  - Implement **gap filling & dynamic sequence tracking**:
    - Detect **missing NSD numbers** and intelligently estimate missing data.
    - Adjust for **irregular NSD publication** patterns.

- **Re-query and Error Handling:**
  - If a gap is detected, re-query to verify missing NSDs.
  - Exception handling ensures **no failures in sequential data processing**.

- **Database Storage:**
  - Data is saved to `tbl_nsd`, **maintaining historical versions**.

---

### **3.3 Financial Statements Capture & Processing**
**Modules:** `statements_processor.py`, `intel_processor.py`
- **Financial Statement Scraping:**
  - Extract **financial statements and quarterly reports** linked to NSD.
  - Process **income statements, balance sheets, and cash flows**.

- **Data Standardization & Processing:**
  - `intel_processor.py` **applies categorization criteria** to standardize financial data.
  - Adjusts:
    - **Accounts starting with '3' or '4'** → Adjust quarterly values.
    - **Accounts starting with '6' or '7'** → Ensure correct aggregation.

- **Storage & Versioning:**
  - Data is stored in:
    - `tbl_statements_raw` (Raw statements before processing)
    - `tbl_statements_normalized` (Standardized financial data)
  - Only the **latest version** is marked as "current" while preserving **historical changes**.

---

### **3.4 Corporate Events Capture**
**Modules:** `corporate_events_processor.py`
- **Captures** corporate actions such as:
  - **Stock splits, dividend payments, capital increases, mergers.**
- **Processes** financial impacts on stock valuation.
- **Integrates** corporate events data into:
  - `tbl_statements_corp_events`
  - `tbl_stock_data`

---

### **3.5 Stock Market & Historical Data Processing**
**Modules:** `market_processor.py`, `historical_stock_url_processor.py`, `stock_processor.py`
- **Historical Stock Data Collection:**
  - Uses `historical_stock_url_processor.py` to fetch **historical prices** for each company.
  - Extracts **monthly and quarterly median stock prices** for **fundamental analysis**.

- **Daily Market Updates:**
  - `market_processor.py` fetches **daily stock prices, volume, and corporate event effects**.
  - Computes **quarterly averages** and integrates with financial statement analysis.

- **Final Storage & Processing:**
  - Stores cleaned and structured data in:
    - `tbl_stock_data` (Daily market data)
    - `tbl_statements_corp_events` (Corporate events affecting stock)

---

## **4. System Features & Automation**

### **4.1 Periodic Data Updates**
- The system performs **scheduled and on-demand updates**:
  - **On-Demand Scraping** (Triggered manually or via API request).
  - **Scheduled Batch Updates** (Irregular/randomized execution to reflect real-world updates).

- Ensures **only new or modified data is reprocessed**, optimizing efficiency.

---

### **4.2 Database & Storage Structure**
#### **Database Schema Highlights**
- **CompanyData Data:** `tbl_company_data_info`
- **NSD Tracking:** `tbl_nsd`
- **Raw Financial Statements:** `tbl_statements_raw`
- **Standardized Financial Statements:** `tbl_statements_normalized`
- **Corporate Events & Market Data:** `tbl_statements_corp_events`
- **Stock Market History:** `tbl_stock_data`

---

### **4.3 Performance & Benchmarking**
- `base_processor.py` includes **benchmarking utilities** to:
  - Compare processing performance under **different worker/thread configurations**.
  - Optimize **database I/O and memory usage**.

- **Log-based performance tracking** ensures:
  - **Consistent execution time measurement** (`log_execution_time()`).
  - **Thread-based batch processing performance monitoring**.

---

## **5. Error Handling & Data Validation**
- **Robust exception handling** across all processors ensures:
  - **Missing/Incomplete Data Handling** (`try-except` for failed requests).
  - **Re-querying for failed NSDs** when gaps are detected.
  - **Logging of unexpected data patterns** (`log_error()` standard).

- **Validation Checks:**
  - **CompanyData data** is checked against duplicate entries.
  - **Financial statements** are validated against expected schema structures.
  - **Stock market data** is compared against previous records to detect anomalies.

---

## **6. Conclusion**
The FLY project ensures:
- **Accurate and timely financial data extraction**.
- **Standardized data processing and storage**.
- **Automated updates with high efficiency**.
- **Scalable architecture to integrate new financial data sources**.

By continuously improving **scraping logic, database management, and processing efficiency**, the system remains a **robust financial intelligence tool**.
