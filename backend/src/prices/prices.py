from fastapi import APIRouter, Query, HTTPException
import requests
import logging
from fastapi.responses import JSONResponse
from fastapi import status


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/prices", tags=["prices"])

@router.get("/necessities-price")
def get_necessities_prices(
    category: str = Query(None),
    commodity: str = Query(None)
):
    """從政府開放資料平台獲取民生必需品價格資訊"""
    try:
        logger.info(f"Fetching prices for category: {category}, commodity: {commodity}")
        
        try:
            response = requests.get(
                "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
                params={"CategoryName": category, "Name": commodity},
            )
            response.raise_for_status()
        except requests.ConnectionError as conn_err:
            logger.error(f"Connection error: {str(conn_err)}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "error",
                    "message": "無法連接到價格資料服務",
                    "detail": "連線失敗"
                }
            )
        except requests.Timeout as timeout_err:
            logger.error(f"Timeout error: {str(timeout_err)}")
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "status": "error",
                    "message": "請求超時",
                    "detail": str(timeout_err)
                }
            )
        except requests.RequestException as req_err:
            logger.error(f"Request error: {str(req_err)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "message": "請求失敗",
                    "detail": str(req_err)
                }
            )

        try:
            data = response.json()
        except ValueError as json_err:
            logger.error(f"JSON parsing error: {str(json_err)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "message": "解析回應資料失敗",
                    "detail": str(json_err)
                }
            )

        logger.info("Successfully fetched price data")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": data
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "獲取價格資料時發生未預期的錯誤",
                "detail": str(e)
            }

        ) 