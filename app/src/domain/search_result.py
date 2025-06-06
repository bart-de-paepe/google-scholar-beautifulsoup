from app.src.domain.common.entity import Entity
from app.src.domain.link import Link


class SearchResult(Entity):
    def __init__(self, title, author, publisher, date, text, link, media_type = ""):
        self.title = title
        self.author = author
        self.publisher = publisher
        self.date = None
        self.set_date(date)
        self.text = text
        self.link = Link(url=link)
        self.media_type = media_type
        self.log_message = ''
        self.is_processed = False
        super().__init__()

    def set_date(self, date):
        if date is not None and date.isnumeric():
            self.date = date
