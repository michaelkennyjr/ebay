import datetime
from dateutil.relativedelta import relativedelta
from decimal import *

from inputs import constants

def clean_field(value, method):
    """
    Transforms text value from HTML according to the prescribed method
    """
    def to_number(value):
        chars = [c for c in value if c == '.' or c.isdigit()]
        if len(chars) == 0:
            return None
        else:
            return Decimal(''.join(chars))
            
    def to_datetime(value):
        year = datetime.datetime.now().year
        time_listed = f'{year} {value}'
        time_listed = datetime.datetime.strptime(time_listed, '%Y %b-%d %H:%M')

        # Change to previous year if datetime is after now
        if time_listed > datetime.datetime.now():
            time_listed -= relativedelta(years=1)
            
        # Change Pacific time to Central
        time_listed += relativedelta(hours=2)

        return time_listed
        
    def to_countdown(value):
        time_left = value.replace(' left', '')

        periods = {'d': 0, 'h': 0, 'm': 0}
        for period in periods:
            if period in time_left:
                time_split = time_left.split(period)
                periods[period] = int(time_split[0])
                time_left = time_split[1]
                
        return '{:02d}d {:02d}h {:02d}m'.format(
            periods['d'],
            periods['h'],
            periods['m']
        )
    
    if value in (None, ''):
        return
    
    return locals()[method](value)
    
    
def calculate_field_value(field_name, listing, search):
    """
    Calculates value from other field values scraped from HTML
    """
    
    def total_price(listing, search):
        return (listing['price'] or 0) + (listing['shipping'] or 0)
        
    def card_name(listing, search):
        return match_card(listing, search.cards, 'name')
        
    def condition(listing, search):
        if listing['title'] is None:
            return
    
        conditions = constants['conditions']
        
        # Split title on all non-alphanumeric characters
        split_title = []
        next_word = True
        for char in listing['title']:
            if char.isalnum():
                if next_word:
                    split_title.append(char)
                    next_word = False
                else:
                    split_title[-1] += char
            else:
                next_word = True
        
        # Check if any keywords match the title
        for condition in conditions:
            for term in conditions[condition]['terms']:
                
                # If keyword contains space/symbol, search entire title; otherwise do word match
                if any([char in term for char in " -/"]):
                    if term.lower() in listing['title'].lower():
                        return condition
                else:
                    for word in split_title:
                        if word.lower() == term.lower():
                            return condition
        
    def mkt_price(listing, search):
        return match_card(listing, search.cards, 'mkt_price')
        
    def value_score(listing, search):
        if listing['mkt_price'] is None:
            return
        else:
            return 100 * (1 - listing['total_price'] / listing['mkt_price'])
    
    def cond_price(listing, search):
        if listing['mkt_price'] in (None, 0):
            return
        else:
            conditions = constants['conditions']
            list_condition = conditions.get(listing['condition'])
            
            # Get price multiplier for condition (default to lowest)
            all_rates = [conditions[c].get('price_rate') for c in conditions]
            price_rate = min([r for r in all_rates if r is not None])
            if list_condition:
                if 'price_rate' in list_condition:
                    price_rate = list_condition['price_rate'] 
            
            return listing['mkt_price'] * Decimal(price_rate)      
    
    def cond_value(listing, search):
        if listing['total_price'] in (None, 0) or listing['cond_price'] in (None, 0):
            return
        return -100 * (listing['total_price'] - listing['cond_price']) / listing['cond_price']
    
    return locals()[field_name](listing, search)


def match_card(listing, cards, attr):
    """
    Finds first match for listing title from list of cards
    """
    
    def check_match(word, listing):
        if None in [word, listing['title']]:
            return False
        else:
            return word.lower() in listing['title'].lower()
    
    match = None
    for card in cards:
        search_words = card.search_term.split(' ')
        if all([check_match(word, listing) for word in search_words]):
            match = card
            break
            
    if match:
        return getattr(match, attr)