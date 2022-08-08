import boto3
MTURK_SANDBOX = 'https://mturk-requester-sandbox.us-east-1.amazonaws.com'
mturk = boto3.client('mturk',
   aws_access_key_id = "AKIA2J624RIXPFLDLE5Y",
   aws_secret_access_key = "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",
   region_name='us-east-1',
   endpoint_url = MTURK_SANDBOX
)
print("I have $", mturk.get_account_balance()['AvailableBalance'], " in my Sandbox account")

question = open('darma_prerequisite.xml', 'r').read()
new_hit = mturk.create_hit(
    Title = 'Darma Prerequisite Task (WARNING: This HIT may contain adult language. Worker discretion is advised.)',
    Description = 'This is a task to teach you about the instructions for the main Darma task, as well as to assess your understanding of those instructions.',
    Keywords = 'survey, prerequisite',
    Reward = '0.50',
    MaxAssignments = 1000,
    LifetimeInSeconds = 17280000,
    AssignmentDurationInSeconds = 600,
    AutoApprovalDelayInSeconds = 14400,
    Question = question,
)
print("A new HIT has been created. You can preview it here:")
print("https://workersandbox.mturk.com/mturk/preview?groupId=", new_hit['HIT']['HITGroupId'])
print ("HITID = " + new_hit['HIT']['HITId'] + " (Use to Get Results)")
# Remember to modify the URL above when you're publishing
# HITs to the live marketplace.
# Use: https://worker.mturk.com/mturk/preview?groupId=