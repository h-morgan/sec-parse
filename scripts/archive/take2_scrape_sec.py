# following youtube tutorial
import csv
import pprint
import pathlib
import collections
import xml.etree.ElementTree as ET
import utils
import yfinance as yf
import requests
from bs4 import BeautifulSoup

# ===== THIS FROM OTHER TUTORIAL JUST TO GET LOCATIONS OF XBRL DOCS FROM SEC =====================
# SO I DONT NEED TO SAVE THEM TO MY COMPUTER EACH TIME

STOCK = 'FB'

# Get stock name and CIK number 
cik = utils.getCIKs([STOCK])[STOCK]
company_name = yf.Ticker(STOCK).info['longName']
doc_type = "10-Q"

# HTML for the search page
base_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={}&type={}"
edgar_response = requests.get(base_url.format(cik, doc_type))
edgar_txt = edgar_response.text

# Find location/link for the document
doc_link=''
soup = BeautifulSoup(edgar_txt, 'html.parser')
table_tag = soup.find('table', class_='tableFile2')
rows = table_tag.find_all('tr')
for row in rows:
  cells = row.find_all('td')
  if len(cells) > 3: 
    date_ = cells[3].text
    year_ = int(date_[0:4])
    if date_ == '2019-10-31':  
      this_doc_location = cells[1].a['href']
      doc_link = "https://www.sec.gov" + this_doc_location
 
# Obtain HTML for document page
doc_resp = requests.get(doc_link)
doc_str = doc_resp.text

# Find the XBRL links
xbrl_links = {}
soup = BeautifulSoup(doc_str, 'html.parser')
table_tag = soup.find('table', class_ = 'tableFile', summary='Data Files')
rows = table_tag.find_all('tr')
for row in rows:
  cells = row.find_all('td')
  if len(cells) > 3:
    doc_type = cells[3].text
    doc_href = cells[2].a['href']
    if ".CAL" in doc_type: xbrl_links['cal'] = "https://sec.gov" + doc_href 
    if ".DEF" in doc_type: xbrl_links['def'] = "https://sec.gov" + doc_href 
    if ".LAB" in doc_type: xbrl_links['lab'] = "https://sec.gov" + doc_href 
    if "XML" in doc_type: xbrl_links['htm'] = "https://sec.gov" + doc_href 

# ===== END OF GETTING DOCS, RESUME ORIGINAL YOUTUBE TUTORIAL ====================

# Define the paths to the documents (retrieved in our preamble above)
file_htm = xbrl_links['htm']
file_cal = xbrl_links['cal']
file_def = xbrl_links['def']
file_lab = xbrl_links['lab']

# Define the different storage components
storage_list = []
storage_values = {}
storage_gaap = {}

# Create a named tuple
FilingTuple = collections.namedtuple("FilingTuple", ['file_path', 'namespace_element', 'namespace_label'])

# Initialize my list of named tuples, I plan to parse
files_list = [
    FilingTuple(file_cal, r'{http://www.xbrl.org/2003/linkbase}calculationLink', 'calculation'), 
    FilingTuple(file_def, r'{http://www.xbrl.org/2003/linkbase}definitionLink','definition'), 
    FilingTuple(file_lab, r'{http://www.xbrl.org/2003/linkbase}labelLink','label')
    ]

# Define 2 categories of labels - those I want, and those I don't want
avoids = ['linkbase', 'roleRef']
parse = ['label', 'labelLink', 'labelArc', 'loc', 'definitionLink', 'definitionArc', 'calculationArc']

# Create 2 sets to store my keys - label list and calculation list 
lab_list = set()
cal_list = set()

