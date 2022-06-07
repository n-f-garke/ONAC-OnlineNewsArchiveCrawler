import sys
from dataclasses import dataclass
import random
import time
import datetime
import nge_datetime
import urllib.parse
import requests
from bs4 import BeautifulSoup
import newspaper
import pandas


class NewsMedium:

    def __init__(self,
                 name: str,
                 archive_page_location: str):
        self.name: str = name
        self.archive_page_location: str = archive_page_location

    def __str__(self):
        return self.name


class Article:

    def __init__(self,
                 publisher: str,
                 url: str,
                 date_of_publication: str,
                 title: str,
                 text: str):
        self.publisher: str = publisher
        self.url: str = url
        self.date_of_publication: str = date_of_publication
        self.title: str = title
        self.text: str = text

    def __str__(self):
        return self.publisher[:3] + " | " + \
               self.date_of_publication + " | " + \
               self.url[:20] + " ... " + \
               self.url[-20:] + " | " + \
               self.title[:20] + " | " + \
               self.text[:40]


def store_articles_to_csv_file(news_articles: [[str, str, str, str]],
                               csv_file_path: str):
    news_articles_data_frame = pandas.DataFrame(news_articles,
                                                columns=["publisher",
                                                         "url",
                                                         "date_of_publication",
                                                         "text"])
    news_articles_data_frame.to_csv(csv_file_path,
                                    index=False)

    print("__ store archive _____________")
    print("____ csv file path ___________: " + csv_file_path)


def load_articles_from_csv_file(csv_file_path: str):
    print("__ load archive ______________")
    print("____ csv file path ___________: " + csv_file_path)

    return


def parse_archive(news_medium: NewsMedium,
                  start_of_period: datetime.date,
                  end_of_period: datetime.date,
                  min_secs_before_request: int,
                  max_secs_before_request: int):
    def print_parameters():
        print("__ retrieve archive __________  ")
        print("____ publisher _______________: " + news_medium.__str__())
        print("____ start_of_period _________: " + start_of_period.strftime(nge_datetime.date.ISO_8601_format))
        print("____ end_of_period ___________: " + end_of_period.strftime(nge_datetime.date.ISO_8601_format))
        print("____ min_secs_before_request _: " + str(min_secs_before_request))
        print("____ max_secs_before_request _: " + str(max_secs_before_request))
        print("______________________________ ")

    def print_archive():
        for archive_page in archive.archive_pages:
            print("____ archive page ____________ ")
            print("______ url ___________________: " + archive_page.url)
            print("______ date __________________: " + archive_page.date)
            print("______ articles ______________ ")
            for article_in_archive in archive_page.articles_in_archive:
                print("________ article _____________: " + article_in_archive.__str__())
            print("______________________________ ")

    @dataclass
    class ArchivePage:
        url: str
        date: str
        articles_in_archive: [Article]

    @dataclass
    class Archive:
        archive_pages: [ArchivePage]

    print_parameters()

    archive: Archive = Archive([])

    # --------------------------------------------------------------------------------------------------------------
    # EXTRACT DATES TO PARSE FROM TIME PERIOD
    # --------------------------------------------------------------------------------------------------------------
    dates_to_parse: [datetime.date] = []
    if "%d" in news_medium.archive_page_location \
            and "%m" in news_medium.archive_page_location \
            or "%-m" in news_medium.archive_page_location \
            and "%Y" in news_medium.archive_page_location:
        dates_to_parse = nge_datetime.date.get_dates_between(start_of_period, end_of_period)

    # --------------------------------------------------------------------------------------------------------------
    # CREATE ARCHIVE PAGE FOR EVERY DATE OF TIME PERIOD
    # --------------------------------------------------------------------------------------------------------------
    for date_to_parse in dates_to_parse:
        archive_page = ArchivePage(
            time.strftime(news_medium.archive_page_location, date_to_parse.timetuple()),
            time.strftime(nge_datetime.date.ISO_8601_format, date_to_parse.timetuple()),
            [],
        )
        archive.archive_pages.append(archive_page)

    @dataclass
    class ArchivePageContent:
        urls_in_archive: [str]
        filtered_urls_in_archive: [str]
        articles_in_archive: [str]
        filtered_articles_in_archive: [str]

    archive_pages_contents = []
    for archive_page in archive.archive_pages:
        archive_pages_contents.append({
            "page": archive_page,
            "content": ArchivePageContent([], [], [], [])
        })

    # --------------------------------------------------------------------------------------------------------------
    # The archive pages are requested and the urls contained in them extracted.
    # --------------------------------------------------------------------------------------------------------------
    for archive_page_content in archive_pages_contents:
        secs_before_request: int = random.randrange(min_secs_before_request, max_secs_before_request)
        time.sleep(secs_before_request)

        response: requests.Response = requests.get(archive_page_content["page"].url)
        response_text: str = response.text

        print("____ archive page download ___: " + archive_page_content["page"].url)

        soup = BeautifulSoup(response_text, "html.parser")
        for a in soup.find_all("a"):
            url: str = urllib.parse.urljoin(archive_page_content["page"].url, a.get("href"))
            parsed_url: urllib.parse.ParseResult = urllib.parse.urlparse(url)
            parsed_url = parsed_url._replace(params="")
            parsed_url = parsed_url._replace(query="")
            parsed_url = parsed_url._replace(fragment="")
            url = parsed_url.geturl()

            if url not in archive_page_content["content"].urls_in_archive:
                archive_page_content["content"].urls_in_archive.append(url)

    # --------------------------------------------------------------------------------------------------------------
    # The article urls are filtered. Every url that appeared more than once is filtered.
    # --------------------------------------------------------------------------------------------------------------
    url_counts: [] = []
    for archive_page_content in archive_pages_contents:
        for url_in_archive in archive_page_content["content"].urls_in_archive:

            contained = False
            for url_count in url_counts:
                if url_count["url"] == url_in_archive:
                    url_count["count"] += 1
                    contained = True

            if not contained:
                url_counts.append({
                    "url": url_in_archive,
                    "count": 1
                })

    for archive_page_content in archive_pages_contents:
        for url_in_archive in archive_page_content["content"].urls_in_archive:

            article = False
            for url_count in url_counts:
                if url_count["url"] == url_in_archive:
                    if url_count["count"] == 1:
                        article = True

            if article:
                archive_page_content["content"].filtered_urls_in_archive.append(url_in_archive)

    # --------------------------------------------------------------------------------------------------------------
    # The article pages are requested and the page content filtered. Only elements that appeared should be kept.
    # --------------------------------------------------------------------------------------------------------------
    for archive_page_content in archive_pages_contents:
        for filtered_url_in_archive in archive_page_content["content"].filtered_urls_in_archive:
            secs_before_request: int = random.randrange(min_secs_before_request, max_secs_before_request)
            time.sleep(secs_before_request)

            try:
                newspaper3k_article = newspaper.Article(filtered_url_in_archive)
                newspaper3k_article.download()
                newspaper3k_article.parse()

                print("________ article download ____: " + filtered_url_in_archive)
                print("__________ article text ______: " + newspaper3k_article.text.replace("\n", " | "))

                article = Article(
                    news_medium.name,
                    filtered_url_in_archive,
                    archive_page_content["page"].date,
                    newspaper3k_article.title,
                    newspaper3k_article.text.replace("\n", " | ")
                )
                archive_page_content["content"].articles_in_archive.append(article)

            except:
                pass

    # --------------------------------------------------------------------------------------------------------------
    # FILTER ARTICLES
    # --------------------------------------------------------------------------------------------------------------
    url_counts = []
    for archive_page_content in archive_pages_contents:
        for article_in_archive in archive_page_content["content"].articles_in_archive:

            contained = False
            for url_count in url_counts:
                if url_count["text"] == article_in_archive.text:
                    url_count["count"] += 1
                    contained = True

            if not contained:
                url_counts.append({
                    "text": article_in_archive.text,
                    "count": 1
                })

    for archive_page_content in archive_pages_contents:
        for article_in_archive in archive_page_content["content"].articles_in_archive:

            article = False
            for url_count in url_counts:
                if url_count["text"] == article_in_archive.text:
                    if url_count["count"] == 1:
                        article = True

            if article:
                archive_page_content["page"].articles_in_archive.append(article_in_archive)

    print_archive()

    news_articles: [[str, str, str, str]] = []

    for archive_page in archive.archive_pages:
        for article_in_archive in archive_page.articles_in_archive:
            news_articles.append([article_in_archive.publisher,
                                  article_in_archive.url,
                                  article_in_archive.date_of_publication,
                                  article_in_archive.text])

    return news_articles


