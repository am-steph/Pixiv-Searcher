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

sleepTime = config.getfloat('Searcher','sleepTime')
_dir = config['Searcher']['directory']

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
def appapi_search(aapi, search, filename):
    # first_tag = input("Enter search string:")
    first_tag = search
    s_offset = 0
    all_images = []
    all_results = []
    endOfSearch = False
    appendDate = False
    nextDate = None
    counter = 1
    file_name = filename

    while(endOfSearch != True):
        try:
            temp_list = []
            if not appendDate:
                time.sleep(sleepTime)
                json_result = aapi.search_illust(first_tag, search_target="partial_match_for_tags", sort="date_desc", filter="for_ios", offset=s_offset)
                illusts = json_result['illusts']
                for i in illusts:
                    item = {'id' : i.id, 'x_restrict' : i.x_restrict, 'create_date' : i.create_date, 'total_view' : i.total_view, 'total_bookmarks' : i.total_bookmarks}
                    temp_list.append(item)
                all_images.extend(temp_list)
                all_results.extend(illusts)
                #print(temp_list[-1]) 
                s_offset+=len(temp_list)
                print(f'Searching: {s_offset} - Found: {len(temp_list)}')
                if s_offset >= 4500: #once it hits 4500 we'll exit and use the last date as the new place to start searching since offset maxes at 5000
                    appendDate = True
                    s_offset = 0
                    counter+= 1
                    nextDate = all_images[-1].get("create_date")[0:10]

            else:
                time.sleep(sleepTime)
                json_result = aapi.search_illust(first_tag, search_target="partial_match_for_tags", end_date=nextDate, sort="date_desc", offset=s_offset)
                illusts = json_result['illusts']
                for i in illusts:
                    item = {'id' : i.id, 'x_restrict' : i.x_restrict, 'create_date' : i.create_date, 'total_view' : i.total_view, 'total_bookmarks' : i.total_bookmarks}
                    temp_list.append(item)
                all_images.extend(temp_list)
                all_results.extend(illusts)
                #print(temp_list[-1]) 
                s_offset+=len(temp_list)
                print(f"Round {counter} - Searching: {s_offset}")
                if s_offset >= 4500:
                    s_offset = 0
                    counter+= 1
                    nextDate = all_images[-1].get("create_date")[0:10]
                    print(nextDate)
                    print("Refreshing Auth") #In case the search took a while, the access token might be expired, so we'll refresh it
                    token = refresh(_REFRESH_TOKEN)
                    aapi.set_auth(access_token=token,refresh_token=_REFRESH_TOKEN)
            
            if len(temp_list) == 0:
                endOfSearch = True
                print("End of Search")
                
        except Exception as e:
            print("End of search")
            traceback.print_exc()
            endOfSearch = True
    results = [all_images,all_results]
    return results


# %%
def export(illusts, filename):
    all_images = illusts[0]
    all_results = illusts[1]
    file_name = filename
    
    currentDir = _dir
    os.chdir(currentDir)
    try:
        os.mkdir(file_name)
    except Exception:
        print("Folder exists")
        pass
    os.chdir('%s/%s'%(currentDir,file_name))

    print("Normalizing dataframe")
    df = pd.json_normalize(all_results)
    print("Inserting Pixiv Links")
    for i,row in df.iterrows():
        id = df.at[i,'id']
        df.at[i,'id'] = f'https://www.pixiv.net/en/artworks/{id}'
    print("Exporting to CSV Sheet")
    df.to_csv(f"{file_name}.csv",encoding="utf-8")

    bookmark_output = open('%s_Bookmarks.txt'%file_name,'w')
    view_output = open('%s_Views.txt'%file_name,'w')
    
    sfw_bookmark_output = open('%s_Bookmarks_SFW.txt'%file_name,'w')
    sfw_view_output = open('%s_Views_SFW.txt'%file_name,'w')
    sfw_bookmark_link = open('%s_Bookmarks_links_SFW.txt'%file_name,'w')
    sfw_view_link = open('%s_Views_links_SFW.txt'%file_name,'w')

    bookmark_link = open('%s_Bookmark_links.txt'%file_name,'w')
    view_link = open('%s_View_links.txt'%file_name,'w')
    
    print("Sorting images by bookmark...")
    bookmark_rank = {}
    sfw_bookmark_rank = {}
    for i in all_images:
        bookmark_rank.update({i.get('id') : i.get('total_bookmarks')})
        if i.get('x_restrict') == 0:
            sfw_bookmark_rank.update({i.get('id') : i.get('total_bookmarks')})
    bookmark_sort = sorted(bookmark_rank.items(),key=lambda x: x[1], reverse=True)
    sfw_bookmark_sort = sorted(sfw_bookmark_rank.items(),key=lambda x: x[1], reverse=True)
    print("Writing to file...")
    for i,j in bookmark_sort:
        bookmark_output.write('https://www.pixiv.net/en/artworks/%d  '%i+'Bookmarks: %d\n'%j )
        bookmark_link.write('https://www.pixiv.net/en/artworks/%d\n'%i)
    bookmark_output.close()
    bookmark_link.close()
    for i,j in sfw_bookmark_sort:
        sfw_bookmark_output.write('https://www.pixiv.net/en/artworks/%d  '%i+'Bookmarks: %d\n'%j )
        sfw_bookmark_link.write('https://www.pixiv.net/en/artworks/%d\n'%i)
    sfw_bookmark_output.close()
    sfw_bookmark_link.close()
    print('Done...')

    print("Sorting images by views")
    view_rank = {}
    sfw_view_rank = {}
    for i in all_images:
        view_rank.update({i.get('id') : i.get('total_view')})
        if i.get('x_restrict') == 0:
            sfw_view_rank.update({i.get('id') : i.get('total_view')})
    view_sort = sorted(view_rank.items(),key=lambda x: x[1], reverse=True)
    sfw_view_sort = sorted(sfw_view_rank.items(),key=lambda x: x[1], reverse=True)

    print("Writing to file...")
    for i,j in view_sort:
        view_output.write('https://www.pixiv.net/en/artworks/%d  '%i+'Views: %d\n'%j )
        view_link.write('https://www.pixiv.net/en/artworks/%d\n'%i)
    view_output.close()
    view_link.close()
    for i,j in sfw_view_sort:
        sfw_view_output.write('https://www.pixiv.net/en/artworks/%d  '%i+'Views: %d\n'%j )
        sfw_view_link.write('https://www.pixiv.net/en/artworks/%d\n'%i)
    sfw_view_output.close()
    sfw_view_link.close()
    print('Done...')

    print('\nCompleted')

# %%
#Main
# app-api
search = input("Enter search term: ")
filename = input('Enter filename: ')
aapi = AppPixivAPI(**_REQUESTS_KWARGS)

accessToken = refresh(_REFRESH_TOKEN)

_e = None
for _ in range(3):
    try:
        aapi.set_auth(access_token=accessToken,refresh_token=_REFRESH_TOKEN)
        break
    except PixivError as e:
        _e = e
        time.sleep(10)
else:  # failed 3 times
    raise _e
results = appapi_search(aapi, search, filename)

# %%
#print(results)
export(results,filename)


