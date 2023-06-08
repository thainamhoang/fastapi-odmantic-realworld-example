from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends
from odmantic import AIOEngine

from core.article import (
    add_article_to_favorite,
    build_get_articles_query,
    build_get_feed_articles_query,
    ensure_is_author,
    get_article_by_slug,
    get_multiple_articles_response,
    remove_article_from_favorites,
)
from models.article import ArticleModel
from models.user import UserModel
from schemas.article import (
    MultipleArticlesResponse,
    NewArticle,
    SingleArticleResponse,
    UpdateArticle,
)
from settings import EngineD
from utils.security import get_current_user_instance, get_current_user_optional_instance

router = APIRouter()


@router.get("/articles", response_model=MultipleArticlesResponse)
async def get_articles(
    author: str = None,
    favorited: str = None,
    tag: str = None,
    limit: int = 20,
    offset: int = 0,
    user_instance: Optional[UserModel] = Depends(get_current_user_optional_instance),
    engine: AIOEngine = EngineD,
):
    query = await build_get_articles_query(engine, author, favorited, tag)
    if query is None:
        return MultipleArticlesResponse(articles=[], articles_count=0)
    response = await get_multiple_articles_response(
        engine, user_instance, query, limit, offset
    )
    return response


@router.get("/articles/feed", response_model=MultipleArticlesResponse)
async def get_feed_articles(
    limit: int = 20,
    offset: int = 0,
    user_instance: UserModel = Depends(get_current_user_instance),
    engine: AIOEngine = EngineD,
):
    query = build_get_feed_articles_query(user_instance)
    response = await get_multiple_articles_response(
        engine, user_instance, query, limit, offset
    )
    return response


@router.post("/articles", response_model=SingleArticleResponse)
async def create_article(
    new_article: NewArticle = Body(..., embed=True, alias="article"),
    user_instance: UserModel = Depends(get_current_user_instance),
    engine: AIOEngine = EngineD,
):
    print(new_article.tag_list)
    article = ArticleModel(author=user_instance, **new_article.dict())
    article.tag_list.sort()
    await engine.save(article)
    return SingleArticleResponse.from_article_instance(article, user_instance)


@router.get("/articles/{slug}", response_model=SingleArticleResponse)
async def get_single_article(
    slug: str,
    engine: AIOEngine = EngineD,
    user_instance: Optional[UserModel] = Depends(get_current_user_optional_instance),
):
    article = await get_article_by_slug(engine, slug)
    return SingleArticleResponse.from_article_instance(article, user_instance)


@router.put("/articles/{slug}", response_model=SingleArticleResponse)
async def update_article(
    slug: str,
    update_data: UpdateArticle = Body(..., embed=True, alias="article"),
    current_user: UserModel = Depends(get_current_user_instance),
    engine: AIOEngine = EngineD,
):
    article = await get_article_by_slug(engine, slug)
    ensure_is_author(current_user, article)

    patch_dict = update_data.dict(exclude_unset=True)
    for name, value in patch_dict.items():
        setattr(article, name, value)
    article.updated_at = datetime.utcnow()
    await engine.save(article)
    return SingleArticleResponse.from_article_instance(article, current_user)


@router.delete("/articles/{slug}")
async def delete_article(
    slug: str,
    current_user: UserModel = Depends(get_current_user_instance),
    engine: AIOEngine = EngineD,
):
    article = await get_article_by_slug(engine, slug)
    ensure_is_author(current_user, article)
    await engine.delete(article)


@router.post("/articles/{slug}/favorite", response_model=SingleArticleResponse)
async def favorite_article(
    slug: str,
    current_user: UserModel = Depends(get_current_user_instance),
    engine: AIOEngine = EngineD,
):
    article = await get_article_by_slug(engine, slug)
    await add_article_to_favorite(engine, user=current_user, article=article)
    return SingleArticleResponse.from_article_instance(article, current_user)


@router.delete("/articles/{slug}/favorite", response_model=SingleArticleResponse)
async def unfavorite_article(
    slug: str,
    current_user: UserModel = Depends(get_current_user_instance),
    engine: AIOEngine = EngineD,
):
    article = await get_article_by_slug(engine, slug)
    await remove_article_from_favorites(engine, user=current_user, article=article)
    return SingleArticleResponse.from_article_instance(article, current_user)
