from datetime import datetime, timedelta
import configparser
import tweepy
from kafka import KafkaProducer, KafkaConsumer
from json import dumps,loads


def get_start_end_time():
        dtformat = '%Y-%m-%dT%H:%M:%SZ'

        time = datetime.utcnow()
        start_time = time - timedelta(days=1)
        end_time = time - timedelta(seconds=30)
#datetime.strptime("2022-12-11T10:00:00Z"
        return [start_time.strftime(dtformat), end_time.strftime(dtformat)]


#fetch tweets function
def get_tweets(stock,start,end,topic_name):

        config = configparser.ConfigParser()
        config.read('path to config.ini')

        client = tweepy.Client(bearer_token=config['tweets']['bearer'],return_type=dict)

        response = client.search_recent_tweets(query=f'{stock} lang:en -is:reply -is:retweet',
                        max_results=10,
                        start_time=start,
                        end_time=end, 
                        tweet_fields=['created_at']
                        )
                 
        publish(topic_name,{"ticker":stock, "data":response['data']})
                         
        return print(f"Publishing {stock} is done!")


def publish(topic_name,value):

        producer = KafkaProducer(bootstrap_servers=['kafka'], value_serializer=lambda x: dumps(x).encode('utf-8'))
        producer.send(topic_name, value=value)
        producer.flush()

def subscriber(topic_name,groupe):
        consumer = KafkaConsumer(
                topic_name,
                bootstrap_servers=['kafka'],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id=groupe,
                consumer_timeout_ms=500,
                value_deserializer=lambda x: loads(x.decode('utf-8')))
        return consumer