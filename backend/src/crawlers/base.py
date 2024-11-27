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
    @abc.abstractmethod
    def get_headline(self, search_term: str, page: int | tuple[int, int]) -> list[Headline]:
        pass

    @abc.abstractmethod
    def parse(self, url: AnyHttpUrl | str) -> News:
        pass
