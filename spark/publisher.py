import argparse
import tweepy
import pandas as pd
from utils import get_start_end_time, get_tweets, publish


df = pd.read_csv('/opt/spark/nasdaq_screener.csv')
df_dict = df.to_dict('index')

parser = argparse.ArgumentParser()
parser.add_argument('--input_tweets_topic_name', required=False, default='twitter_topic')
parser.add_argument('--input_nasdaq_topic_name', required=False, default='nasdaq_topic')
args = parser.parse_args()
tweets_topic_name = args.input_tweets_topic_name
nasdaq_topic_name = args.input_nasdaq_topic_name


s,e= get_start_end_time()

for i in range(len(df.index)):
    print(df_dict[i]['Symbol'])       
    get_tweets(df_dict[i]['Symbol'],s,e,tweets_topic_name)
    publish(nasdaq_topic_name,df_dict[i])



