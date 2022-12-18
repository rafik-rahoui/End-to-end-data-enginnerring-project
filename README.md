# End-to-end-data-enginnerring-project

The main goal of this project is to move data from source destination though an ELT pipeline, using cutting edge data processing models. The trajectory starts from twitter → to kafka → to a data lake (gs) using Spark. A Beam transformation takes over, before loading the results to BigQuery. Key indicators are then displayed on a dashboard (Looker studio). The whole process is orchestrated by Airflow.

For the purpose of this study, the source is twitter and the main result to display on the dashboard is the sentiment analysis of a list of stocks. The latter consist of a basket of 40 Nasdaq stocks with a Cap above 50m USD (There are only 35 foreign companies respecting such criteria, so I added 5 US companies to complete the list). The final dashboard is presented here:
