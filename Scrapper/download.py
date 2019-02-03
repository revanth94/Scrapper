import requests, zipfile, io
from Scrapper import links, config
from bs4 import BeautifulSoup as bs


def download(link, file, headers):
    zip_stream = requests.get(link, headers=headers, stream=True)
    # z = zipfile.ZipFile(io.BytesIO(zip_stream.content))
    print(zip_stream)
    with open(file, "wb+") as zip_file:
        for chunk in zip_stream.iter_content(chunk_size=1024):
            # writing one chunk at a time
            if chunk:
                zip_file.write(chunk)

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
    if len(download_page_link) == 0:
        return None
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
    print(download_page_link)
    payload = get_download_request_payload(download_page_link)
    print(payload)
    if payload is None:
        return
    download_link = get_download_link(payload)
    print(download_link)
    if download_link is None:
        return
    download_path = config.DOWNLOAD_FOLDER_PATH + movie_name + ".zip"
    print(download_path)
    download(download_link, download_path, config.headers_mobile)


def get_page_content(url, headers):
    response = requests.get(url, headers=headers)
    return bs(response.content, 'html.parser')

def get_movie_list():
    file_name = "/home/revanth/PycharmProjects/Scrapper/patterns_and_data/telugu_movies_with_song_urls.csv"
    links = []
    file = open(file_name, 'r')
    for line in file:
        links.append(line.split(','))
    file.close()
    return links[10:100]


if __name__ == "__main__":
    m_list = get_movie_list()
    for movie in m_list:
        download_movie(movie[1], movie[0])
    '''
    download_link = "http://hqzone.telugump3z.org/load/A_to_Z/V/Veera-Bhoga-Vasantha-Rayalu-(2018)-HQ/.zip/Veera" \
                    "%20Bhoga%20Vasantha%20Rayalu%20(2018)%20320Kbps.zip"
    file_name = "test.zip"
    print("Downloading" + file_name)
    download(download_link, file_name, links.headers_mobile)
    print("Downloaded" + file_name)
    '''