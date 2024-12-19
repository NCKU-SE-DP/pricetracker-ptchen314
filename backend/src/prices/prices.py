from fastapi import APIRouter, Query
import requests

router = APIRouter(prefix="/api/v1/prices", tags=["prices"])

@router.get("/necessities-price")
def get_necessities_prices(
    category: str = Query(None),
    commodity: str = Query(None)
):
    """
    從政府開放資料平台獲取民生必需品價格資訊
    
    Args:
        category: 商品類別
        commodity: 商品名稱
        
    Returns:
        JSON 格式的價格資訊
    """
    return requests.get(
        "https://opendata.ey.gov.tw/api/ConsumerProtection/NecessitiesPrice",
        params={"CategoryName": category, "Name": commodity},
    ).json() 