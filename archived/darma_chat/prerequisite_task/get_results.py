
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
import xmltodict

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


# qualifications for darma tasks
# sandbox->level->qual
QUALS = {}
QUALS[True] = {}
QUALS[False] = {}
QUALS[True][1] = "3RVX62BZKMVWO7PCBOSCECIBD3ZLP6"
QUALS[True][2] = "3KKCXPMQWHGOCAJCDUT1DUSX6YCIZA"
QUALS[False][1] = "3XDD2ODWMRSLBOD2MO6YN94TNLIGXL"
QUALS[False][2] = "30LLG2NWCXJYZOKJ56BHMEVV91290S"

# check the assignment
def check(a):
  xml_doc = xmltodict.parse(a['Answer'])
  print("Answers:")
  results = []
  for af in xml_doc['QuestionFormAnswers']['Answer']:
    res = f"\t{af['QuestionIdentifier']}->{af['FreeText']}"
    results.append(res)
    print(res)
  while True:
    ans = input("Do you want to qualify this user? (y/n): ")
    if ans.lower() not in ('y', 'n'):
      print("Please type 'y' or 'n'")
      continue
    qual = ans.lower() == 'y'
    break
  return qual, results


def main():
  parser = argparse.ArgumentParser(description="manually verify qualification tasks",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  addonoffarg(parser, 'debug', help="debug mode", default=False)
  parser.add_argument("--hit", type=str, required=True, help="hit to validate")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
  parser.add_argument("--level", type=int, choices=[1,2], help="which level of qualification to give", default=1)
  addonoffarg(parser, 'sandbox', help="look in sandbox instead of main", default=True)



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

  outfile = prepfile(args.outfile, 'w')
  mturk = getclient(os.environ.get('access_key'),
                    os.environ.get('secret_key'),
                    sandbox=args.sandbox)

  results = mturk.list_assignments_for_hit(HITId=args.hit, AssignmentStatuses=['Submitted'])
  for a in results['Assignments']:
    worker=a['WorkerId']
    id=a['AssignmentId']
    data = [worker, id]
    data.append(a['SubmitTime']-a['AcceptTime'])
    qualify, report = check(a)
    data.append(qualify)
    data.extend(report)
    message="Thank you for taking our qualification survey."
    if (qualify):
      qid = QUALS[args.sandbox][args.level]
      print(f"qid = {qid}, wid={worker}")
      message=message+" You are now qualified. We will contact you for an initial real dialogue task test."
      mturk.associate_qualification_with_worker(QualificationTypeId=qid, WorkerId=worker)
    mturk.approve_assignment(AssignmentId=id, RequesterFeedback=message)
    outfile.write("\t".join([str(x) for x in data])+"\n")


if __name__ == '__main__':
  main()



