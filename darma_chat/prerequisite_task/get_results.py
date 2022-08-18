import boto3
import os
from dotenv import load_dotenv
MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
load_dotenv()
myKey = os.environ['access_key']
my_access_key_id = os.environ.get('access_key')
print("access key:", my_access_key_id)
my_secret_key = os.environ.get('secret_key')
if (my_access_key_id is None) or (my_secret_key is None):
    print("Please create a \".env\" file in this directory containing your access_key and secret_key.")
    exit()
mturk = boto3.client('mturk',
   aws_access_key_id = my_access_key_id,
   aws_secret_access_key = my_secret_key,
   region_name='us-east-1',
   endpoint_url = MTURK_SANDBOX
)
# You will need the following library
# to help parse the XML answers supplied from MTurk
# Install it in your local environment with
# pip install xmltodict
import xmltodict
# Use the hit_id previously created
hit_id = '3E9ZFLPWOXR6LRXPLZNY4ZROJVIXIA'
# We are only publishing this task to one Worker
# So we will get back an array with one item if it has been completed
worker_results = mturk.list_assignments_for_hit(HITId=hit_id, AssignmentStatuses=['Submitted'])

if worker_results['NumResults'] > 0:
   for assignment in worker_results['Assignments']:
      xml_doc = xmltodict.parse(assignment['Answer'])
      
      print("Worker's answer was:")
      if type(xml_doc['QuestionFormAnswers']['Answer']) is list:
         # Multiple fields in HIT layout
         for answer_field in xml_doc['QuestionFormAnswers']['Answer']:
            print("For input field: ", answer_field['QuestionIdentifier'])
            print("Submitted answer: ", answer_field['FreeText'])
      else:
         # One field found in HIT layout
         print("For input field: ", xml_doc['QuestionFormAnswers']['Answer']['QuestionIdentifier'])
         print("Submitted answer: ", xml_doc['QuestionFormAnswers']['Answer']['FreeText'])
else:
   print("No results ready yet")