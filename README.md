# SEC Company 10-K Parser and Stock Analyzer

## Project Overview
Project created to scrape the SEC EDGAR filings website to retrieve data from company 10-K filings. Specifically, retrieving the financial statements (balance sheets, income statements, shareholder's equity statements). The data is then parsed and used for calculations to analyze stock performance and identify potential investment opportunities.

### scrape_sec.py
- User enters a stock ticker,  and a document type (for now these are hard-coded, but plan to build a UI that will make this more user-friendly).
- The script then requests the company's SEC Edgar filing URL, and parses the response to get the URLs for the 10 most recent documents (of type specified).
- Each document's URL is then requested, and parsed to grab the filing summrary.
- The filing summary for each document is then requested and parsed, in order to grab the URLs for the company's financial statements.
- Financial statements are then scraped.
