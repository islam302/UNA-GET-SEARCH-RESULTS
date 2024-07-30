from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import SearchWordForm
from .models import SearchWord, SearchResult
from ChromeDriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import re
import tkinter as tk
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from PIL import Image, ImageTk
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from io import BytesIO
import xlsxwriter
import logging
import chardet
import datetime
import psutil
import urllib
import requests
import base64
import glob
import sys
import os
import codecs
from urllib.parse import quote, unquote, urlparse
from .serializers import SearchWordSerializer, SearchResultSerializer
from django.views import View


class SearchView(View):

    def get(self, request):
        form = SearchWordForm()
        return render(request, 'search/search.html', {'form': form})

    def post(self, request):
        form = SearchWordForm(request.POST, request.FILES)
        if form.is_valid():
            search_words = form.cleaned_data['word'].split(',')
            time_option = form.cleaned_data['time_option']
            max_results = form.cleaned_data['max_results']
            excluded_domains = [domain.strip() for domain in form.cleaned_data['excluded_domains'].split(',') if
                                domain.strip()]

            all_data = self.main(search_words, time_option, max_results, excluded_domains)

            # Save results to the database
            for data in all_data:
                # Retrieve or create a SearchWord instance
                search_word_instance, created = SearchWord.objects.get_or_create(word=data['Search Word'])

                # Create a SearchResult instance
                SearchResult.objects.create(
                    search_word=search_word_instance,
                    link=data['Link'],
                    link_text=data.get('Link Text', '')
                )

            # Save results to an Excel file
            excel_file = self.save_to_excel(all_data)

            # Create an HTTP response with the Excel file
            response = HttpResponse(excel_file,
                                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="search_results.xlsx"'
            return response

        return render(request, 'search/search.html', {'form': form})

    def start_driver(self):
        self.driver = WebDriver.start_driver(self)
        return self.driver

    def main(self, search_words, time_option, max_results, excluded_domains):
        all_data = []

        try:
            for search_word in search_words:
                found_links_all = []

                # found_links_all.extend(self.search_google(search_word, time_option, max_results))


                found_links_all.extend(self.search_duckduckgo(search_word, time_option, max_results))

                filtered_links = [link for link in found_links_all if
                                  not any(domain in link['link'] for domain in excluded_domains)]

                for link in filtered_links:
                    all_data.append({
                        'Search Word': search_word,
                        'Link': link['link'],
                        'Link Text': link.get('link_text', '')
                    })

        except Exception as e:
            print(f"An error occurred: {e}")
        return all_data

    def search_google(self, word, time_option='anytime', max_results=10):
        found_links = []
        processed_urls = set()
        start = 0

        while len(found_links) < max_results:
            encoded_word = quote(word)
            search_url = f'https://www.google.com/search?q="{encoded_word}"&start={start}'

            if time_option != 'anytime':
                search_url += f"&tbs=qdr:{time_option}"

            try:
                response = requests.get(search_url)
                response.raise_for_status()
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    search_results = soup.find_all("a", href=True)
                    links_found = 0

                    for result in search_results:
                        href = result.get("href")
                        if href and href.startswith("/url?q="):
                            url = href.split("/url?q=")[1].split("&sa=")[0]
                            url = unquote(url)
                            if url not in processed_urls and not url.startswith(
                                    ('data:image', 'javascript', '#', 'https://maps.google.com/',
                                     'https://accounts.google.com/', 'https://www.google.com/preferences',
                                     'https://policies.google.com/', 'https://support.google.com/', '/search?q=')):
                                link_text = result.text.strip()
                                found_links.append({'link': url, 'link_text': link_text})
                                processed_urls.add(url)
                                links_found += 1
                                if len(found_links) >= max_results:
                                    break
                    if links_found == 0:
                        break

                start += 10

            except requests.exceptions.HTTPError as e:
                print(f"HTTP Error occurred: {e}")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break

        return found_links

    def search_duckduckgo(self, word, time_option='anytime', max_results=10):
        found_links = []
        processed_urls = set()

        encoded_word = quote(word)
        search_url = f'https://duckduckgo.com/html/?q="{encoded_word}"'

        if time_option != 'anytime':
            search_url += f"&df={time_option}"
        print(search_url)

        driver = self.start_driver()
        driver.get(search_url)

        while len(found_links) < max_results:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.result__a"))
                )

                links_found = 0
                search_results = driver.find_elements(By.CSS_SELECTOR, "a.result__a")
                for result in search_results:
                    href = result.get_attribute("href")
                    if href and href not in processed_urls:
                        link_text = result.text.strip()
                        found_links.append({'link': href, 'link_text': link_text})
                        processed_urls.add(href)
                        links_found += 1
                        if len(found_links) >= int(max_results):
                            break

                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "a[class='result--more__btn']")
                    next_button.click()
                    time.sleep(random.uniform(1.0, 3.0))
                except NoSuchElementException:
                    print("No more results found. Moving to the next word.")
                    break

                if links_found == 0:
                    print("No new links found in this page. Moving to the next word.")
                    break

            except Exception as e:
                print(e)
                break

        driver.quit()
        return found_links

    def save_to_excel(self, all_data):
        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(all_data)

        # Create a BytesIO object to save the Excel file in memory
        buffer = BytesIO()

        # Write the DataFrame to the buffer
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Search Results')

        buffer.seek(0)
        return buffer.getvalue()

