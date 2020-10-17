import requests
import yfinance as yf

from forms import filing_form


def getCompanyName(ticker):
  '''
  	Function to return the name of the company, given it's stock ticker.
  	Utilizes yahoo finance
  '''
  company_name = ''
  company_name = yf.Ticker(ticker.info['longName'])
    

  print(company_name)

print(filing_form.filing)



