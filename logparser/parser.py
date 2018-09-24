"""Helper methods to generate parse logs"""

import gzip
import os
import collections
import re
from datetime import datetime
import shutil


def get_codes(download_dir, files):
    """Returns a list of error codes given a list of log files"""
    codes = []
    # Only care about 4XX and 5XX status codes
    pattern = re.compile("^[4-5][0-9][0-9]$")

    for file in files:
        filename = file.split('/')[-1]
        path = os.path.join(download_dir, filename)
        with gzip.open(path, 'r') as fin:
            for line in fin:
                code = line.strip().split(' ')[8]
                if pattern.match(code):
                    codes.append(code)
    return codes


def get_urls_by_error(download_dir, files, code):
    """Returns a list of urls corresponding to a given status code"""
    urls = []

    for file in files:
        filename = file.split('/')[-1]
        path = os.path.join(download_dir, filename)
        with gzip.open(path, 'r') as fin:
            for line in fin:
                fields = line.strip().split(' ')
                if fields[8] == code:
                    urls.append(fields[13])
    return urls


def get_uas_by_error(download_dir, files, code):
    """Returns a list of user agents corresponding to a given status code"""
    uas = []
    for file in files:
        filename = file.split('/')[-1]
        path = os.path.join(download_dir, filename)
        with gzip.open(path, 'r') as fin:
            for line in fin:
                fields = line.strip().split(' ')
                if fields[8] == code:
                    ua = line.strip().split('"')[3]
                    uas.append(ua)
    return uas


def get_all_urls(download_dir, files):
    """Returns a set of distinct urls given a list of log files"""
    counts = {}
    for file in files:
        filename = file.split('/')[-1]
        path = os.path.join(download_dir, filename)
        with gzip.open(path, 'r') as fin:
            for line in fin:
                url = line.strip().split(' ')[13]
                counts[url] = counts.get(url, 0) + 1
    return counts


def get_max_processing_times_by_url(urls, download_dir, files):
    """Gets the max of req_processing_time, target_processing_time, resp_processing_time given a list of urls"""
    result = []
    for url in urls:
        u = url[0]
        latencies = []
        max_req_processing_time = 0.000
        max_target_processing_time = 0.000
        max_resp_processing_time = 0.000
        for file in files:
            filename = file.split('/')[-1]
            path = os.path.join(download_dir, filename)
            with gzip.open(path, 'r') as fin:
                for line in fin:
                    fields = line.strip().split(' ')
                    if fields[13] == u:
                        # Determine max values
                        if float(fields[5]) > max_req_processing_time:
                            max_req_processing_time = float(fields[5])
                        if float(fields[6]) > max_target_processing_time:
                            max_target_processing_time = float(fields[6])
                        if float(fields[7]) > max_resp_processing_time:
                            max_resp_processing_time = float(fields[7])
        result.append(
            (url[0],
             str(url[1]),
             str(url[2]),
             str(max_req_processing_time),
             str(max_target_processing_time),
             str(max_resp_processing_time)))
    # result is a list of tuples (url,request_count,top_status_code,max_req_processing_time,max_target_processing_time,max_resp_processing_time)
    return result


def get_top_status_code_by_url(urls, download_dir, files):
    """Gets the top status code given a list of urls"""
    result = []
    for url in urls:
        resp_codes = []
        u = url[0]
        for file in files:
            filename = file.split('/')[-1]
            path = os.path.join(download_dir, filename)
            with gzip.open(path, 'r') as fin:
                for line in fin:
                    fields = line.strip().split(' ')
                    if fields[13] == u:
                        resp_codes.append(fields[8])
        top_status_code = collections.Counter(resp_codes).most_common(1)[0]
        result.append((url[0], url[1], int(top_status_code[0])))
    return result
