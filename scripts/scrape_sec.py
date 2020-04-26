import requests 
from bs4 import BeautifulSoup
import utils
import yfinance as yf


STOCK = "AAPL"
DOC_TYPE = "10-K"

# Base URL for the SEC EDGAR browser
endpoint = r"https://www.sec.gov/cgi-bin/browse-edgar"

# Define our parameters dictionary 
cik = utils.getCIKs([STOCK])[STOCK]
try:
  company_name = yf.Ticker(STOCK).info['longName']
except: 
  company_name = STOCK
param_dict = { 'action' : 'getcompany', 'CIK' : cik, 'type' : DOC_TYPE }

# Request the URL, and then parse the response, and let user know it was successful
response = requests.get(url = endpoint, params = param_dict)
soup = BeautifulSoup(response.content, 'html.parser')
print("Request successful. Retrieving " + STOCK + " " + DOC_TYPE + " documents.")
print(response.url)

# Find the document table with our data
doc_table = soup.find_all('table', class_='tableFile2')

# Define a base URL that will be used for link building
base_url_sec = r"https://www.sec.gov"

master_list = []

# Loop through each row in the table, keep track of number of 10-K's kept (only need 10)
num_docs = 0
for row in doc_table[0].find_all('tr'):
  # find all of the columns, and move on to next row if none
  cols = row.find_all('td')
  if (len(cols)) != 0:
    
    # Grab the text
    filing_type = cols[0].text.strip()
    filing_date = cols[3].text.strip()
    filing_numb = cols[4].text.strip()

    # Find the links
    filing_doc_href = cols[1].find('a', {'href':True, 'id':'documentsbutton'})
    filing_int_href = cols[1].find('a', {'href':True, 'id': 'interactiveDataBtn'})
    filing_num_href = cols[4].find('a')
   
    # Build the URLs for all 3 href locations
    if filing_doc_href != None:
      filing_doc_link = base_url_sec + filing_doc_href['href']
    else:
      filing_doc_link = 'no link'
    
    if filing_int_href != None:
      filing_int_link = base_url_sec + filing_int_href['href']
    else:
      filing_int_link = 'no link'

    if filing_num_href != None:
      filing_num_link = base_url_sec + filing_num_href['href']
    else:
      filing_num_link = 'no link'

    # Go in to the documents link and get the .txt file for each document
    doc_response = requests.get(filing_doc_link)
    doc_text = doc_response.text
    filing_txt_link = ''
    soup_2 = BeautifulSoup(doc_text, 'html.parser')
    table_tag = soup_2.find('table', class_='tableFile', summary='Document Format Files')
    rows = table_tag.find_all('tr')
    for r in rows:
      cells = r.find_all('td')
      if len(cells) > 3 and "Complete submission" in cells[1].text:
        this_txt_loc = cells[2].a['href']
        filing_txt_link = base_url_sec + this_txt_loc

    # Convert normal url to document .json url
    cut_url = filing_txt_link.split('/')
    separator = '/'
    doc_storage_url = separator.join(cut_url[:-1]) + '/'
    json_url = doc_storage_url + 'index.json'
  
    # Request the URL and decode it
    content = requests.get(json_url).json()
   
    for f in content['directory']['item']:
      # Grab the filing summary and create a new URL leading to the file
      if f['name'] == 'FilingSummary.xml':
        xml_summary = base_url_sec + content['directory']['name'] + '/' + f['name']
        xml_content = requests.get(xml_summary).content
        soup = BeautifulSoup(xml_content, 'lxml')
        reports = soup.find('myreports')
        
        balance_stmts = ['consolidated balance sheets']
        income_stmts = ['statements of income', 'statements of operations', 'statements of earnings', 'of comprehensive income', 'of comprehensive loss']
        cash_stmts = ['cash flows']
        sh_equity_stmts = ["stockholder's equity", "shareholder's equity", "stockholders' equity", "shareholders' equity", "statements of equity", "equity" ] 

      
        financials = {}
        financials['balance'] = balance_stmts
        financials['income'] = income_stmts
        financials['cash'] = cash_stmts
        financials['equity'] = sh_equity_stmts
        
        
        for report in reports.find_all('report')[:-1]:
          report_name = report.shortname.text.lower()
          if "consolidated" not in report_name: continue
          #print('Looking:', report.shortname.text)
          for key in financials:
            possible = financials[key]
            if any(x in report_name for x in possible):
              skip_these = ['parenthetical', 'restatement', 'variable interest', 'arrangements', 'condensed', '(detail)', '(details)', '(tables)', 'details', 'paranthetical', 'parenthetical']
              if any(y in report_name for y in skip_these): continue
              print("Grabbed:", report_name, report.menucategory.text)

    # Create and store the data in a dictionary
    file_dict = {}
    file_dict['file_type'] = filing_type
    file_dict['file_number'] = filing_numb
    file_dict['file_date'] = filing_date
    file_dict['links'] = {}
    file_dict['links']['documents'] = filing_doc_link
    file_dict['links']['interactive_data'] = filing_int_link
    file_dict['links']['filing_number'] = filing_num_link
    file_dict['links']['text_file'] = filing_txt_link
    file_dict['links']['doc_storage_url'] = doc_storage_url
    file_dict['links']['filing_summary'] = xml_summary

    # Let the user know it's working
    print('='*100)
    print("Company: " + company_name)
    print("Filing Type: " + filing_type)
    print("Filing Date: " + filing_date)
    print("Filing Number: " + filing_numb)
    print("Filing Link: " + filing_doc_link)
    print("Filing Summary: " + xml_summary)
    
    # Append the dictionary to the master list
    master_list.append(file_dict)

    # Increment number of 10ks if type is 10k and link is not empty
    if filing_type == '10-K' and filing_txt_link is not "no link": num_docs += 1
    if num_docs == 10: break

print('='*100)
print(str(len(master_list)) + " documents retrieved. " + str(num_docs) + " 10-Ks collected.")

'''
	ALL 10K LOCATIONS COLLECTED AND STORED - NOW PROCESSING
'''

