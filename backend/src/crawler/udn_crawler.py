import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from .exceptions import ParseError, NetworkError

BASE_URL = "https://udn.com/api/more"

def get_news_list(search_term: str, is_initial: bool = False) -> list:
    """獲取新聞列表"""
    try:
        all_news_data = []
        
        if is_initial:
            page_range = range(1, 10)
        else:
            page_range = range(1, 2)
            
        for p in page_range:
            params = {
                "page": p,
                "id": f"search:{quote(search_term)}",
                "channelId": 2,
                "type": "searchword",
            }
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            
            if is_initial:
                all_news_data.extend(response.json()["lists"])
            else:
                all_news_data.extend(response.json()["lists"])

                
        return all_news_data
        
    except requests.RequestException as e:
        raise NetworkError(f"獲取新聞列表失敗: {str(e)}")
    except (KeyError, ValueError) as e:
        raise ParseError(f"解析新聞列表失敗: {str(e)}")

def get_article_content(url: str) -> dict:

    """獲取文章內容"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        title = soup.find("h1", class_="article-content__title")
        if not title:
            raise ParseError("找不到文章標題")
        title = title.text.strip()

        
        time = soup.find("time", class_="article-content__time")
        if not time:
            raise ParseError("找不到文章時間")
        time = time.text.strip()

        
        content_section = soup.find("section", class_="article-content__editor")
        if not content_section:
            raise ParseError("找不到文章內容區塊")
        
        paragraphs = [
            p.text.strip()

            for p in content_section.find_all("p")
            if p.text.strip() != "" and "▪" not in p.text
        ]
        
        content = " ".join(paragraphs)
        
        return {
            "url": url,
            "title": title,
            "time": time,
            "content": content
        }
        
    except requests.RequestException as e:
        raise NetworkError(f"獲取文章內容失敗: {str(e)}")
    except ParseError as e:
        raise e
    except Exception as e:
        raise ParseError(f"解析文章內容失敗: {str(e)}")
