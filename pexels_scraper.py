import requests
import os
import string
import random
import time

def generate_random_filename(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

def download_video(url, directory):
    random_filename = generate_random_filename() + '.mp4'
    filepath = os.path.join(directory, random_filename)
    response = requests.head(url, allow_redirects=True)
    response.raise_for_status()
    direct_url = response.url
    with requests.get(direct_url, stream=True) as response:
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    time.sleep(2)
    return random_filename

def load_used_urls(file_path):
    used_urls = set()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                used_urls.add(line.strip())
    return used_urls

def save_used_url(file_path, url):
    with open(file_path, 'a') as f:
        f.write(url + '\n')

def calculate_percentage(total_downloaded, num_videos):
    return (total_downloaded / num_videos) * 100

def search_and_download_videos(api_key, query, num_videos, batch_size=100, per_page=10, directory='my_dataset', used_urls_file='used_urls.txt', checkpoint_file='checkpoint.txt'): #checkpoint for videos downloaded, used_urls for videos already downloaded
    total_downloaded = 0 #specify how many videos have been downloaded, or change checkpoint.txt
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            total_downloaded = int(f.read())
    while total_downloaded < num_videos:
        try:
            os.makedirs(directory, exist_ok=True)
            headers = {
                'Authorization': api_key,
            }
            params = {
                'query': query,
                'per_page': per_page,
                'type': 'video',
            }
            downloaded_urls = load_used_urls(used_urls_file)
            while total_downloaded < num_videos:
                response = requests.get('https://api.pexels.com/videos/search', headers=headers, params=params)
                if response.status_code == 429:
                    # If rate limit is exceeded, wait and retry
                    print("Rate limit exceeded. Waiting before retrying...")
                    time.sleep(300)  # Wait for 5 mins
                    continue
                response.raise_for_status()
                data = response.json()
                for video in data['videos']:
                    if total_downloaded >= num_videos:
                        break
                    video_url = video['video_files'][0]['link']
                    if video_url not in downloaded_urls:
                        filename = download_video(video_url, directory)
                        save_used_url(used_urls_file, video_url)
                        downloaded_urls.add(video_url)
                        total_downloaded += 1
                        percentage = calculate_percentage(total_downloaded, num_videos)
                        print(f"Downloaded {total_downloaded} out of {num_videos} videos ({percentage:.2f}%).")
                        if total_downloaded % batch_size == 0:
                            print(f"Downloaded {total_downloaded} out of {num_videos} videos ({percentage:.2f}%).")
                params['page'] = data['page'] + 1
            with open(checkpoint_file, 'w') as f:
                f.write(str(total_downloaded))
        except Exception as e:
            print(f"An error occurred: {e}. Attempting to relaunch the script...")
            time.sleep(60)  # Wait for 1 minute before relaunching
            continue

if __name__ == '__main__':
    api_key = 'enter API key here'
    query = '' # Enter Query Here
    num_videos = 10000  # Specify the total number of videos you want to download
    search_and_download_videos(api_key, query, num_videos)
