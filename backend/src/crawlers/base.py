import abc
from pydantic import AnyHttpUrl
from tldextract import tldextract
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

class Headline(BaseModel):
    title: str = Field(
        default=...,
        example="Title of the article",
        description="The title of the article"
    )
    url: AnyHttpUrl | str = Field(
        default=...,
        example="https://www.example.com",
        description="The URL of the article"
    )

class News(Headline):
    time: str = Field(
        default=...,
        example="2021-10-01T00:00:00",
        description="The time the article was published"
    )
    content: str = Field(
        default=...,
        example="Content of the article",
        description="The content of the article"
    )

class NewsCrawlerBase(metaclass=abc.ABCMeta):
    news_website_url: AnyHttpUrl | str
    news_website_news_child_urls: list[AnyHttpUrl | str]

    @abc.abstractmethod
    async def get_headline(
            self, search_term: str, page: int | tuple[int, int]
    ) -> list[Headline]:
        """Get news headlines from the website"""
        pass

    @abc.abstractmethod
    async def parse(self, url: AnyHttpUrl | str) -> News:
        """Parse news content from the given URL"""
        pass

    @staticmethod
    @abc.abstractmethod
    def save(news: News, db: Session | None):
        """Save news to database"""
        pass

    def _is_valid_url(self, url: AnyHttpUrl | str) -> bool:
        """Check if URL belongs to the news website"""
        main_domain = tldextract.extract(self.news_website_url).registered_domain
        url_domain = tldextract.extract(str(url)).registered_domain
        return url_domain == main_domain
