# %%
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ast import Continue
import sys
import time
import os 
from pixivpy3 import AppPixivAPI, PixivError
import traceback
import pandas as pd
import configparser
sys.dont_write_bytecode = True

config = configparser.ConfigParser()
config.read('config.ini')

# use python pixiv_auth login
# get your refresh_token, and replace _REFRESH_TOKEN
#  https://github.com/upbit/pixivpy/issues/158#issuecomment-778919084
_REFRESH_TOKEN = config['Pixiv']['refreshToken']
_TEST_WRITE = False


# If a special network environment is meet, please configure requests as you need.
# Otherwise, just keep it empty.
_REQUESTS_KWARGS = {
    # 'proxies': {
    #     'https': 'http://127.0.0.1:1087',
    # },
    # 'verify': False,       # PAPI use https, an easy way is disable requests SSL verify
}

_csv = config['Downloader']['csvFile']
_path = config['Downloader']['path']
NSFW = config.getboolean('Downloader','nsfw')
original = config.getboolean('Downloader','original')
minBookmarks = config.getint('Downloader','minBookmarks')
sleepTime = config.getfloat('Downloader','sleepTime')

if NSFW:
    restrict = 0
else:
    restrict = 1

if original:
    type = 'meta_single_page.original_image_url'
else:
    type = 'image_urls.large'

# %%
import requests
from pprint import pprint

USER_AGENT = "PixivIOSApp/7.13.3 (iOS 14.6; iPhone13,2)"
AUTH_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"
REQUESTS_KWARGS = {
    # 'proxies': {
    #     'https': 'http://127.0.0.1:1087',
    # },
    # 'verify': False
}

def print_auth_token_response(response):
    data = response.json()

    try:
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
    except KeyError:
        print("error:")
        pprint(data)
        exit(1)

    print("access_token:", access_token)
    print("refresh_token:", refresh_token)
    print("expires_in:", data.get("expires_in", 0))
    return access_token

def refresh(refresh_token):
    response = requests.post(
        AUTH_TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "include_policy": "true",
            "refresh_token": refresh_token,
        },
        headers={
            "user-agent": USER_AGENT,
            "app-os-version": "14.6",
            "app-os": "ios",
        },
        **REQUESTS_KWARGS
    )
    access = print_auth_token_response(response)
    return access

# %%
csv_file = _csv
df = pd.read_csv(csv_file)

sfwdf = df[(df['x_restrict']==restrict) | (df['total_bookmarks'] <= minBookmarks)].index
df.drop(sfwdf,inplace=True)

bookmark_rank = {}
df2 = df[[type,'total_bookmarks']]
for index, row in df2.iterrows():
    bookmark_rank.update({row[type] : row['total_bookmarks']})
bookmark_sort = sorted(bookmark_rank.items(),key=lambda x: x[1], reverse=True)

#print(bookmark_sort)


# %%
print(len(bookmark_sort))
for col in df.columns:
    print(col)

# %%
api = AppPixivAPI()
token = refresh(_REFRESH_TOKEN)
api.set_auth(access_token=token,refresh_token=_REFRESH_TOKEN)
dir = _path

counter=0
for j in range(counter,len(bookmark_sort)-1):
    try:
        i = bookmark_sort[j]
        time.sleep(sleepTime)
        filename=i[0].split('/')[-1]
        print(f'{counter+1}: Downloading {filename}')
        api.download(url=i[0],path=dir,fname=f'{counter+1}_{filename}')
        counter+=1
        if counter%150==0:
            token = refresh(_REFRESH_TOKEN)
            api.set_auth(access_token=token,refresh_token=_REFRESH_TOKEN)
    except:
        continue



