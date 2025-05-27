from fastapi import FastAPI
from pydantic import BaseModel
from scripts.query_search import ChromaQueryClient
from scripts.top_similarity import TopSimilarity

class QueryInputs(BaseModel):
    query_text1: str # make sure again the input is string/list
    query_text2: str

app = FastAPI()
client = ChromaQueryClient(host="<vm-ip>", port=8000)
similarity = TopSimilarity()

@app.post("/query/all_collections")
def query_all_collections(request: QueryInputs):
    # query every collection
    df_titles = client.query_job_titles(request.query_text1)
    df_descriptions = client.query_job_descriptions(request.query_text2)
    df_resumes = client.query_resumes(request.query_text2)

    # combine the results with top similarity
    # (only 2 df, still determine `df_resumes` is used for)
    mongo_ids = similarity.weighted_similarity(df_titles, df_descriptions)
    return mongo_ids
