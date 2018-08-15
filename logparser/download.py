"""Helper methods to download logs from S3"""

from datetime import datetime, timedelta
import math
import boto3
import botocore
import os
from concurrent import futures
import shutil

def datetime_range(start, end, delta):
  """Returns all datetime objects of specified interval (eg 5 mins) between start and end datetime objects."""
  current = start
  while current < end:
    yield current
    current += delta


def start_end_dt_from_dates(from_, to_):
  """Returns datetime object given start and end date stamps such as '2018/07/01'."""
  from_timestamp = from_.split('/')
  from_year = int(from_timestamp[0])
  from_month = int(from_timestamp[1])
  from_day = int(from_timestamp[2])

  to_timestamp = to_.split('/')
  to_year = int(to_timestamp[0])
  to_month = int(to_timestamp[1])
  to_day = int(to_timestamp[2])

  #  ELB/ALB log files contain logs for the previous 5 minutes, so we add 5 minutes to start and end datetime
  return(datetime(from_year, from_month, from_day, 0, 5),datetime(to_year, to_month, to_day, 0, 5))


def list_datetime_range(dt_range):
  """Returns a list of datetime objects in 5 minute intervals given a datetime range."""
  return [dt.strftime('%Y%m%dT%H%MZ') for dt in 
        datetime_range(dt_range[0], dt_range[1],
        timedelta(minutes=5))]


def ceiling_dt(dt):
  """Round datetime object to the nearest 5 minute interval. From https://stackoverflow.com/questions/13071384/python-ceil-a-datetime-to-next-quarter-of-an-hour/32657466"""
  # how many secs have passed this hour
  nsecs = dt.minute*60 + dt.second + dt.microsecond*1e-6  
  # number of seconds to next quarter hour mark
  # Non-analytic (brute force is fun) way:  
  #   delta = next(x for x in xrange(0,3601,900) if x>=nsecs) - nsecs
  # analytic way:
  delta = math.ceil(nsecs / 300) * 300 - nsecs
  #time + number of seconds to quarter hour mark.
  return dt + timedelta(seconds=delta)


def start_end_dt_from_now(for_):
  """Returns start and end datetime objects given relative date and time stamps eg. 7 days/5 hours
  """
  _now = ceiling_dt(datetime.utcnow())

  if for_[1] in ('minute','minutes'):
    return (_now - timedelta(minutes=int(for_[0])), _now)
  elif for_[1] in ('hour','hours'):
    return (_now - timedelta(hours=int(for_[0])), _now)
  elif for_[1] in ('day','days'):
    return (_now - timedelta(days=int(for_[0])), _now)


def get_prefix_format(dt):
  """Generate s3 prefix given datetime string. The prefix is used to query for availables keys in a given S3 bucket
  """
  # TODO: modify prior to using, get these values from a config file or environment variables
  s3prefix_format = '{month}/{account}_elasticloadbalancing_{region}_{alb_name}_{timestamp}'
  account = '000000000000'
  region = 'us-east-1'
  alb_name = 'alb.name.id'
  datetime_object = datetime.strptime(dt, '%Y%m%dT%H%MZ')
  return s3prefix_format.format(month=datetime_object.strftime('%d'),account=account, region=region, alb_name=alb_name, timestamp=dt)

    
def get_prefix_list(dts):
  """Given a list of datetime objects, return a list of prefixes."""
  return list(map(lambda dt: get_prefix_format(dt), dts))


def get_keys_from_bucket(bucket):
  """Get an inventory of all items in a given S3 bucket. The list is then used to filter and build a list of objects to download."""
  # It is done this way instead of making a call to S3 to filter object(s) during each download operation because calling s3bucket.objects.filter for each download can be expensive
  print("Gathering info about contents in {}...".format(bucket))
  s3 = boto3.resource('s3')
  my_bucket = s3.Bucket(bucket)
  objs = list(my_bucket.objects.all())
  return list(map(lambda x: x.key, objs))


def download(bucket_name, download_dir, file):
  """Downloads a file from S3."""
  s3client = boto3.client('s3')
  s3 = boto3.resource('s3')

  filename = file.split('/')[-1]
  from_file = os.path.join(download_dir, filename)

  # Do not download if file already exists in the downloads directory
  if not os.path.exists(from_file):
    try:
      # print("{} does not exist in download dir. Downloading...".format(from_file))
      s3client.download_file(bucket_name, file, from_file)
    except botocore.exceptions.ClientError as e:
      if e.response['Error']['Code'] == "404":
        print("The object {} does not exist.".format(file))
      else:
        print("There was a problem downloading {}".format(file))


def download_all(bucket_name, download_dir, files_to_download):
  """Download all files given a list of filenames."""
  print("Downloading log files from s3. This might take a while...")
  if not os.path.exists(download_dir):
    os.makedirs(download_dir)
  # Download files concurrently as this can take a long time for large lists
  # TODO: get max_worker size from config file or env vars
  with futures.ThreadPoolExecutor(max_workers=20) as executor:
    for file in files_to_download:
      future = executor.submit(download, bucket_name, download_dir, file)
  print("DONE!\n\n")