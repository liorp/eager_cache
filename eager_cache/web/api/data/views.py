from aioredis import Redis
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from eager_cache.fetchers import *
from eager_cache.services.redis.dependency import get_redis_connection

router = APIRouter()
fetchers = {klass.data_type: klass for klass in AbstractFetcher.__subclasses__()}


@router.get("/{data_type}/")
async def api_data(
    data_type: str,
    request: Request,
    redis: Redis = Depends(get_redis_connection),
) -> Response:
    """
    Route for fetching api data.

    :param data_type: Data type to fetch.
    :param request: The request object, used for getting query params.
    :param redis: The redis object used to manage cache.

    :raises HTTPException: If the data_type was not found, 404 is returned.
    :return: Response
    """
    if data_type not in fetchers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fetcher for data type {data_type} not found",
        )
    result = await fetchers[data_type].fetch(redis, **request.query_params)
    return JSONResponse(jsonable_encoder(result))
