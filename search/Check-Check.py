from tkinter import Tk, ttk, filedialog, simpledialog, messagebox, Button, Label, PhotoImage, Frame, font, Entry, Canvas, NW
from bs4 import BeautifulSoup
import time
import random
import ttkbootstrap as TTK
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


class SearchAboutNews(Tk):

    def __init__(self):
        super().__init__()

        self.include_iframe_var = tk.BooleanVar()
        self.include_iframe_var.set(True)
        self.title("Searching Links Extractor")
        self.geometry("600x900")
        self.configure(bg="#282828")
        self.style = TTK.Style()
        self.style.theme_use("darkly")
        self.style.configure('TButton', background='blue', foreground='white')

        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ]

        self.driver = None
        self.current_dir = os.path.dirname(sys.argv[0])
        self.results_folder = os.path.join(self.current_dir, 'RESULTS')
        os.makedirs(self.results_folder, exist_ok=True)

        self.templates = []
        self.create_widgets()

    def create_widgets(self):
        # Set logo as window background
        current_dir = os.path.dirname(sys.argv[0])
        logo_files = glob.glob(os.path.join(current_dir, "logo.*"))
        if logo_files:
            logo_path = logo_files[0]
            try:
                logo_image = Image.open(logo_path)
                logo_image = logo_image.resize((600, 900), Image.LANCZOS)
                self.background_image = ImageTk.PhotoImage(logo_image)
                bg_label = tk.Label(self, image=self.background_image)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            except Exception as e:
                print(f"Error loading image: {e}")
                messagebox.showerror("Error", "Failed to load logo image")

        # Main window properties
        self.title("Searching Links Extractor")
        self.geometry("600x900")
        self.configure(bg="#282828")

        custom_font = font.Font(family="Helvetica", size=14, weight="bold")

        btn_style = {
            'bg': '#006400',
            'fg': 'white',
            'padx': 20,
            'pady': 10,
            'bd': 0,
            'borderwidth': 0,
            'highlightthickness': 0,
            'font': custom_font
        }

        self.task2_button = tk.Button(self, text='Run Searching TASK', command=self.execute_task, **btn_style)
        self.task2_button.pack(pady=(200, 10))  # Adjust pady to move the button down

        self.template_frame = tk.Frame(self, bg='#282828')
        self.template_frame.pack(pady=4)

        self.template_entries = []
        self.add_template_entry()

        add_template_button = tk.Button(self, text='+', command=self.add_template_entry, **btn_style)
        add_template_button.pack(pady=4)

        time_display_options = ['اي وقت', 'اخر سنة', 'اخر شهر', 'اخر اسبوع', 'اخر يوم', 'اخر ساعة']
        self.time_option_var = tk.StringVar()
        self.time_option_menu = ttk.Combobox(self, textvariable=self.time_option_var, values=time_display_options,
                                             state="readonly", font=("Arial", 14))
        self.time_option_menu.set(time_display_options[0])
        self.time_option_menu.pack(pady=5)

        exit_button = tk.Button(self, text="Exit", command=self.destroy, bg="red", fg="white", font=("Arial", 20))
        exit_button.pack(pady=4)

        self.style = ttk.Style()
        self.style.configure('TButton', background='#006400', foreground='white')
        self.style.configure('TFrame', background='#282828')

    def execute_task(self):
        news_articles = self.get_templates()
        if not news_articles:
            messagebox.showinfo("Error", "No words in this file")
            return

        time_option = self.time_option_var.get()
        if not time_option:
            return

        # Map time_option to specific values
        time_option_map = {
            'اخر سنة': 'y',
            'اخر شهر': 'm',
            'اخر اسبوع': 'w',
            'اخر يوم': 'd',
            'اخر ساعة': 'h',
            'اي وقت': 'anytime'
        }

        time_option = time_option_map.get(time_option, 'anytime')

        max_results = self.select_max_results()
        excluded_domains = self.get_excluded_domains('black-list.txt')

        # Prompt user for folder name input
        folder_name_input = simpledialog.askstring("Folder Name", "Enter folder name for search results:")

        if not folder_name_input:
            messagebox.showinfo("Error", "Folder name cannot be empty")
            return

        # Create a single folder for all results
        now = datetime.datetime.now()
        formatted_now = now.strftime("%Y-%m-%d_%H-%M")
        folder_name = f'Search-Results-{formatted_now}-{folder_name_input}'
        folder_path = os.path.join(self.results_folder, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        all_data = []

        for i, news_article in enumerate(news_articles, start=1):
            if not news_article:
                print(f"Skipping article {i} due to missing title")
                continue

            search_word_data = self.main(folder_name_input, folder_path, [news_article], time_option, max_results,
                                         excluded_domains)
            all_data.extend(search_word_data)

        file_name = f'Search-Data-{formatted_now}-{folder_name_input}.xlsx'
        excel_path = os.path.join(folder_path, file_name)

        # Create DataFrame from all_data list
        df_all_data = pd.DataFrame(all_data)

        # Write DataFrame to Excel
        try:
            with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer_all:
                df_all_data.to_excel(writer_all, index=False)
                worksheet_all = writer_all.sheets['Sheet1']
                worksheet_all.set_column('A:C', 50)
        except Exception as e:
            print(f"Failed to write Excel file: {e}")
            messagebox.showinfo("Error", "Failed to write Excel file")
            return

        messagebox.showinfo("Task Completed", "Task completed successfully!")

    def add_template_entry(self):
        entry = Entry(self.template_frame, width=50)
        entry.pack(pady=3)
        self.template_entries.append(entry)

    def get_templates(self):
        self.templates = [entry.get() for entry in self.template_entries if entry.get()]
        return self.templates

    def main(self, file_name_input, folder_path, search_words, time_option, max_results, excluded_domains):
        all_data = []

        try:
            for search_word in search_words:
                found_links_all = []

                found_links_all.extend(self.search_google(search_word, time_option, max_results))
                found_links_all.extend(self.search_duckduckgo(search_word, time_option, max_results))

                filtered_links = [link for link in found_links_all if
                                  not any(domain in link['link'] for domain in excluded_domains)]

                for link in filtered_links:
                    all_data.append({
                        'Search Word': search_word,
                        'Link': link['link'],
                        'Link Text': link.get('link_text', '')  # Append link text if available
                    })

        except Exception as e:
            print("Error", f"An error occurred: {e}")
            messagebox.showinfo("Error", "An error occurred. Please try again.")
        finally:
            if self.driver:
                driver_pid = self.driver.service.process.pid
                self.killDriverZombies(driver_pid)

        return all_data

    def encode_image_to_base64(self, image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return encoded_string

    def start_driver(self):
        self.driver = WebDriver.start_driver(self)
        return self.driver

    def get_publish_date(self, link):
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        try:
            response = requests.get(link)
            if response.status_code == 200:
                encoding = chardet.detect(response.content)['encoding']
                response.encoding = encoding
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')

                link_text = soup.get_text()
                date_match = re.search(r'\b\d{1,2}\s+\w+\s+\d{4}\b', link_text, re.IGNORECASE | re.UNICODE)
                if date_match:
                    link_date = date_match.group()
                    return link_date.strip()

                date_patterns = [
                    r'\b(\d{4}/\d{2}/\d{2})\b',
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',
                    r'\b(\d{1,2}\s+\w+\s+\d{2,4})\b',
                    r'\b(\d{4}-\d{2}-\d{2})\b',
                    r'\b(\d{1,2}\s+\w+\s+\d{4})\b',
                    r'\b(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{2,4})\b',
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2})\b',
                    r'\b(\d{1,2}\s+\w+\s+/\s+\w+\s+\d{2,4})\b',
                    r'\b(\d{1,2}\s+\w+\s+\d{4}\s+\d{1,2}:\d{2}:\d{2})\b',
                    r'\b(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\b',
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}:\d{2})\b',
                    r'\b(\d{1,2}\s+\w+\s+\d{4}\s+\d{1,2}:\d{2}:\d{2})\b',
                    r'\b(\d{1,2}\s+[?-?]+\s+\d{4})\b',
                    r'\b(\d{1,2}/\d{1,2}/\d{2,4})\s+[?-?]+\s+\d{1,2}:\d{2}\b',
                    r'\b(\d{1,2}\s+[\u0623-\u064a]+\s+\d{4})\b',
                    r'\b(\d{1,2}\s+[\u0623-\u064a]+\s+/\s+[\u0623-\u064a]+\s+\d{2,4})\b',
                    r'(\d{4}/\d{2}/\d{2}/)'
                ]

                for pattern in date_patterns:
                    date_match = re.search(pattern, html_content, re.IGNORECASE | re.UNICODE)
                    if date_match:
                        link_date = date_match.group()
                        return link_date.strip()

                time_tags = soup.find_all('time', class_=re.compile(r'.*'))
                for time_tag in time_tags:
                    datetime_attr = time_tag.get('datetime')
                    if datetime_attr:
                        arabic_date = time_tag.text.strip()
                        return arabic_date

                link_date_match = re.search(r'(\d{4}-\d{2}-\d{2})', link)
                if link_date_match:
                    return link_date_match.group()

            return None
        except:
            return None

    def get_title(self, link):
        try:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            response = requests.get(link)
            if response.status_code == 200:
                encoding = chardet.detect(response.content)['encoding']
                response.encoding = encoding
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')
                title = soup.title.string.strip()
                return title
        except:
            return None

    def killDriverZombies(self, driver_pid):
        try:
            parent_process = psutil.Process(driver_pid)
            children = parent_process.children(recursive=True)
            for process in [parent_process] + children:
                process.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Select Search Engine Links File",
                                               filetypes=[("All files", "*.*")])
        return file_path

    def select_max_results(self):
        max_results = simpledialog.askinteger("Max Results",
                                              "Enter the maximum number of results to fetch:")
        return max_results

    def get_excluded_domains(self, domains_file):
        try:
            with open(domains_file, 'r') as file:
                excluded_domains = [line.strip() for line in file.readlines()]
            return excluded_domains
        except FileNotFoundError:
            print(f"Domains file '{domains_file}' not found.")
            return []

    def simulate_human_interaction(self, driver):
        actions = ActionChains(driver)
        actions.move_by_offset(random.randint(0, 10), random.randint(0, 10)).perform()
        time.sleep(random.uniform(0.5, 1.5))
        actions.move_by_offset(random.randint(0, 10), random.randint(0, 10)).perform()
        time.sleep(random.uniform(0.5, 1.5))
        actions.move_by_offset(random.randint(0, 10), random.randint(0, 10)).perform()

    def search_google(self, word, time_option='anytime', max_results=10):
        found_links = []
        processed_urls = set()
        start = 0

        while len(found_links) < max_results:
            encoded_word = quote(word)
            search_url = f'https://www.google.com/search?q="{encoded_word}"&start={start}'

            if time_option != 'anytime':
                search_url += f"&tbs=qdr:{time_option}"

            print(search_url)

            try:
                time.sleep(1)
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
                        break  # No new links found, exit the loop

                start += 10
                time.sleep(random.uniform(1.0, 3.0))

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

if __name__ == "__main__":
    app = SearchAboutNews()
    app.mainloop()



