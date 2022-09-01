# Pixiv Searcher
Uses PixivPy to run searches on a specific tag, sort all the results in order of views or bookmarks and returns a text file and csv of the results

## Files
Naming scheme
`{name}_{sort}_{type}.txt`

- **name** : name of character given at beginning of search
- **sort** : type of sorting, either by number of views or bookmarks
- **type** : `links` indicates that it has **links only**, those without the `_links` contains the number of views/bookmarks beside each link
- **sfw** : those that have SFW appended only contain SFW images (not marked R-18 on Pixiv but some are still really risque, don't rely soley on this)

## Requirements
- pixivipy
- pandas
- selenium
- pprint

## Pixiv Auth
Reference here

https://gist.github.com/upbit/6edda27cb1644e94183291109b8a5fde?permalink_comment_id=3872537

## Usage
Selenium WebDriver will be required to use the pixiv_auth script to grab the refresh key

Create and configure the `config.ini` file, a `example.ini` is provided