# Loop through each file
for file_ in files_list:
  # Aside - need to get request our files from SEC website
  f_response = requests.get(file_.file_path)
  f_text = f_response.text
  
  # NOW parse the file
  tree = ET.ElementTree(ET.fromstring(f_text)) 

  # Grab all the namespace elements in the tree
  elements = tree.findall(file_.namespace_element)

  # Loop through each element
  for element in elements:
    # If the element has children, we want to parse those as well
    for child_element in element.iter():
      # Split the label at the closing curly bracket to separate namespace from label
      element_split_label = child_element.tag.split('}')
      namespace = element_split_label[0]
      label = element_split_label[1]
      
      # Is this label one we want?
      if label in parse:
        # Define the item type label - add namespace label to help us determine where these labels come from
        element_type_label = file_.namespace_label + '_' + label

        # Initialize smaller dictionary
        dict_storage = {}
        dict_storage['item_type'] = element_type_label

        # Grab all the attribute keys
        cal_keys = child_element.keys()

        # For each attribute do something
        for key in cal_keys:
          if '}' in key:
            # We just want the portion of the key that comes after the curly bracket, if present
            new_key = key.split('}')[1]
            dict_storage[new_key] = child_element.attrib[key]
          else:
            # If no curly bracket in key - no namespace - we can just use the original key
            dict_storage[key] = child_element.attrib[key]

        # Now start organizing this data (right now label proving to be greatest source of truth)
        if element_type_label == "label_label":
          # Grab the label key
          key_store = dict_storage['label']
          
          # Create master key
          master_key = key_store.replace('lab_', '')

          # Split the master key
          label_split = master_key.split('_')

          # Create my gaap id
          gaap_id = label_split[0] + ':' + label_split[1]
    
          # One master dictionary contains only the values from the XML files 
          storage_values[master_key] = {}
          storage_values[master_key]['label_id'] = key_store
          storage_values[master_key]['location_id'] = key_store.replace('lab_', 'loc_')
          storage_values[master_key]['us_gaap_id'] = gaap_id
          storage_values[master_key]['us_gaap_value'] = None
          storage_values[master_key][element_type_label] = dict_storage

          # The other dictionary will only contain the values related to GAAP metrics
          storage_gaap[gaap_id] = {}
          storage_gaap[gaap_id]['id'] = gaap_id
          storage_gaap[gaap_id]['master_id'] = master_key

        # Add to dictionary
        storage_list.append([file_.namespace_label, dict_storage])

'''
	PARSE THE HTM 10Q FILE
'''

# Load the XML file (the actual 10-Q or 10-K)
htm_response = requests.get(file_htm)
htm_text = htm_response.text

# Now parse the file
tree = ET.ElementTree(ET.fromstring(htm_text)) 

# Loop through all of the elements
for element in tree.iter():
  
  if 'nonNumeric' in element.tag:
    # Grab the attribute name and the master ID
    attr_name = element.attrib['name']
    gaap_id = storage_gaap[attr_name]['master_id']
  
    storage_gaap[attr_name]['context_ref'] = element.attrib['contextRef']
    storage_gaap[attr_name]['context_id'] = element.attrib['id']
    storage_gaap[attr_name]['continued_at'] = element.attrib.get('continuedAt', 'null')
    # .get method on a dictionary allows us to specify default value (in our case, null) if the key doesn't exist
    storage_gaap[attr_name]['escape'] = element.attrib.get('escape', 'null')
    storage_gaap[attr_name]['format'] = element.attrib.get('format', 'null')

  # same process for nonFraction tags, but this time we grab the text too
  if 'nonFraction' in element.tag:
    #Grab the attribute name and the master ID
    attr_name = element.attrib['name']
    gaap_id = storage_gaap[attr_name]['master_id']
  
    storage_gaap[attr_name]['context_ref'] = element.attrib['contextRef']
    storage_gaap[attr_name]['fraction_id'] = element.attrib['id']
    storage_gaap[attr_name]['unit_ref'] = element.attrib.get('unitRef', 'null')
    storage_gaap[attr_name]['decimals'] = element.attrib.get('decimals', 'null')
    storage_gaap[attr_name]['scale'] = element.attrib.get('scale', 'null')
    storage_gaap[attr_name]['format'] = element.attrib.get('format', 'null')
    storage_gaap[attr_name]['value'] = element.text.strip() if element.text else 'null'
   
    # Don't forget to store the actual value if it exists
    if gaap_id in storage_values:
      storage_values[gaap_id]['us_gaap_value'] = storage_gaap[attr_name]

'''
	DUMP IT ALL INTO CSV FILES
'''

file_name = 'sec_xbrl_scrape_content.csv'
with open(file_name, mode='w', newline='') as sec_file:
  # Create a writer
  writer = csv.writer(sec_file)
  # Write the header
  writer.writerow(['FILE', 'LABEL', 'VALUE'])
  # Dump the dict to the csv file
  for dict_cont in storage_list:
    for item in dict_cont[1].items():
      writer.writerow([dict_cont[0]] + list(item))

file_name = 'sec_xbrl_scrape_values.csv'
with open(file_name, mode='w', newline='') as sec_file:
  # Create a writer
  writer = csv.writer(sec_file)
  # Write the header
  writer.writerow(['ID', 'CATEGORY', 'LABEL', 'VALUE'])
  # Dump the dict to the csv file
  for storage_1 in storage_values:
    for storage_2 in storage_values[storage_1].items():
      # If the value is a dict, then we have one more possible level
      if isinstance(storage_2[1], dict):
        for storage_3 in storage_2[1].items():
          writer.writerow([storage_1] + [storage_2[0]] + list(storage_3))
      else: 
        # If not a dict, in some cases you won't have a storage_2
        if storage_2[1] != None:
          writer.writerow([storage_1] + [storage_2] + ['None'])
