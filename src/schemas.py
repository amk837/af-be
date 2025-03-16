from typing import Optional

from pydantic import BaseModel


class Article(BaseModel):
    title: str
    description: str

class UpdateArticle(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
