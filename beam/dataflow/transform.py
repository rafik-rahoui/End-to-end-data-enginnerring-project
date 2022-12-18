import typing
from apache_beam import CombinePerKey
from apache_beam import Map 
import google.auth

import apache_beam as beam
from apache_beam.io.gcp.bigquery import BigQueryDisposition, WriteToBigQuery
from apache_beam.dataframe.convert import to_dataframe, to_pcollection
from apache_beam.runners import DataflowRunner
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax


def predict(tweet):

    tweet_words = []

    for word in tweet.split(' '):
        if word.startswith('@') and len(word) > 1:
            word = '@user'
    
        elif word.startswith('http'):
            word = "http"
        tweet_words.append(word)

    tweet_proc = " ".join(tweet_words)

# load model and tokenizer
    roberta = "cardiffnlp/twitter-roberta-base-sentiment"
    model = AutoModelForSequenceClassification.from_pretrained(roberta)
    tokenizer = AutoTokenizer.from_pretrained(roberta)

    labels = ['Negative', 'Neutral', 'Positive']

# performing sentiment analysis
    encoded_tweet = tokenizer(tweet_proc, return_tensors='pt')

    output = model(**encoded_tweet)

    scores = output[0][0].detach().numpy()
    scores = softmax(scores)
    list=[]
    for i in range(len(scores)):
        l = labels[i]
        s = scores[i]
        list.append((l,s))   
# returning a tuple (a,1) with a indicating the dominant sentiment             
    return  (max(list, key=lambda x: x[1])[0],1)


input_file = "gs://<path-to-parquet-files>/*.parquet"

project = google.auth.default()[1]


bucket = "gs://<path-to-bucket>"
schema_bq = "Symbol:string,Name:string,Market_Cap_B:float,Country:string,Sector:string,Indutry:string,data:string"
table = f"{project}:<dataset_name>.<table_name>"


# bq schema before loading
def prepare(element):
        dictionary = {
           "Symbol": element[0],
           "Name": element[1],
           "Market_Cap_B": round(float(element[2])/1000000000,2),
           "Country": element[3],
           "Sector": element[4],
           "Indutry": element[5],
           "data": element[6]
        }
        return dictionary 


def sentiment_max(element):
    return max(element, key=lambda x: (x[1]))[0]

# getting the sentiment for every tweet in the list    
def infer(func, element):
    return  [func(s) for s in element]

# sub-pipline to perform sentiment analysis    
def count(pcollection):
        return (pcollection 
                | CombinePerKey(sum)
                | beam.combiners.ToList()
                | Map(lambda x : sentiment_max(x)))

class schema_1(typing.NamedTuple):
    Symbol: str
    Name: str
    Market_Cap: float
    Country: str
    Sector: str
    Indutry: str
    data: str

class schema_2(typing.NamedTuple):
    data: str
    
argv = [
'--project={0}'.format(project),
#'--job_name=examplejob3',
'--save_main_session',
'--staging_location={0}/staging/'.format(bucket),
'--temp_location={0}/staging/'.format(bucket),
'--region=us-central1',
'--num_workers=6',
'--requirements_file=./dataflow/requirements.txt',
'--runner=DataflowRunner'
]


with beam.Pipeline(argv=argv) as p1:

    data = (p1 | "read file" >>beam.io.ReadFromParquet(input_file)
               | "schema 1" >> Map(lambda x: x).with_output_types(schema_1))
               
    
    data_prediction = (data   | "data" >> Map(lambda x: x["data"])
                              | "encode1 et" >> Map(lambda x: infer(predict,x))
                              | "decode et" >> Map(lambda x : count(x))
                              |  "schema 2" >> Map(lambda x: x).with_output_types(schema_2))  

    
    df1 = to_dataframe(data)
    df2 = to_dataframe(data_prediction)
    df1["data"] = df2["data"] 
    result = (to_pcollection(df1) |  Map(lambda x: prepare(x)) 
                                  |  WriteToBigQuery(table=table,schema=schema_bq,\
                                      custom_gcs_temp_location="%s/temp" % bucket,\
                                      create_disposition=BigQueryDisposition.CREATE_IF_NEEDED,\
                                      write_disposition=BigQueryDisposition.WRITE_TRUNCATE))     