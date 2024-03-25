from typing import List


class BookList:
    def __init__(
        self,
        thumbnail: str,
        title: str,
        authors: List[str],
        publisher: str,
        translators: List[str],
        poll_count: int,
        isbn: str,
        **kwargs
    ):
        self.cover = thumbnail
        self.title = title
        self.author_list = authors
        self.publisher = publisher
        self.translator_list = translators
        self.poll_count = poll_count
        
        isbn_list = isbn.split(' ')
        if len(isbn_list) == 2:
            isbn = isbn_list[0] if len(isbn_list[0]) == 13 else isbn_list[1]
        self.isbn = isbn
