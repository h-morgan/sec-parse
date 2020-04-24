from bs4 import BeautifulSoup
import requests
import sys
import utils
import yfinance as yf
import datetime

# Company we want to access
STOCK = 'RTN'

# Set up with some initial params
CURRENT_YEAR = datetime.datetime.now().year
OLDEST_DATA_YEAR = CURRENT_YEAR - 10

# Get stock name and CIK number 
cik = utils.getCIKs([STOCK])[STOCK]
company_name = yf.Ticker(STOCK).info['longName']
doc_type = "10-K"

# HTML for the search page
base_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={}&type={}"
edgar_response = requests.get(base_url.format(cik, doc_type))
edgar_txt = edgar_response.text
#print(base_url.format(cik, doc_type, doc_date))

# Find location/link for the 10K documents
doc_links = {}
soup = BeautifulSoup(edgar_txt, 'html.parser')
table_tag = soup.find('table', class_='tableFile2')
rows = table_tag.find_all('tr')
for row in rows:
  cells = row.find_all('td')
  if len(cells) > 3: 
    date_ = cells[3].text
    year_ = int(date_[0:4])
    if year_ < OLDEST_DATA_YEAR: continue  
    this_doc_location = cells[1].a['href']
    doc_links[date_] = "https://www.sec.gov" + this_doc_location

# Exit the program if the 10-Ks were not found
if doc_links == {}:
  print("Couldn't locate the 10-Ks on the SEC website. Exiting.")
  sys.exit
else:
  print("Got the 10-Ks for " + STOCK + " from the SEC.")

# Obtain HTML for each 10-K in our doc_links dictionary (there should be 10)
xbrl_links = {}
for dt in doc_links:
  this_link = doc_links[dt]
  doc_response = requests.get(this_link)
  print(doc_response.url)
  doc_text = doc_response.text
  #Get the xbrl link
  xbrl_link = '' 
  soup = BeautifulSoup(doc_text, 'html.parser')
  table_tag = soup.find('table', class_ = 'tableFile', summary="Data Files")
  rows = table_tag.find_all('tr')
  for row in rows:
    cells = row.find_all('td')
    if len(cells) > 3 and 'INS' in cells[3].text:
      this_xbrl_loc = cells[2].a['href']
      xbrl_link = "https://www.sec.gov/" + this_xbrl_loc 
      xbrl_links[dt] = xbrl_link

'''
# Open each XBRL document and do what u does !
x = 0
for key in xbrl_links:
  x_link = xbrl_links[key]
  xbrl_response = requests.get(x_link)
  xbrl_text = xbrl_response.text
  # Find that you want to find girl!
  #print(xbrl_text)
  soup = BeautifulSoup(xbrl_text, 'lxml')
  tag_list = soup.find_all()
  for tag in tag_list: 
    if "us-gaap:" in tag.name and tag.text.isdigit():
      print(tag.name, tag.text)
  x += 1
  if x > 0: break
'''
