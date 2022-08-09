# Launching the Prerequisite Task

There are two files in this repository.
1. create_tasks.py
2. darma_prerequisite.xml

## create_tasks.py

This file contains the script to launch the prerequisite task.

The client() method on line 3 creates a link to Amazon's Mechanical Turk (MTurk). Use the aws_access_key_id and aws_secret_access_key to connect to an MTurk IAM account. Remove the endpoint_url part to launch the task without using the sandbox.

The "question" object on line 11 links to the darma_prerequisite.xml file.

The "new_hit" object is where the settings of the task, such as task compensation, is set.

## darma_prerequisite.xml

Add the HTML of the task here, starting after line 3.

## Launching the Task

To launch the task, run:

`python create_tasks.py`

## More Information

More detailed and step by step information can be found here:

<https://blog.mturk.com/tutorial-a-beginners-guide-to-crowdsourcing-ml-training-data-with-python-and-mturk-d8df4bdf2977>