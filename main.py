import os

import openai
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()
from bson import ObjectId
from openai import OpenAI
from src.db import db
from src.schemas import Article, UpdateArticle
from pinecone import Pinecone, ServerlessSpec

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

collection = db["articles"]

def transform_id(article):
    article["_id"] = str(article["_id"])
    return article

def get_article_by_id(id: str):
    article = collection.find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return transform_id(article)

Validated_Article = Depends(get_article_by_id)
# CRUD Endpoints
@app.get("/articles/")
def get_articles():
    articles = list(collection.find({}))
    return [transform_id(article) for article in
            articles]


@app.get("/articles/{id}")
def get_article(id: str):
    article = get_article_by_id(id)
    return article


@app.post("/articles/")
def create_article(article: Article):
    new_article = collection.insert_one(article.model_dump())
    if not new_article.acknowledged:
        raise HTTPException(status_code=500, detail="Failed to create article")
    created_article = get_article_by_id(new_article.inserted_id)
    return created_article


@app.put("/articles/{id}")
def update_article(id: str, article: UpdateArticle):
    update_data = {k: v for k, v in article.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = collection.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    updated_article = get_article_by_id(id)
    return updated_article


@app.delete("/articles/{id}")
def delete_article(id: str):
    result = collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"message": "Article deleted successfully"}


# Summarization Endpoint
openai_api_key = os.getenv("OPENAI_API_KEY", '')
if not openai_api_key:
    raise Exception("OPENAI_API_KEY not set")
client = OpenAI(api_key=openai_api_key)
@app.post("/articles/{id}/summarize")
def summarize_article(id: str):
    article = collection.find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": f'Summarize this article.\n{article["description"]}'
                }
            ]
        )
        summary = response.choices[0].message.content

        return {"summary": summary}
    except:
        raise HTTPException(status_code=500, detail="Failed to summarize article")

# Pinecone Integration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", '')
if not PINECONE_API_KEY:
    raise Exception("PINECONE_API_KEY not set")

pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "articles-index"
try:
    index = pc.Index(index_name)
except:
    # Create the index if it doesn't exist
    index = pc.create_index(
        name=index_name,
        dimension=1024,  # Replace with your model dimensions
        metric="cosine",  # Replace with your model metric
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )



@app.post("/articles/{id}/embed")
def embed_article(id: str):
    article = collection.find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    try:
        response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=article["description"]
        )
        embedding = response["data"][0]["embedding"]
        index.upsert([(id, embedding)])

        return {"message": "Embedding stored successfully"}
    except:
        raise HTTPException(status_code=500, detail="Failed to store embedding")


@app.get("/articles/search")
def search_articles(query: str):
    try:
        response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=query
        )
        query_embedding = response["data"][0]["embedding"]
        results = index.query(query_embedding, top_k=5, include_metadata=True)
        return {"results": results }
    except:
        raise HTTPException(status_code=500, detail="Failed to search articles")

