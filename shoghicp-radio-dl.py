#!/usr/local/bin/python3
import json
import multiprocessing
import os
import re
import shutil
import sys
import urllib.parse
import requests

# Change this to your own API key.
API_KEY = ""

# Feel free to change.
DOWNLOAD_THREADS = 2
DOWNLOAD_DIRECTORY = "~/Media/Music/Unorganized"
FILENAME_FORMAT = lambda x: f'{x["artist"]} - {x["title"]}' # set to False to keep original filename
FOLDERNAME_FORMAT = lambda x: f'{x["album"]}' # set to False to avoid creating album folders

# Terminal color escape codes.
CLEAR_EC = "\x1b[0m"
RED_EC = "\x1b[1;35m"
YELLOW_EC = "\x1b[1;33m"
GREEN_EC = "\x1b[1;32m"
WHITE_EC = "\x1b[1;38m"
GRAY_EC = "\x1b[1;30m"


def download_file(result):
    """Downloads a single track to disk."""
    download_url = f'https://radio.animebits.moe/api/download/{result["hash"]}'

    print(f" {GRAY_EC}* Downloading:{CLEAR_EC} {WHITE_EC}{result['artist']} - {result['title']} ({result['album']}){CLEAR_EC}")
    with requests.get(download_url, auth=("", API_KEY), stream=True) as dl_req:
        # Fetch real filename from content-disposition header so we know which
        # extension to append to the downloaded file when renaming it.
        try:
            # Handle UTF-8 filenames
            real_filename = urllib.parse.unquote(re.findall(
                r"filename\*=utf-8''(.+)", dl_req.headers["content-disposition"]
            )[0])
        except IndexError:
            # Handle ASCII filenames
            real_filename = re.findall(
                "filename=\"(.+)\"", dl_req.headers["content-disposition"]
            )[0]

        # Don't create album folders if FOLDERNAME_FORMAT == False
        try:
            foldername = FOLDERNAME_FORMAT(result)
        except TypeError:
            foldername = ''

        # Don't rename files if FILENAME_FORMAT == False
        try:
            filename = FILENAME_FORMAT(result).replace("\\", "_")
            extension = real_filename[real_filename.rfind(".") + 1 :]
            filename += f".{extension}"
        except TypeError:
            filename = real_filename

        # Create directory, write file
        os.makedirs(os.path.join(DOWNLOAD_DIRECTORY, foldername), exist_ok=True)
        with open(os.path.join(DOWNLOAD_DIRECTORY, foldername, filename), "wb") as file:
            shutil.copyfileobj(dl_req.raw, file)


def parse_download_list(string):
    """Expands ranges into a list (ex.: "1-3,7" becomes [1,2,3,7])."""
    download_list = set()
    matches = re.findall(r"(\d+(?:-\d+)?)", string)
    for match in matches:
        if "-" in match:
            # Treat ranges (ex.: 1-3)
            start = int(match[: match.find("-")])
            end = int(match[match.find("-") + 1 :])

            for element in list(range(start, end + 1)):
                download_list.add(element)
        else:
            # Treat isolated numbers
            download_list.add(int(match))

    return download_list


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 shoghicp-radio-dl.py <search query>")
        quit()

    query = " ".join(sys.argv[1:])
    query_url = f"https://radio.animebits.moe/api/search/{query}"

    # Query API endpoint
    print(f"{RED_EC}=>{CLEAR_EC} {WHITE_EC}Searching:{CLEAR_EC} {query}")
    req = requests.get(query_url, auth=("", API_KEY))
    if req.status_code != 200:
        print(f"{RED_EC}ERROR:{CLEAR_EC} Received {req.status_code} from server.")
        quit()

    # Parse JSON response
    res = json.loads(req.text)
    for i, result in enumerate(res, 1):
        print(
            f'{RED_EC}{i}. {result["artist"]}{CLEAR_EC} - {YELLOW_EC}{result["title"]}{CLEAR_EC} ({result["album"]})'
        )

    # Ask for user input
    tracks = input(
        f"\n{RED_EC}=>{CLEAR_EC} {WHITE_EC}Which tracks to download?{CLEAR_EC} (ex.: 1-3,7): "
    )
    try:
        download_list = parse_download_list(tracks)
    except (IndexError, ValueError):
        print(f"{RED_EC}ERROR:{CLEAR_EC} Invalid input. Exiting...")
        quit()

    # Download files
    pool = multiprocessing.Pool(DOWNLOAD_THREADS)
    threads = []
    for i, result in enumerate(res, 1):
        if i in download_list:
            threads.append(pool.apply_async(download_file, args=(result,)))
    pool.close()

    # Re-raise any exceptions that happened in the download threads
    [thread.get() for thread in threads]

    # Wait for all threads to finish
    pool.join()

    print(f"{RED_EC}=>{CLEAR_EC} {WHITE_EC}Done!{CLEAR_EC}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Hide traceback when user hits CTRL-C
        quit()
