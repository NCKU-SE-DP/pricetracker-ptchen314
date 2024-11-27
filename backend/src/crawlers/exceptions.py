class DomainMismatchException(Exception):
    """Raised when URL domain doesn't match the crawler's domain"""
    def __init__(self, url: str):
        self.url = url
        self.message = f"URL domain {url} doesn't match crawler's domain"
        super().__init__(self.message) 