if __name__ == '__main__':
    # python3 main.py nytimes https://www.nytimes.com/sitemap/%Y/%m/%d/ 2022 4 10 2022 4 9
    # python3 main.py nypost https://nypost.com/%Y/%m/%d/ 2022 4 10 2022 4 9

    news_medium_name = sys.argv[1]
    news_medium_archive_url = sys.argv[2]
    date1_year: int = int(sys.argv[3])
    date1_month: int = int(sys.argv[4])
    date1_day: int = int(sys.argv[5])
    date2_year: int = int(sys.argv[6])
    date2_month: int = int(sys.argv[7])
    date2_day: int = int(sys.argv[8])

    # --------------------------------------------------------------------------------------------------------------
    # PARSE NEWS ARTICLES FROM ONLINE NEWS ARCHIVE
    # --------------------------------------------------------------------------------------------------------------

    date1 = datetime.date(date1_year, date1_month, date1_day)
    date2 = datetime.date(date2_year, date2_month, date2_day)
    parse_interval_min = 2
    parse_interval_max = 6

    parsed_news_articles: [[str], [str], [str], [str]] = parse_archive(
        NewsMedium(news_medium_name, news_medium_archive_url),
        date1,
        date2,
        parse_interval_min,
        parse_interval_max
    )

    # --------------------------------------------------------------------------------------------------------------
    # STORE NEWS ARTICLES TO CSV FILE
    # --------------------------------------------------------------------------------------------------------------

    date1_string = date1.strftime(nge_datetime.date.ISO_8601_format)
    date2_string = date2.strftime(nge_datetime.date.ISO_8601_format)
    csv_file_name = "onac_collection-%s_from_%s_to_%s.csv" % (news_medium_name, date1_string, date2_string)
    csv_file_path = "collections/%s" % csv_file_name
    store_articles_to_csv_file(parsed_news_articles, csv_file_path)
