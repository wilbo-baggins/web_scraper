import requests
import time
import datetime
import tarfile
import os
import undetected_chromedriver.v2 as uc
from bs4 import BeautifulSoup
from io import StringIO, BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import concurrent.futures
import threading
from fake_useragent import UserAgent


# uncomment if using a proxy for low-level scrape requests
# proxyDict = {"http": "http_proxy_ip","https": "https_proxy_ip"}

# uncomment if using a proxy for high-level scrape requests
# p = 'selenium_proxy_ip'

# uncomment if running secure traffic through proxy
# verify_certificate = 'name_and_path_of_proxy_cert'
base_urls = [{urls_to_be_scraped}]
manifest = []

def create_directories():
	root_path = os.getcwd()
	directories = ["final_manifest", "url_lists"]
	for folder in directories:
		path = os.path.join(root_path, folder)
		if not os.path.exists(path):
			os.mkdir(path)

def scrape_dealership(retailer_id):
	final_cars_list = []
	for base_url in base_urls:
		chrome_options = Options()
		chrome_options.add_argument('--headless')
		chrome_options.add_argument('ignore-certificate-errors')
		chrome_options.add_argument('--disable-web-security')
		# chrome_options.add_argument('--disable-site-isolation-trials')
		# use this argument if you need to spoof your user agent string, modify string for your desired user agent
		# chrome_options.add_argument('--user-agent=%s' % "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36")
		chrome_options.add_argument('--proxy-server=%s' % p)
		# chrome_options.add_experimental_option('excludeSwitches',['enable-logging'])
		scraper = uc.Chrome(options=chrome_options)
		scraper.get(base_url+retailer_id)

		# Uncomment this block of code if it's the first time you've run the script and it just dies.  
		# There's a prompt about accepting cookies.  I tried using an if statement, but I think it fails due to the find_element function.	
		
		# time.sleep(8)
		# scraper.execute_script('''return document.querySelector('div#usercentrics-root').shadowRoot.querySelector('button[data-testid="uc-accept-all-button"]')''').click()

		while True:
			time.sleep(12)
			try:
				unique_cars = scraper.find_elements(By.CLASS_NAME, value='vehicleItem__image')
				base_images = scraper.find_elements(By.CLASS_NAME, value='image')
				for car in unique_cars:
					soup = car.get_attribute('href')
					if soup not in final_cars_list:
						final_cars_list.append(soup)
				for image in base_images:
					soup = image.find_element(By.TAG_NAME, value='img')
					img_url = soup.get_attribute('src')
					manifest.append(f'<a href="{img_url}">link</a>')
				# count_tab = scraper.find_element(By.CLASS_NAME, value='vehicleTypeTab__totalCars')
				# count = count_tab.find_element(By.XPATH, value='//*[@id="__layout"]/div/main/section/section/div[1]/header/div[1]/div/div/h1')
				# count_text = count.text.split(' ')
				# print(count_text[0])

				next_button = scraper.find_element(By.CLASS_NAME, value='pagination__next')
				next_button.click()
			except Exception as e:
				break

	with open(f'url_lists/{retailer_id}', mode='a+', encoding='utf-8') as f:
		f.write('\n'.join(final_cars_list))
		scraper.quit()

def low_level_scrape(retailer_id):
	with open(f'url_lists/{retailer_id}', mode='r', encoding='utf-8') as f:
		urls = f.readlines()
		session = requests.Session()
		for url in urls:
			scrape_individual_car(url, session)


def scrape_individual_car(url, session):
	page = session.get(url, proxies=proxyDict, verify=verify_certificate)
	soup = BeautifulSoup(page.text, 'html.parser')
	temp_list = soup.find_all(class_="galleryImage")
	for item in temp_list:
		img_url = item.img.get('data-url')
		img_manifest_string = f'<a href="{img_url}">link</a>'
		manifest.append(img_manifest_string)


def top_scrape_threads(retailer_ids):
	# Iterates through the retailer_ids list, and calls scrape_dealership once per retailer, passing the individual retailer_id as a parameter when the scrape_dealership function is called
	# When one scraper finishes, the thread used for that scraper is reassigned to a new one, using a max number of threads specified
	with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
		executor.map(scrape_dealership, retailer_ids)


def low_scrape_threads(retailer_ids):
	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		executor.map(low_level_scrape, retailer_ids)


if __name__ == "__main__":
	retailer_ids = [retailer_ids_to_build_url]
	start_time = time.time()
	start_time_readable = time.strftime('%H:%M %Z')
	day_full = datetime.datetime.now()
	day = day_full.strftime("%Y-%m-%d")
	print(f"Script started at: {start_time_readable}")
	create_directories()
	top_scrape_threads(retailer_ids)
	low_scrape_threads(retailer_ids)

	with open(f'final_manifest/manifest-{day}.html', mode='a', encoding='utf-8') as f2:
		f2.write("<html><head></head><body>\n")
		f2.write('\n'.join(manifest))
		f2.write("\n</body></html>")


	with tarfile.open('final_manifest/all_manifests.tar', 'x') as tar:
		tar.add(f'final_manifest/manifest-{day}.html')


	end_time = time.time()
	end_time_readable = time.strftime('%H:%M %Z')
	duration = (end_time - start_time)
	duration_minutes = duration // 60
	print(f"Script finished at {end_time_readable} with a run duration of {duration_minutes} minutes.")



