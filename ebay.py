import pandas
import sys

from inputs import get_search_data
from search import search_ebay

SEARCH_TYPE = 'new'
if len(sys.argv) > 1:
    if sys.argv[1] in ['new', 'soon', 'cheap']:
        SEARCH_TYPE = sys.argv[1]


searches = get_search_data()
results = [search_ebay(search, SEARCH_TYPE) for search in searches]

df = pandas.concat(results)
df = df[df['title'].notnull() & df['price'].notnull() & (df['value_score'] >= 0)]

if SEARCH_TYPE == 'soon':
    df.sort_values('time_left', inplace=True)
    df = df[df.bid_count.notnull()]
elif SEARCH_TYPE == 'new':
    df.sort_values('time_listed', ascending=False, inplace=True)
    df = df[df.bid_count.isnull()]
else:
    df.sort_values('value_score', ascending=False, inplace=True)
    df = df[df.bid_count.isnull()]

df.to_csv('results.csv', index=False)

"""
html = results.to_html()
with open('ebay.html', 'w', encoding='utf-8') as htmlfile:
    htmlfile.write(html)
"""