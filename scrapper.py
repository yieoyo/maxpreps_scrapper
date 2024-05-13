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

chrome_options = Options()
chrome_options.add_argument("--headless")


driver = webdriver.Chrome(options=chrome_options)


driver.get("https://www.maxpreps.com/baseball/stat-leaders/strikeouts/k/?classyear=11")  


userurls = []
userinfo = []

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

def writefile(pagenumber, my_dict):
    try:
        current_directory = os.getcwd()
        file_path = os.path.join(current_directory, 'data', f'{pagenumber}.txt')
        with open(file_path, 'w') as file:
            json.dump(my_dict, file, indent=4)
        print(f"File '{file_path}' created successfully.")
    except Exception as e:
        print(f"Error occurred: {e}")
print(userurls)
sys.exit(0)
for count, userurl in enumerate(userurls):
        retry_count = 5
        for _ in range(retry_count):
            try:
                response = requests.get(userurl)
                soup = BeautifulSoup(response.content, "html.parser")
                name = soup.find("a", {"class": "athlete-name"}).get_text()
                twitter_script = soup.find("script", {"id": "__NEXT_DATA__"}).get_text()
                twitter_script = json.loads(twitter_script)
                twitter_id = twitter_script['props']['pageProps']['careerContext']['careerData']['twitterHandle']
                if twitter_id:
                    twitter_url = 'https://twitter.com/' + twitter_id
                    userinfo.append({'Name': name,'URL':userurl, 'Twitter': twitter_url})
                    print('Player: ' + str(count) + ' URL: ' + userurl+ ' Twitter: ' + twitter_url)
                else:
                    print('User: ' + str(count) + ' No twitter User: ' + userurl)
                break
            except Exception as e:
                print(f"Error occurred, retrying for url: {userurl} {e}")
                time.sleep(2)
if len(userinfo) > 0:
    writefile(1,userinfo)
