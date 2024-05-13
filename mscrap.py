import json
import os
import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import threading

chrome_options = Options()
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(options=chrome_options)

driver.get("https://www.maxpreps.com/baseball/stat-leaders/strikeouts/k/?classyear=11")

userurls = []
userinfo = []
lock = threading.Lock()

while True:
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    name_links = soup.find_all('a', class_='name')
    for link in name_links:
        userurls.append(link['href'].replace("baseball/stats/", ""))

    controls = driver.find_elements(By.CSS_SELECTOR, ".controls > button")

    if len(controls) > 1:
        next_button = controls[len(controls) - 2]
        if next_button.get_attribute("disabled"):
            break
        driver.execute_script("arguments[0].click();", next_button)
    else:
        break

driver.quit()

def fetch_data(urls, start, end):
    local_userinfo = []
    for count, userurl in enumerate(urls[start:end]):
        usernumber = count + start
        retry_count = 5
        for _ in range(retry_count):
            try:
                response = requests.get(userurl)
                soup = BeautifulSoup(response.content, "html.parser")
                name = soup.find("a", {"class": "athlete-name"}).get_text()
                city = soup.find("a", {"class": "school-name"}).get_text()
                # Assuming soup contains the parsed HTML
                hwidth = soup.find(class_='followers').find_next_sibling()
                hwidth = hwidth.find_next_sibling().get_text()
                hwidth = hwidth.split('•')
                height = hwidth[0].strip()
                width = hwidth[1].strip()

                twitter_script = soup.find("script", {"id": "__NEXT_DATA__"}).get_text()
                twitter_script = json.loads(twitter_script)
                twitter_id = twitter_script['props']['pageProps']['careerContext']['careerData']['twitterHandle']
                if twitter_id:
                    twitter_url = 'https://twitter.com/' + twitter_id
                    local_userinfo.append({'Name': name, 'URL': userurl, 'Twitter': twitter_url, 'City': city, 'Height': height, 'Width': width})
                    print('Player: ' + str(count) + ' URL: ' + userurl+ ' Twitter: ' + twitter_url+ ' City: ' + city+ ' Height: ' + height+ ' Width: ' + width)
                    # sys.exit(0)
                else:
                    print('User: ' + str(count) + ' No twitter User: ' + userurl)
                break
            except Exception as e:
                print(f"Error occurred, retrying for url: {userurl} {e}")
                time.sleep(2)
    with lock:
        userinfo.extend(local_userinfo)

# Define the number of threads you want to use
num_threads = 100
chunk_size = len(userurls) // num_threads

threads = []
for i in range(num_threads):
    start = i * chunk_size
    end = start + chunk_size if i < num_threads - 1 else len(userurls)
    thread = threading.Thread(target=fetch_data, args=(userurls, start, end))
    thread.start()
    threads.append(thread)

# Wait for all threads to finish
for thread in threads:
    thread.join()

def writefile(my_dict):
    try:
        current_directory = os.getcwd()
        file_path = os.path.join(current_directory, 'data', 'userinfo.txt')
        with open(file_path, 'w') as file:
            json.dump(my_dict, file, indent=4)
        print(f"File '{file_path}' created successfully.")
    except Exception as e:
        print(f"Error occurred: {e}")

writefile(userinfo)
