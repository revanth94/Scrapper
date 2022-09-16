import asyncio

import requests
import json

from pydantic import BaseModel, Field
from collections import defaultdict
from typing import Dict, Optional
from ebooklib import epub
from pymongo import MongoClient


class ChapterInfo(BaseModel):
    chapter_id: int = Field(alias="id")
    book_id: int = Field(alias="orgId")
    chapter_order: int = Field(alias="chapterOrder")
    word_counts: int = Field(alias="wordCounts")
    content: str
    title: str


def get_db(connection_uri="mongodb://root:rootpassword@localhost:27017/", db_name="mydatabase"):
    my_client = MongoClient(connection_uri)
    mydb = my_client[db_name]
    return mydb


def fetch_json(url, params=None):
    response = requests.get(url, params=params)
    return response.json()


class WnmtlScraper:
    CHAPTER_URL = "https://api.mystorywave.com/story-wave-backend/api/v1/content/chapters"
    PAGES_URL = CHAPTER_URL + "/page"

    def get_chapter_url(self, chapter_id):
        return f'{self.CHAPTER_URL}/{chapter_id}', None

    def get_chapter(self, chapter_id):
        print(chapter_id)
        url = f'{self.CHAPTER_URL}/{chapter_id}'
        response = fetch_json(url)
        if response.get("message") == "success":
            return response.get("data")

    @staticmethod
    def get_chapter_ids(file_name):
        with open(file_name, 'r') as f:
            data = json.load(f)
        chapter_ids = [x.get('id') for x in data]
        return chapter_ids

    async def get_chapters_for_book(self, book_id, group_size=100):
        chapter_groups = {}
        page_number = 1
        params = dict(
            sortDirection="ASC",
            bookId=book_id,
            pageNumber=page_number,
            pageSize=group_size
        )
        metadata_response = fetch_json(self.PAGES_URL, params=params)
        total_pages = metadata_response['data']['totalPages']

        for i in range(1, total_pages+1):
            params['pageNumber'] = i
            response_dict = fetch_json(self.PAGES_URL, params)
            if response_dict.get("message") == "success":
                yield dict(group=f'{i*group_size}-{(i+1)*group_size}', chapters=response_dict.get("data").get("list"))
        #     chapter_groups[i] = response_dict
        # return chapter_groups

    @staticmethod
    def write_chapter_to_db(book_id, chapter_data):
        db = get_db(db_name='manga')
        collection = db.get_collection(name=f"{book_id}_chapters")
        collection.insert_one(chapter_data)

    @staticmethod
    def get_chapter_info_collection(book_id):
        return f"{book_id}_chapter_list"

    @staticmethod
    def get_chapters_collection(book_id):
        return f"{book_id}_chapters"

    async def get_and_insert_chapters_ids_for_book(self, book_id):
        db = get_db(db_name='manga')
        collection = db.get_collection(name=self.get_chapter_info_collection(book_id))
        chapter_id_generator = self.get_chapters_for_book(book_id=book_id)
        async for chapter_id_group in chapter_id_generator:
            if chapter_id_group:
                collection.insert_one(chapter_id_group)

    async def get_chapter_info_from_db(self, book_id):
        db = get_db(db_name='manga')
        collection = db.get_collection(name=self.get_chapter_info_collection(book_id))
        db_response = collection.find().sort("group")
        for result in db_response:
            chapters = result['chapters']
            for chapter in chapters:
                yield chapter

    async def get_and_insert_chapters_for_book(self, book_id):
        db = get_db(db_name='manga')
        collection = db.get_collection(name=self.get_chapters_collection(book_id))
        async for chapter in self.get_chapter_info_from_db(book_id):
            chapter_id = chapter['id']
            chapter_data = self.get_chapter(chapter_id)
            if chapter_data:
                collection.insert_one(chapter_data)

    def get_text_for_book(self, book_id):
        def get_bucket(n, s=100):
            q = n//s if n % s else (n//s - 1)
            return f'{q*s}-{(q+1)*s}'
        db = get_db(db_name='manga')
        collection = db.get_collection(name=self.get_chapters_collection(book_id))
        db_response = collection.find().sort("chapterOrder")  # .limit(5)
        book_data = defaultdict(list)
        for result in db_response:
            chapter_order = result.get("chapterOrder")
            heading = result.get("title")
            text = result.get("content")
            formatted_content = f'<h1>{heading}</h1><p>{text}</p>'
            book_data[get_bucket(chapter_order)].append(formatted_content)
        compressed_book_data = {x: "".join(y) for x, y in book_data.items()}
        return compressed_book_data

    @staticmethod
    def compile_book(book_name, book_data):
        book = epub.EpubBook()

        book.set_title(book_name)
        spine = ['nav']
        toc = []
        c1 = epub.EpubHtml(title='Introduction',
                           file_name='intro.xhtml',
                           lang='en')
        c1.set_content(u'<html><body><h1>Introduction</h1><p>Introduction</p></body></html>')

        for title, contents in book_data.items():
            chapter = epub.EpubHtml(title=title, file_name=f'{title}.xhtml', lang='hr')
            chapter.content = contents
            book.add_item(chapter)
            spine.append(chapter)
            toc.append(chapter)
        book.toc = (epub.Link('chap_01.xhtml', 'Introduction', 'intro'),
                    (epub.Section('Chapters'), tuple(x for x in toc)))
        # add default NCX and Nav file
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        # define CSS style
        style = 'BODY {color: white;}'
        nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
        # add CSS file
        book.add_item(nav_css)
        # write to the file
        book.spine = spine
        epub.write_epub(f'{book_name}.epub', book, {})

    def get_chapters_and_compile_book(self, book_id, book_name):
        book_data = self.get_text_for_book(book_id)
        self.compile_book(book_name, book_data)


def main():
    martial_peak_book_id = 2292
    against_the_gods_book_id = 2351
    god_emperor_book_id = 2298
    scraper = WnmtlScraper()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(scraper.get_and_insert_chapters_ids_for_book(against_the_gods_book_id))
        loop.run_until_complete(scraper.get_and_insert_chapters_for_book(against_the_gods_book_id))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
    scraper.get_chapters_and_compile_book(against_the_gods_book_id, "AgainstTheGods")


if __name__ == "__main__":
    main()
    # https://api.mystorywave.com/story-wave-backend/api/v1/content/books/custom/LastUpdatedLocal