# logparser

logparser is a tool that will fetch load balancer logs from an S3 bucket and provides a few reporting options.

## Setup

#### Prerequisites
- python 2.7
- pip >= 6.0

To get the best experience, it is recommended to run logparser from a virtualenv. The [virtualenvwrapper](https://bitbucket.org/dhellmann/virtualenvwrapper) extensions is an ideal option to create, delete and manage virtual environments. 

```
mkvirtualenv logparser

git clone git@github.com:wcleong/logparser.git

cd logparser

pip install .
```

It is also assumed that you have aws tools setup with the appropriate credentials to access the S3 bucket you are trying to download from. Refer to the [boto3 quickstart guide](https://boto3.readthedocs.io/en/latest/guide/quickstart.html) for more details on setting up your credentials.

## Commands

#### Options

```
usage: logparser [-h] [--code <http_status_code>] [--from <from_date>]
                 [--to <from_date>] [--max <count>]
                 [--for <relative_time> <relative_time>]
                 get_option

positional arguments:
  get_option            [getcodes, geturls, getUAs, getreport]

optional arguments:
  -h, --help            show this help message and exit
  --code <http_status_code>
                        http error code to filter by (default: None)
  --from <from_date>    start date for search (default: None)
  --to <from_date>      end date for search (default: None)
  --max <count>         Top N items to display (default: None)
  --for <relative_time> <relative_time>
                        Relative duration (default: None)
```

#### Examples
Get top N error codes for a given period of time:
```
logparser getcodes --from 2018/07/01 --to 2018/07/07 --max N
```
Get top N urls for an error passed as parameter for a given period of time:
```
logparser geturls --code 404 --from 2018/07/01 --to 2018/07/07 --max N
```
Get top N user agents for a given http code for a given period of time:
```
logparser geturls --code 404 --from 2018/07/01 --to 2018/07/07 --max N
```
Get a report containing the most requested url for a given period of time. The report also includes the number of request, the most common status code and max values for req_processing_time, target_processing_time and resp_processing_time:
```
logparser getreport --from 2018/07/01 --to 2018/07/02 --max N
```
Sample output:
```
Gathering info about contents in <bucket_name>...
DONE!
Downloading log files from s3. This might take a while...
DONE!


Top 10 User Agents
==============
8375 - Mozilla/5.0 (compatible; SemrushBot/2~bl; +http://www.semrush.com/bot.html)
3913 - Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)
1931 - Pingdom.com_bot_version_1.4_(http://www.pingdom.com/)
1074 - Nextcloud Server Crawler
971 - Mozilla/5.0 (compatible; Qwantify/2.4w; +https://www.qwant.com/)/2.4w
784 - Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)
667 - Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0
503 - Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36
484 - Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)
452 - Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0
```
#### Notes

You can use absolute (2018/07/01) ​*date* stamps and relative *date and time* stamps.
```
logparser geturls --code 404 --from 2018/07/01 --to 2018/07/07
logparser geturls --code 404 --for 7 days
logparser geturls --code 404 --for 5 hours
```

logparser will interpret the lack of a *--max* parameter as “provide all results for that metric”.