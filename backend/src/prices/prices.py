from fastapi import APIRouter, Query, HTTPException
import requests
import logging

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
        response = requests.get(
            "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
            params={"CategoryName": category, "Name": commodity},
        )
        response.raise_for_status()
        data = response.json()
        logger.info("Successfully fetched price data")
        return data
    except requests.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="無法連接到價格資料服務"
        )
    except Exception as e:
        logger.error(f"Error fetching prices: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="獲取價格資料時發生錯誤"
        ) 