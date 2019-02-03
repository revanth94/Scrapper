from bs4 import BeautifulSoup as bs
import requests
from Scrapper import config, links, download


def get_download_page_link(movie_page_link):
	response = requests.get(movie_page_link, headers=config.headers_mobile)
	modified_response = str(response.content).replace('--!>', '-->', 100)
	soup = bs(modified_response, 'html.parser')
	divs = soup.find_all('div', attrs={'class': 'bg'})
	links_list = []
	for div in divs:
		a = div.find('a')
		text = a.text
		if '320Kbps' in text:
			rel_link = a.attrs.get('href')
			links_list.append(config.base_link + rel_link)
	final_list = []
	[final_list.append(link) for link in links_list if link not in final_list]
	return final_list


def get_download_request_payload(download_page_link):
	print("getting page content")
	print(download_page_link[0])
	content = get_page_content(download_page_link[0], config.headers_mobile)
	# divs = content.find('div', attrs={'class': 'd2', 'align':'left'})
	form = content.find('form')
	inputs = form.find_all('input')
	payload = {}
	for line in inputs:
		if (line.attrs.get('name') is not None) and (line.attrs.get('value') is not None):
			payload[line.attrs.get('name')] = line.attrs.get('value')
	return payload


def get_download_link(payload):
	# Add a sample payload here
	if 'dir' in payload and 'file' in payload:
		post_response = requests.post(config.post_link, data=payload)
		return post_response.url
	return None


def download_movie(movie_page_link, movie_name):

	download_page_link = get_download_page_link(movie_page_link)

	payload = get_download_request_payload(download_page_link)
	print(payload)
	download_link = get_download_link(payload)
	print(download_link)
	if download_link is None:
		return
	download_path = config.DOWNLOAD_FOLDER_PATH + movie_name + ".zip"
	print(download_path)
	download.download(download_link, download_path, config.headers_mobile)


def get_page_content(url, headers):
	response = requests.get(url, headers=headers)
	return bs(response.content, 'html.parser')


def get_movie_indices():
	index_list = []
	movie_index_link_pattern = "http://hqzone.telugump3z.net/?d=A_to_Z&p=0&page={0}&sort=0&tag"
	has_response = True
	index_page_counter = 0
	while(has_response):
		index_page_url = movie_index_link_pattern.format(index_page_counter)
		index_page_counter+=1
		index_page_content = get_page_content(index_page_url, config.headers_mobile)
		indices_in_page = extract_indices_from_index_page(index_page_content)
		if len(indices_in_page) == 0:
			has_response = False
		for index in indices_in_page:
			if index not in index_list:
				index_list.append(index)
			else:
				has_response = False
				continue
	return index_list


def extract_movies_from_index_page(page_content):
	index_list = []
	if page_content is None:
		return index_list
	div_list = page_content.find_all('div', attrs={'class': 'bg'})
	for div in div_list:
		tables = div.find_all('table')
		if len(tables) == 0:
			return index_list
		table = tables[0]
		t_rows = table.find_all('tr')
		if len(t_rows) == 0:
			return index_list
		t_row = t_rows[0]
		t_ds = t_row.find_all('td')
		for t_d in t_ds:
			a_s = t_d.find_all('a')
			if len(a_s) == 0:
				continue
			a = a_s[0]
			movie = [a.text, config.base_link + a.attrs.get('href')]
			index_list.append(movie)
		a_s = div.find_all('a')
		a = a_s[0]
		link = a.attrs.get('href')
		if link is None:
			continue
		else:
			full_link = links.base_link + link
			index_list.append(full_link)
	return index_list


def get_all_movie_urls(all_indices):
	all_movie_urls = []
	for index in all_indices:
		# index_page_content = get_response(index, config.headers_mobile)
		movie_urls_in_index = get_movies_in_index(index)
		for movie_url in movie_urls_in_index:
			all_movie_urls.append(movie_url)
	return all_movie_urls


def extract_indices_from_index_page(page_content):
	movies = []
	div_list = page_content.find_all('div', attrs={'class': 'bg'})
	for div in div_list:
		a_s = div.find_all('a')
		a = a_s[0]
		link = a.attrs.get('href')
		if link is None:
			continue
		else:
			full_link = links.base_link + link
			movies.append(full_link)
	return movies


def get_index_page_pattern(index_base_url):
	index_base_url_stripped = index_base_url.split("&tag")
	return "&p=0&page={0}&sort=0&tag".join(index_base_url_stripped)


def get_movies_in_index(index_url):
	movie_list = []
	index_page_pattern = get_index_page_pattern(index_url)
	has_response = True
	index_page_counter = 0
	while (has_response):
		index_movie_page_url = index_page_pattern.format(index_page_counter)
		index_page_counter += 1
		index_page_content = get_page_content(index_movie_page_url, config.headers_mobile)
		indices_in_page = extract_movies_from_index_page(index_page_content)
		if len(indices_in_page) == 0:
			has_response = False
		for index in indices_in_page:
			if index not in movie_list:
				movie_list.append(index)
			else:
				has_response = False
				continue
	return movie_list


def get_all_songs_for_all_movies():
	all_indices = get_movie_indices()
	print(all_indices)
	all_movie_urls = get_all_movie_urls(all_indices)
	for movie in all_movie_urls:
		print(movie)
		download_movie(movie[1], movie[0])

if __name__ == "__main__":
	print("yay")
	# get_all_songs_for_all_movies()
	movie_page_url = "http://hqzone.telugump3z.net/?d=A_to_Z/0-9/1-Nenokkadine (2013) HQ&p=0&sort=0&tag"
	movie_name = "one_nenokkadine"
	download_movie(movie_page_url, movie_name)
	# link = config.base_link + "index.php?d=/A_to_Z/V/Veera-Bhoga-Vasantha-Rayalu-(2018)-HQ/"
	# d_link = get_download_page_link(link)[0]
	# print(d_link)
	#d_link = 'http://hqzone.telugump3z.net/download.php?d=/A_to_Z/V/Veera-Bhoga-Vasantha-Rayalu-(2018)-HQ/&' \
	#		'filename=VmVlcmEgQmhvZ2EgVmFzYW50aGEgUmF5YWx1ICgyMDE4KSAzMjBLYnBzLnppcA=='
	#params = get_download_request_payload(d_link)
