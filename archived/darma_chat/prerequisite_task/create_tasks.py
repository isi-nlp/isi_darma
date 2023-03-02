
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit
import boto3
import os
import json

scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  if type(fh) is str:
    fh = open(fh, code)
  ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret


def getclient(access_key, secret_key, sandbox=False, region="us-east-1"):
  MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
  params = {}
  params["aws_access_key_id"] = access_key
  params["aws_secret_access_key"] = secret_key
  params["region_name"] = region
  if sandbox:
    params["endpoint_url"] = MTURK_SANDBOX
  return boto3.client('mturk', **params)

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)



QUALS = {}
QUALS["US"] =  {
          'QualificationTypeId': '00000000000000000071',
          'Comparator': 'In',
          'LocaleValues': [
              {
                  'Country': 'US',
              },
              {
                  'Country': 'DZ', # algeria
              },
              {
                  'Country': 'CA', # canada
              },
              {
                  'Country': 'FR', # france
              },
              {
                  'Country': 'HT', # haiti
              },
              {
                  'Country': 'BE', # belgium
              }
            
          ],
      }
QUALS["ADULT"] = {
          'QualificationTypeId': '00000000000000000060',
          'Comparator': 'EqualTo',
          'IntegerValues': [
                  1,
              ],
      }

QUALS["95"] =   {
          'QualificationTypeId': '000000000000000000L0',
          'Comparator': 'GreaterThanOrEqualTo',
          'IntegerValues': [
                  95,
              ],
      }
# only applies to main. sandbox doesn't use it but if you need to
# the qid is 37AYPMB2R96GO8LN6LUXBB8N89XPE0
QUALS["FRENCH"] =   {
          'QualificationTypeId': '35ZCVQVYQ96BLEX64XPM415HA9RSG8',
          'Comparator': 'EqualTo',
          'IntegerValues': [
                  1,
              ],
      }

BOXBANLIST = ['FRENCH']

def main():
  parser = argparse.ArgumentParser(description="create qualification task",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  addonoffarg(parser, 'debug', help="debug mode", default=False)
  parser.add_argument("--hitfile", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input hit (xml) file")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--assignments", "-a", type=int, default=10,  help="number of assignments per HIT")
  parser.add_argument("--reward", "-r", type=float, default=0.5,  help="reward, in dollars")
  parser.add_argument("--quals", "-q", nargs='+', choices=['US', 'ADULT', '95', 'FRENCH'], default=['US', 'ADULT', '95', 'FRENCH'], type=str, help="which qualifications to include") 
  parser.add_argument("--title", type=str, help="hit title", default="'Introduction to Pretend to be Toxic in a Chat Room (In French)")
  parser.add_argument("--description", type=str, help="hit description", default="(WARNING: This HIT contains explicit language in English and French. Worker discretion is advised.) You will view a conversation based on a Reddit subreddit involving a toxic user. A bot moderator will moderate the toxic user, and you will continue the conversation imitating the toxic user. This will be an introduction to the main task, and the first step in getting qualification for the main task.")
  parser.add_argument("--keywords", type=str, help="hit keywords", default='survey, dialogue, moderation, french')
  addonoffarg(parser, 'sandbox', help="submit to sandbox instead of main", default=True)



  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  if args.debug:
    print(workdir)
  else:
    atexit.register(cleanwork)


  hitfile = prepfile(args.hitfile, 'r')
  outfile = prepfile(args.outfile, 'w')



  mturk = getclient(os.environ.get('access_key'),
                    os.environ.get('secret_key'),
                    sandbox=args.sandbox)

  
  qr = []
  for qual in args.quals:
    if args.sandbox and qual in BOXBANLIST:
      print(f"Not including {qual}; not enabled for sandbox.")
    else:
      qr.append(QUALS[qual])

  new_hit = mturk.create_hit(
      Title = args.title,
      Description = args.description,
      Keywords = args.keywords,
      Reward = str(args.reward),
      MaxAssignments = args.assignments,
      LifetimeInSeconds = 17280000,
      AssignmentDurationInSeconds = 6000,
      AutoApprovalDelayInSeconds = 14400,
      Question = hitfile.read(),
      QualificationRequirements = qr,
  )
  url_prefix = "https://worker.mturk.com/mturk/preview?groupId="
  if args.sandbox:
    url_prefix="https://workersandbox.mturk.com/mturk/preview?groupId="
  # clean up ugly XML
  del new_hit['HIT']['Question']
  outfile.write(f"{url_prefix}{new_hit['HIT']['HITGroupId']}\n")
  outfile.write(new_hit['HIT']['HITId']+"\n")
  outfile.write(json.dumps(new_hit,indent=2, sort_keys=True, default=str)+"\n")
  #print(new_hit)
  #json.dump(new_hit, outfile, indent=2)

if __name__ == '__main__':
  main()



