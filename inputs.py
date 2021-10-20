import csv
from decimal import *
import json

with open('inputs/constants.json', 'r') as jsonfile:
    constants = json.load(jsonfile)

def get_search_data():
    with open('inputs/card_data.csv', 'r') as file:
        reader = csv.DictReader(file)
        cards = [r for r in reader]

    search_names = [c['search'] for c in cards]
    search_names = list(dict.fromkeys(search_names)) # Deduplicate
    search_list = [Search(name, cards) for name in search_names]
    
    return search_list


class Search:
    def __init__(self, search_name, cards):
        self.name = search_name
        self.cards = [Card(c) for c in cards if c['search'] == search_name]
            
    def terms(self):
        return [c.search_term for c in self.cards]
        
    def query(self):
        base = (constants['base_queries'].get(self.name) or '')
        terms = ', '.join(self.terms())
        return f'{base} ({terms}) -japanese -japan -jp'
        

class Card:
    def __init__(self, row):
        self.search = row['search']
        self.number = row['number']
        self.name = row['name']
        self.mkt_price = Decimal(row['mkt_price'])

        if row['search_term'] == '':
            self.search_term = row['name']
        else:
            self.search_term = row['search_term']