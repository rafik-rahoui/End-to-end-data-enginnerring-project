from datetime import datetime 

from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash import BashOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator


# DAG default arguments  
default_args = {
    "owner": "me",
    "schedule_interval": "0 6 2 * *",
    "start_date" : datetime(2022, 12,16),
    "end_date" : datetime(2022, 12, 16),
    "start_date": days_ago(1),
    #"depends_on_past": False,
    "retries": 1,
}

# DAG declaration 
with DAG(
    dag_id="twitter_sentiment_analysis",
    schedule_interval="@daily",
    default_args=default_args,
    catchup=True,
    max_active_runs=1,
    tags=['tweetss'],
) as dag:
    # python script to publish tweets  and stocks info into kafka topics
    fetch_tweets_task = BashOperator(
        task_id="fetch_tweets_task",
        bash_command=f"docker exec spark_master python /opt/spark/publisher.py"
    )
    # pyspark script to consume data from kafka topics
    store_gcs_task = BashOperator(
        task_id="store_gcs_task",
        bash_command=f"docker exec spark_master python /opt/spark/consumer.py"
    )
    # beam script to tranform data 
    gcs_to_bq_task = BashOperator(
        task_id="gcs_to_bq_task",
        bash_command=f"docker exec dataflow python /opt/dataflow/dataflow/transform.py"
    )   
    # query to encich the initial table 
    CREATE_BQ_TBL_QUERY = (
            f"CREATE OR REPLACE TABLE <project ID>.<dataset_name>.<scores_table_name> \
            AS \
            SELECT *, \
              CASE data \
                WHEN 'Positive' THEN 1 \
                WHEN 'Neutral' THEN 0 \
                ELSE -1\
                END\
                AS score\
            FROM <project ID>.<dataset_name>.<table_name>\
            ORDER BY score desc;"
        )

        # Create a table from the query
    bq_create_table_task = BigQueryInsertJobOperator(
            task_id=f"bq_create_table_task",
            configuration={
                "query": {
                    "query": CREATE_BQ_TBL_QUERY,
                    "useLegacySql": False,
                }
            }
        )    
        # python script to generate a view 
    create_bq_view_task = BashOperator(
        task_id="create_bq_view_task",
        bash_command=f"docker exec spark_master python /opt/spark/bigquery.py"
    )
        # the order in which the tasks should be executed
    fetch_tweets_task >> store_gcs_task >> gcs_to_bq_task \
    >> bq_create_table_task >> create_bq_view_task