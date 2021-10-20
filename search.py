from bs4 import BeautifulSoup
import json
import pandas
import requests

from analyze import clean_field, calculate_field_value

BASE_URL = 'https://www.ebay.com/sch/i.html'

# Get HTML classes corresponding to fields
with open('inputs/fields.json', 'r') as fields_file:
    fields = json.load(fields_file)


def search_ebay(search, search_type):
    html = get_html(search.query(), search_type)
    listings = parse_html(html, search)
    return listings

    
def get_html(query, search_type):
    """
    Sends request to eBay and returns list of HTML blocks, with each
    representing a card listing
    """
    params = {
        '_nkw': query,
        '_stpos': 60640, # My zip code
        '_sop': {'new': 10, 'soon': 1, 'cheap': 2}[search_type],
        '_ipg': 200, # Results per page (up to 200)
        '_udhi': 100 # Max price
    }
    
    # Make request and turn into soup
    response = requests.get(BASE_URL, params=params)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Isolate listings (first div is not a listing)
    listings = soup.find_all('div', class_='s-item__info clearfix')
    if len(listings) > 1:
        return listings[1:]
    else:
        return []


def parse_html(html, search):
    """
    Parses data in HTML blocks and returns a dataframe of listings
    """
    
    def get_field_value(field, div):
        """
        Finds class associated with each field and gets value
        """
        if not field.get('html_class'):
            return
            
        tag = div.find(class_=field['html_class'])
        if not tag:
            return
        
        # Fix spans for title and listing date
        if field['name'] == 'title':
            for span in tag('span'):
                span.decompose()
        elif field['name'] == 'listing_date':
            for span in tag('span'):
                span.unwrap()
                
        # Get href for URL, or inner text for other fields
        if field['name'] == 'url':
            value = tag.get('href')
        else:
            value = tag.string
            
        # Clean fields by calling functions listed in JSON
        if field.get('cleaner'):
            value = clean_field(value, field['cleaner'])
            
        return value
        
    listings = []
    for div in html:
        listing = {'search': search.name}
        
        # Get field values from HTML
        for field in fields:
            listing[field['name']] = get_field_value(field, div)
        
        # Get calculated field values
        for field in [f for f in fields if f.get('calculated')]:
            listing[field['name']] = calculate_field_value(field['name'], listing, search)
            
        listings.append(listing)
        
    df = pandas.DataFrame(listings)
    return df

 
