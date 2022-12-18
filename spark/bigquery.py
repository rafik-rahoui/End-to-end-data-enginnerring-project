from google.cloud import bigquery
import google.auth



bigquery_client = bigquery.Client()

project = google.auth.default()[1]

i=10

view_id = "{0}.<dataset_name>.<view_name>".format(project)
base_table_id = "{0}.<dataset_name>.<table_name>".format(project)
view = bigquery.Table(view_id)
view.view_query = f"""
SELECT * FROM
	(SELECT *, ROW_NUMBER () OVER (ORDER BY score desc) R FROM `<table name>`)
	
"""

# Make an API request to create the view.
bigquery_client.delete_table(view, not_found_ok=True) 
view = bigquery_client.create_table(view)
print(f"Created {view.table_type}: {str(view.reference)}")