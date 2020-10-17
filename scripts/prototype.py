import requests 
from bs4 import BeautifulSoup
import utils
import yfinance as yf


class Company:
  def __init__(self, stockTicker, docType='10-K', verbose=False):
    self.verbose = verbose
    self.stock = stockTicker
    self.company = self.getCompanyName()
    self.cik = utils.getCIKs([stockTicker])[stockTicker]
    self.doc_type = docType
    self.endpoint =  r"https://www.sec.gov/cgi-bin/browse-edgar"
    self.filing_storage = self.getFilingInfo("10-K")
    self.key_data = ''

  def getCompanyName(self):
    '''
    	Function to return the name of the company, given it's stock ticker.
    	Utilizes yahoo finance
    '''
    try:
      company_name = yf.Ticker(self.stock).info['longName']
    except: 
      company_name = self.stock

    return company_name


  def getFilingInfo(self, doc_to_get):
    '''
	Function to get 10 most recent 10-K filings, and all associated links, for the company
	Returns a list of dicts with each dict containing the links for one 10-K
    ''' 
    param_dict = { 'action' : 'getcompany', 'CIK' : self.cik, 'type' : doc_to_get }

    # Request the URL, and then parse the response, and let user know it was successful
    response = requests.get(url = self.endpoint, params = param_dict)
    soup = BeautifulSoup(response.content, 'html.parser')
    print("Request successful. Retrieving " + self.stock + " " + doc_to_get + " documents.")
    print(response.url)
    
    # Find the document table with our data
    doc_table = soup.find_all('table', class_='tableFile2')
    
    # Define a base URL that will be used for link building
    base_url_sec = r"https://www.sec.gov"
    
    master_list = []

    # Loop through each row in the table, keep track of number of 10-K's kept
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

        # Let the user know it's working
        if self.verbose == True:
          print('='*100)
          print("Company: " + self.company)
          print("Filing Type: " + filing_type)
          print("Filing Date: " + filing_date)
          print("Filing Number: " + filing_numb)
          print("Filing Link: " + filing_doc_link)
        
        # Append the dictionary to the master list
        master_list.append(file_dict)

        # Increment number of 10ks if type is 10k and link is not empty
        if filing_type == self.doc_type and filing_txt_link is not "no link": num_docs += 1
        if num_docs == 1: break

    return master_list

    print('='*100)
    print(str(len(master_list)) + " documents retrieved. " + str(num_docs) + " 10-Ks collected.")


  #def parseFinancialStmts():
    


# keep this here for now, for testing 
if __name__ == "__main__":
  test = Company('AAPL', verbose=True)
  print("Done. Collected all 10-ks for", test.company)

  #print(test.filing_storage[3]['links']['financial_stmts'])

