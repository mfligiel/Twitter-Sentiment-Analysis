
# -*- coding: utf-8 -*-
"""
Created on Thu May 20 15:12:39 2021

@author: matfl
"""


import pandas as pd
from twython import Twython
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer 
import time
import json
import pickle

#bokeh imports

from bokeh.io import show
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, PreText, Select, CustomJS
from bokeh.plotting import figure
# Enter your keys/secrets as strings in the following fields

f = open(r'C:\Users\matfl\OneDrive\Documents\Credentials_twittergcp.json')
credentials = json.load(f)

f.close()

#prep file for upload
from os import environ
from google.cloud import storage

#bucketName = environ.get('foojibot_bucket_mf_try1')
#storage_client = storage.Client()
#bucket = storage_client.get_bucket(bucketName)


#function
def pull_tweet():
    python_tweets = Twython(credentials['CONSUMER_KEY'], credentials['CONSUMER_SECRET'])

# Create our query
    query = {'q': 'Bitcoin',
        'result_type': 'latest',
        'count': 1000,
        'lang': 'en',
        }

# Search tweets
    dict_ = {'user': [], 'date': [], 'text': []}
    for status in python_tweets.search(**query)['statuses']:
        dict_['user'].append(status['user']['screen_name'])
        dict_['date'].append(status['created_at'])
        dict_['text'].append(status['text'])

# Structure data in a pandas DataFrame for easier manipulation
    df_tweets = pd.DataFrame(dict_)
#remove retweets, which could display sentiment but might not be what we want here
    df_tweets = df_tweets[df_tweets.text.str.contains('RT @')==False]
    return df_tweets

#Now, using the above, pull the tweets into this function to perform a VADER analysis
def comp_tweet():
    df_small = pull_tweet()
    analyzer = SentimentIntensityAnalyzer()
    df_small['scores'] = df_small['text'].apply(lambda x: analyzer.polarity_scores(str(x)))
    sent_attributes = pd.DataFrame.from_dict(df_small['scores'].to_list())
    df_scores =  df_small.merge(sent_attributes, left_index=True, right_index=True)
    df_scores.drop('scores', axis=1, inplace=True)
    return df_scores

#p=0
#while p < 44:
#    dd = comp_tweet()
#    if p == 0:
#        dd2 = dd.copy()
#        dd2['date'] = pd.to_datetime(dd2['date'])
#    dd['date'] = pd.to_datetime(dd['date'])
#    dd2 = pd.concat([dd2, dd], axis=0)
#    dd2.reset_index(inplace=True, drop=True)
#    dd2.drop_duplicates(inplace=True)
#    time.sleep(30)
#    p += 1
    
#pull in data
dd2 = pickle.load(open(r'C:\Users\matfl\tweetsformonitoring.pkl',"rb"))

#order by date
dd2.sort_values(by='date', inplace=True)
#take the relevant variables to track
varls = ['compound', 'pos', 'neg', 'neu']
#for each of these, smooth them with a half life
for i in varls:
    j = i+'2'
    dd2[j] = dd2[i].ewm(halflife = '3 min', times=pd.DatetimeIndex(dd2['date'])).mean()
    
    
# set up plots with bokeh
#set up data
data = dd2.loc[:,['date', 'compound2', 'pos2', 'neg2', 'neu2', 'neg2']]
#the second column will become 'y,' which changes as output.
data.columns = ['date', 'compound', 'pos', 'neg', 'neu', 'y']
source = ColumnDataSource(data=data)
source_static = ColumnDataSource(data=data)
tools = 'pan,wheel_zoom,xbox_select,reset'



stats = PreText(text='', width=500)
select1 = Select(value='neg', options=varls)

#cb = CustomJS(args=dict(source=data.to_dict()), code="""
#    // tell the glyph which field of the source y should refer to
#    var data = source.data
#    var y = data['y']
#    var p = source[cb_obj.value]
#    //change each value
#    for (var i = 0; i < y.length; i++) {
#        y[i] = p[i]
#    }
#
#
#    // manually trigger change event to re-render
#    source.change.emit();
#""")





ts1 = figure(width=900, height=200, tools=tools, x_axis_type='datetime', active_drag="xbox_select")
ts1.line('date', y='y', source=source)
#ts1.circle('date', 'y', size=1, source=source, color=None, selection_color="orange")

callback = CustomJS(args = dict(ts1=ts1), code =
            """                
            ts1.glyph.y = {field: cb_obj.value};
            ts1.change.emit();
            """)

select1.js_on_change('value', callback)



# set up layout
#widgets = column(ticker1, ticker2, stats)
#$main_row = row(corr, widgets)
series = column(ts1) #ts2
layout = column(series, select1) #main row

# initialize
show(layout)
