from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from bson import ObjectId
import os
load_dotenv()
from src.db import db
from src.schemas import Article, UpdateArticle

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
# CRUD Endpoints
@app.get("/articles/")
def get_articles():
    articles = list(collection.find({}))
    return [transform_id(article) for article in
            articles]


@app.get("/articles/{id}")
def get_article(id: str):
    article = collection.find_one({"_id": ObjectId(id)})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return transform_id(article)


@app.post("/articles/")
def create_article(article: Article):
    new_article = collection.insert_one(article.model_dump())
    if not new_article.acknowledged:
        raise HTTPException(status_code=500, detail="Failed to create article")
    created_article = collection.find_one({"_id": new_article.inserted_id})
    return transform_id(created_article)


@app.put("/articles/{id}")
def update_article(id: str, article: UpdateArticle):
    update_data = {k: v for k, v in article.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = collection.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    updated_article = collection.find_one({"_id": ObjectId(id)})
    return transform_id(updated_article)


@app.delete("/articles/{id}")
def delete_article(id: str):
    result = collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"message": "Article deleted successfully"}



