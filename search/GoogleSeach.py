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
