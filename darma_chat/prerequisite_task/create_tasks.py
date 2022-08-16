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
print("I have $", mturk.get_account_balance()['AvailableBalance'], " in my Sandbox account")

qr = [
    # In the US
    {
        'QualificationTypeId': '00000000000000000071',
        'Comparator': 'EqualTo',
        'LocaleValues': [
            {
                'Country': 'US',
            },
        ],
    },
    # Is an adult (over the age of 18)
    {
        'QualificationTypeId': '00000000000000000060',
        'Comparator': 'EqualTo',
        'IntegerValues': [
                1,
            ],
    },
    # Has a Hit approval rating of over 95%
    {
        'QualificationTypeId': '000000000000000000L0',
        'Comparator': 'GreaterThanOrEqualTo',
        'IntegerValues': [
                95,
            ],
    },
    # Fluency in French
    {
        'QualificationTypeId': '37AYPMB2R96GO8LN6LUXBB8N89XPE0',
        'Comparator': 'EqualTo',
        'IntegerValues': [
                1,
            ],
    },
]

question = open('darma_prerequisite.xml', 'r').read()
new_hit = mturk.create_hit(
    Title = 'Introduction to Pretend to be Toxic in a Chat Room (In French)',
    Description = '(WARNING: This HIT may contain adult language. Worker discretion is advised.) You will view a conversation based on a Reddit subreddit involving a toxic user. A moderator will moderate the toxic user, and you will continue the conversation imitating the toxic user. This will be an introduction to the main task, and the first step in getting qualification for the main task.',
    Keywords = 'survey, dialogue, moderation, french',
    Reward = '0.50',
    MaxAssignments = 10,
    LifetimeInSeconds = 17280000,
    AssignmentDurationInSeconds = 6000,
    AutoApprovalDelayInSeconds = 14400,
    Question = question,
    QualificationRequirements = qr,
)
print("A new HIT has been created. You can preview it here:")
print("https://workersandbox.mturk.com/mturk/preview?groupId=", new_hit['HIT']['HITGroupId'])
print ("HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)")
# Remember to modify the URL above when you're publishing
# HITs to the live marketplace.
# Use: https://worker.mturk.com/mturk/preview?groupId=