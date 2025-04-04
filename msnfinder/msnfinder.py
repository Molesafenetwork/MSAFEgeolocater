import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template
import hashlib
import json
import cv2
import numpy as np
import threading
import time
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from my_spider import MySpider  # Adjust the import based on your project structure

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables for scraping
scraping_active = False
results = []
useful_links = []  # To store useful links for future searches
log_messages = []  # List to store log messages

class ListHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        log_messages.append(log_entry)

# Add the custom handler to capture logs
list_handler = ListHandler()
list_handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(list_handler)

def hash_face(image_path):
    # Hash the face image
    image = cv2.imread(image_path)
    if image is None:
        logging.warning(f"Image not found at path: {image_path}")
        return None
    # Convert image to a hashable format
    return hashlib.sha256(image.tobytes()).hexdigest()

def scrape_data(input_data, mode, match_count=10, min_score=50):
    global results
    results = []
    accuracy_score = 0

    search_engines = {
        'google': 'https://www.google.com/search?q={}',
        'duckduckgo': 'https://duckduckgo.com/?q={}',
    }

    logging.info("Starting scraping process...")
    inputs = input_data.split()  # Split input data into individual pieces

    for input_piece in inputs:
        # Extract relevant keywords instead of full URLs
        keywords = input_piece.split('/')[-1]  # Get the last part of the URL or just use the input piece
        exact_match_query = f'"{keywords}"'  # Create an exact match query
        retry_count = 0
        max_retries = 5  # Set the maximum number of retries

        while scraping_active and retry_count < max_retries:
            for engine, url_template in search_engines.items():
                # Construct the search URL
                search_url = url_template.format(exact_match_query)
                logging.debug(f"Searching {engine} with URL: {search_url}")
                response = requests.get(search_url)

                if response.status_code == 200:
                    logging.info(f"Successfully fetched results from {engine}")
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Example: Extracting data from Google search results
                    if engine == 'google':
                        found_results = False  # Track if any results are found
                        for item in soup.find_all('div', class_='g'):
                            link = item.find('a')['href']
                            title = item.find('h3').get_text(strip=True)
                            score = np.random.randint(0, 101)  # Simulated score; replace with actual scoring logic

                            if score >= min_score:
                                results.append({
                                    'data': title,
                                    'score': score,
                                    'link': link
                                })
                                useful_links.append(link)  # Save useful link
                                accuracy_score += score
                                found_results = True

                    # Example: Extracting data from DuckDuckGo search results
                    elif engine == 'duckduckgo':
                        found_results = False  # Track if any results are found
                        for item in soup.find_all('a', class_='result__a'):
                            link = item['href']
                            title = item.get_text(strip=True)
                            score = np.random.randint(0, 101)  # Simulated score; replace with actual scoring logic

                            if score >= min_score:
                                results.append({
                                    'data': title,
                                    'score': score,
                                    'link': link
                                })
                                useful_links.append(link)  # Save useful link
                                accuracy_score += score
                                found_results = True
                                logging.debug(f"Found result: {title} with score: {score} and link: {link}")

                    if found_results:
                        if mode == 'limited' and len(results) >= match_count:
                            logging.info(f"Reached match count limit: {match_count}")
                            return  # Exit the function if the limit is reached
                        break  # Exit the search engine loop if successful
                    else:
                        logging.warning(f"No valid results found for {input_piece} on {engine}.")
                        retry_count += 1
                        if retry_count >= max_retries:
                            logging.error(f"Max retries reached for {input_piece} on {engine}. Moving to next input.")

                else:
                    logging.error(f"Failed to fetch results from {engine}, status code: {response.status_code}")
                    retry_count += 1
                    logging.warning(f"Retrying {input_piece} on {engine} (Attempt {retry_count}/{max_retries})")
                    if retry_count >= max_retries:
                        logging.error(f"Max retries reached for {input_piece} on {engine}. Moving to next input.")
                        break  # Exit the search engine loop if max retries reached

            time.sleep(1)  # Delay to avoid overwhelming the server

def start_scraping(input_data, mode, match_count=10, min_score=50):
    global scraping_active
    scraping_active = True
    logging.info("Starting scraping thread...")
    threading.Thread(target=scrape_data, args=(input_data, mode, match_count, min_score)).start()

# Function to run the Scrapy spider and collect results
def run_scrapy_spider():
    process = CrawlerProcess(get_project_settings())
    results = []  # List to store results

    # Define a custom item pipeline to collect results
    class CollectResultsPipeline:
        def open_spider(self, spider):
            self.results = []

        def close_spider(self, spider):
            global results
            results = self.results

        def process_item(self, item, spider):
            self.results.append(item)
            return item

    # Add the pipeline to the Scrapy settings
    process.crawl(MySpider, custom_settings={
        'ITEM_PIPELINES': {
            '__main__.CollectResultsPipeline': 1,
        }
    })
    process.start()  # The script will block here until the crawling is finished

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        social_media = request.form.get('social_media')
        phone_number = request.form.get('phone_number')
        email = request.form.get('email')
        name = request.form.get('name')
        address = request.form.get('address')
        mode = request.form.get('mode')
        match_count = int(request.form.get('match_count', 10))
        min_score = int(request.form.get('min_score', 50))

        # Combine input data for searching
        input_data = f"{social_media} {phone_number} {email} {name} {address}".strip()
        
        # Start scraping based on the selected mode
        logging.info("Received POST request to start scraping.")
        start_scraping(input_data, mode, match_count, min_score)

        return render_template('results.html', results=results)  # This may need to be updated later

    return render_template('index.html')

@app.route('/stop', methods=['POST'])
def stop_scraping():
    global scraping_active
    scraping_active = False
    logging.info("Scraping process stopped.")
    return render_template('results.html', results=results)

@app.route('/logs', methods=['GET'])
def view_logs():
    logging.info("Accessed log viewer.")
    return render_template('logs.html', logs=log_messages)

@app.route('/results', methods=['GET'])
def results_page():
    return render_template('results.html', results=results)

@app.route('/export', methods=['GET'])
def export_results():
    # Implement your export logic here
    return "Export functionality not yet implemented."  # Placeholder for export functionality

@app.route('/start_scraping', methods=['POST'])
def start_scraping_route():
    run_scrapy_spider()
    return render_template('results.html', results=results)  # Adjust as needed

if __name__ == '__main__':
    app.run(debug=True)
