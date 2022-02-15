from fastapi import APIRouter, HTTPException, Request, Response, status

from eager_cache.fetchers.abstract_fetcher import AbstractFetcher

router = APIRouter()
fetchers = {klass.data_type: klass for klass in AbstractFetcher.__subclasses__()}


@router.get("/{data_type}/")
async def api_data(data_type: str, request: Request) -> Response:
    """
    Route for fetching api data.

    :param data_type: Data type to fetch
    :param request: The request object, used for getting query params.

    :raises HTTPException: If the data_type was not found, 404 is returned.
    :return: Response
    """
    if data_type not in fetchers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fetcher for data type {data_type} not found",
        )
    return fetchers[data_type].fetch(**request.query_params)
