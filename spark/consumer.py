import google.auth
import pyspark
from pyspark.sql import SparkSession
import argparse
from pyspark.sql.types import StructType,StructField, StringType, ArrayType
from utils import subscriber



parser = argparse.ArgumentParser()
parser.add_argument('--input_tweets_topic_name', required=False, default='twitter_topic')
parser.add_argument('--input_nasdaq_topic_name', required=False, default='nasdaq_topic')
args = parser.parse_args()
tweets_topic_name = args.input_tweets_topic_name
nasdaq_topic_name = args.input_nasdaq_topic_name

from pathlib import Path

path = Path.cwd()
par= path.parent 
credentials_location = <path-to-google-credentials-json-file>

spark = SparkSession.builder \
    .master("local[*]") \
    .appName('test') \
    .config("spark.jars", "/opt/spark/lib/gcs-connector-hadoop3-2.2.8.jar") \
    .getOrCreate()
# giving spark access to gs objects
hadoop_conf = spark._jsc.hadoopConfiguration()
hadoop_conf.set("fs.AbstractFileSystem.gs.impl",  "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS")
hadoop_conf.set("fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
hadoop_conf.set("fs.gs.auth.service.account.json.keyfile", credentials_location)
hadoop_conf.set("fs.gs.auth.service.account.enable", "true")

schema = StructType([
  StructField('ticker', StringType(), True),
  StructField('data', ArrayType(
                      StructType([
                        StructField('text', StringType(),True),
                        StructField('edit_history_tweet_ids', StringType(),True),
                        StructField('created_at', StringType(),True),
                        StructField('id', StringType(),True)
    ])  
  ), True)
  ])


##################################
consumer_tweets = subscriber(tweets_topic_name,'groupe1')
consumer_nasdaq = subscriber(nasdaq_topic_name,'groupe2')

list_nasdaq=[]
list_tweets=[]

for message in consumer_tweets:
    list_tweets.append(message.value)


for message in consumer_nasdaq:
    list_nasdaq.append(message.value)

df_tweets= spark.createDataFrame(data=list_tweets, schema=schema)          
df_nasdaq= spark.createDataFrame(list_nasdaq)

df_nasdaq.createOrReplaceTempView('nasdaq')
df_tweets.createOrReplaceTempView('tweets')

df_result = spark.sql("""
SELECT 
    t.ticker as Symbol,
    t.data.text AS data,
    n.Name As Name,
    n.Market_Cap AS Market_Cap,
    n.Country As Country,
    n.Sector As Sector,
    n.Industry As Indutry
FROM
    nasdaq as n, tweets as t
WHERE
    t.ticker == n.Symbol     
ORDER BY
    1, 2
""")


df_result.write.format('parquet').mode('overwrite')\
         .save("gs://<path_to bucket>")

print("done!")   

