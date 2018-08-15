import os
import sys
import argparse
from datetime import datetime, timedelta
from cli import setup_cli
import parser as logparser
import download as downloader
import collections

def valid_date(s):
  """Ensures that date stamp entered is valid. Returns datetime object."""
  try:
    # Date stamp must be in %Y/%m/%d format
    return datetime.strptime(s, "%Y/%m/%d")
  except ValueError:
    msg = "Not a valid date format: '{0}'.".format(s)
    raise argparse.ArgumentTypeError(msg)


def validate_args(args, parser):
  """Validates the arguments from argparse. Prints usage output on error."""
  if args.get_option not in ('getcodes','geturls','getUAs','getreport'):
    message = 'get_option must be one of [getcodes, geturls, getUAs, getreport].'
    parser.error(message)
  
  if args.get_option in ('geturls','getUAs') and args.code is None:
    message = 'code must be specified'
    parser.error(message)
  
  if not args.from_ and not args.to and not args.for_:
    message = 'Please specify either an absolute or relative datetime range'
    parser.error(message)

  if args.from_ and not args.to:
    message = 'Please specify an end date'
    parser.error(message)
  
  if args.to and not args.from_:
    message = 'Please specify a start date'
    parser.error(message)
  
  if args.for_ and (args.from_ or args.to):
    message = 'You can only specify a relative duration in the absence of absolute date stamps'
    parser.error(message)

  if args.to < args.from_:
    message = 'Start date must be older than end date'
    parser.error(message)
    
  if args.for_:
    params = args.for_
    if (not params[0].isdigit()) or (params[1].lower() not in ('day','days','hour','hours','minute','minutes')):
      message = 'Cannot parse relative date/time stamps'
      parser.error(message)


def get_dt_range(args):
  """Gets date time range given input"""
  if args.from_:
    return (args.from_ + timedelta(minutes=5), args.to + timedelta(minutes=5))
  else:
    return downloader.start_end_dt_from_now(args.for_)


def process_results(results, field, args):
  """Returns list of results depending on whether there is a max value"""
  counter = collections.Counter(results)
  most_common = []
  top = ""
  if args.max:
    most_common = counter.most_common(int(args.max))
    top = 'Top {} '.format(args.max)
  else:
    most_common = counter.most_common()
    top = 'All '

  print_results(top, field, most_common)


def print_results(top, field, results):
  """Prints results for getcodes, geturls, getUAs"""
  print("{}{}s".format(top, field))
  print("==============")
  for entry in results:
    print("{} - {}".format(entry[1], entry[0]))


def main():

  parser = setup_cli(epilog='Script to parse ALB logs')

  parser.add_argument('get_option', help = '[getcodes, geturls, getUAs, getreport]')
  parser.add_argument("--code", metavar='<http_status_code>' , help="http error code to filter by")
  parser.add_argument("--from", dest='from_', metavar='<from_date>', type = valid_date, help="start date for search")
  parser.add_argument("--to", metavar='<from_date>', type = valid_date, help="end date for search")
  parser.add_argument("--max", metavar='<count>', help="Top N items to display")
  parser.add_argument("--for", dest='for_', nargs=2, metavar='<relative_time>', help="Relative duration")

  args = parser.parse_args()

  validate_args(args, parser)

  # TODO: Modify before use, get this from env var
  bucket_name = 'bucket'
  download_dir = '{}/{}/'.format(os.getcwd(),'logs')
  dts = downloader.list_datetime_range(get_dt_range(args))
  prefixes = downloader.get_prefix_list(dts)
  keys = downloader.get_keys_from_bucket(bucket_name)
  print("DONE!")

  files = []

  # Build a list of files we need to parse
  for prefix in prefixes:
    for key in filter(lambda k: prefix in k, keys):
      filename = key.split('/')[-1]
      files.append(key)

  downloader.download_all(bucket_name, download_dir, files)
  
  if args.get_option == 'getcodes':
    codes = logparser.get_codes(download_dir, files)
    process_results(codes, 'Error Code', args)

  if args.get_option == 'geturls':
    urls = logparser.get_urls_by_error(download_dir, files, args.code)
    process_results(urls, 'URL', args)

  if args.get_option == 'getUAs':
    uas = logparser.get_uas_by_error(download_dir, files, args.code)
    process_results(uas, 'User Agent', args)

  if args.get_option == 'getreport':
    results = logparser.get_all_urls(download_dir, files)

    sorted_results = []
    if args.max:
      max = int(args.max)
      sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)[:max]
    else:
      # this is an expensive operation, cap at 10 items if no max value specified
      sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)[:10]

    top_status_codes = logparser.get_top_status_code_by_url(sorted_results, download_dir, files)
    report = logparser.get_max_processing_times_by_url(top_status_codes, download_dir, files)
    
    now = datetime.now().strftime('%Y%m%dT%H%M%S')
    report_file = '{}/{}'.format(os.getcwd(),'report_{}.csv'.format(now))
    header = "url,request_count,top_status_code,max_req_processing_time,max_target_processing_time,max_resp_processing_time\n"

    # write to csv file
    try:
      with open(report_file, 'a') as f:
        f.write(header)
        print(header)
        for r in report:
          f.write(",".join(x for x in r))
          print(",".join(x for x in r))
    except IOError:
      msg = ("There was a problem writing report to {}.".format(report_file))
      print(msg)
    
    print("\n\nReport generated here - {}".format(report_file))

if __name__ == "__main__":
    main()