from scripts.mongo_ingestion import MongoDBClient
from scripts.chroma_connection import ChromaDBClient
from scripts.text_preprocessor import TextPreprocessor
from scripts.top_similarity import TopSimilarity
from scripts.config import MONGO_URI, DB_NAME
import logging
import pandas as pd


with MongoDBClient(mongo_uri=MONGO_URI, dbname=DB_NAME) as client:
    if client.ping():
        collection = client.get_collection('jobs')
        docs = client.find('jobs', projection={'_id': 1, 'jobPosition': 1, 'jobDescList': 1, 'jobQualificationsList': 1}, limit=10)

df = pd.DataFrame(docs)
print(f"DataFrame: {df}")


text_preprocessor = TextPreprocessor()
ids = text_preprocessor.create_id_list(df)
job_titles = text_preprocessor.create_job_title_list(df)
job_texts = text_preprocessor.create_job_texts(df)


# for job titles
print("Connecting to ChromaDB...")
job_titles_client = ChromaDBClient(collection_name="job_titles")
print("Adding job titles to ChromaDB...")
job_titles_client.add_texts(ids=ids, texts=job_titles)
df1 = job_titles_client.query("backend", n_results=len(job_titles))
peek, count = job_titles_client.preview_collection()
print(f"Collection Count: {count}")

# for job descriptions and requirements
job_desc_requirements_client = ChromaDBClient(collection_name="jobdesk_requirements")
print("Adding jobdesk+requirements to ChromaDB...")
job_desc_requirements_client.add_texts(ids=ids, texts=job_texts)
df2 = job_desc_requirements_client.query("backend", n_results=len(job_texts))

top_similarity = TopSimilarity()
print("Calculating top similarity...")
similarity_ids = top_similarity.weighted_similarity(df1, df2)
print(f"Top Similarity IDs: {similarity_ids}")
