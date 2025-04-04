# my_scrapy_project/my_scrapy_project/spiders/my_spider.py
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from bs4 import BeautifulSoup

class MySpider(scrapy.Spider):
    name = "my_spider"
    start_urls = [
        'https://example.com',  # Replace with the target URL or dynamically set this
    ]

    def parse(self, response):
        # Use BeautifulSoup to parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract data using BeautifulSoup
        for item in soup.find_all('div', class_='item'):  # Adjust the selector as needed
            title = item.find('h2').get_text(strip=True)
            link = item.find('a')['href']
            score = 100  # Placeholder for score; implement your scoring logic

            yield {
                'data': title,
                'link': link,
                'score': score
            }

        # Follow pagination links (if applicable)
        next_page = soup.find('a', class_='next')
        if next_page and 'href' in next_page.attrs:
            yield response.follow(next_page['href'], self.parse)

        # Follow links to other relevant pages
        for result in soup.find_all('a', href=True):
            if self.is_relevant_link(result['href']):
                yield response.follow(result['href'], self.parse_detail)

    def parse_detail(self, response):
        # Extract detailed information from the linked page
        soup = BeautifulSoup(response.text, 'html.parser')
        # Implement your logic to extract relevant data from the detail page
        detail_data = soup.find('div', class_='detail')  # Adjust the selector as needed
        if detail_data:
            title = detail_data.find('h1').get_text(strip=True)
            content = detail_data.get_text(strip=True)
            yield {
                'data': title,
                'content': content,
                'link': response.url,
                'score': 100  # Placeholder for score; implement your scoring logic
            }

    def is_relevant_link(self, url):
        # Implement logic to determine if the link is relevant
        # For example, check if the URL contains certain keywords
        return 'instagram.com' in url or 'profile' in url  # Adjust as needed

# Function to run the Scrapy spider
def run_scrapy_spider():
    process = CrawlerProcess(get_project_settings())
    process.crawl(MySpider)
    process.start()  # The script will block here until the crawling is finished