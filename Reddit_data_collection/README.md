# **Reddit Data Instructions**

  This document provides instructions on the following tasks:
  1. Live streaming Reddit data to build the master log dataset
  2. Collecting Reddit data to mark “removed” comments
  3. Building discussion threads from the data collected
  4. Reporting stats on the data collected

## **1. Live streaming Reddit data to build the master log dataset**

**Current Status**: Live streaming scripts for 6 subreddits are running in the background on the effect server. These scripts are collecting the comments and posts as and when they are being posted on Reddit.

**Steps**:
- Connect to the Effect server in FileZilla (credentials)
- Transfer scripts and Reddit credentials .json using FileZilla to the Effect server
- SSH to the Effect server using terminal
- Run the live streaming script using nohup to run the script in the background.
  - The script connects to the Reddit server using Reddit API
  - Then, calls a generator object which generates comments as and when they are posted.
  - For each comment, a dictionary is created and collected in a dataframe.
  - Every hour, the dataframe is saved to a master log .csv file in append mode.
- For downloading the collected data on your system, connect to FileZilla and transfer the .csv master log files from the Effect server.
- The script is programmed to run till the time Reddit gets comments, which is forever.
- To stop the script, run “ps ax” command to find the process id of the script and run “kill -9 <pid>” to kill the process.

## **2. Collecting Reddit data to mark “removed” comments**

**Steps:**
- Upload the downloaded master log .csv file to the notebook.Comments in the master log .csv file are loaded as a dataframe.
- In the notebook:
  - Comments in the master log .csv file are loaded as a dataframe.
  - Comments IDs of comments from the master log .csv file are collected.
  - Then, using Reddit API, the above comment IDs are used to collect the comment’s body from Reddit when the time elapsed is greater than 24hrs.
  - Then, for the comments with body == “[removed]”, comments ids are collected as a list (removed_ids).
  - Now, a “removed" column is created in the master log dataframe which is True for comments ids in the removed_ids list and False for other comments.
  - After, the master log dataframe is updated with the removed column, we create a “darma_author” column that maps the original “author” to a drama author using a hash function.
  - Updated master log dataframe is saved as .csv files.
  - Removed comments can also be saved as a .csv file by selecting removed==True.
  
## **3. Building discussion threads from the data collected**
  
Using a bottom-up approach to generate threads: starting from the child node (removed comment) and going up each level by finding the parent of the leaf node until root (post) is reached.

**Steps:**
- Upload the master log .csv file for posts and comments to the notebook.
- The thread generation script can be run for complete or a range of comments from .csv files.
- Generating subsequent .json file which only contains author, darma_author and text, and permalink for verification.
- Generating .json file for offline protocol
- Applying 3 filters: gap removal filter (has a significant effect on science subreddit which is high volume), toxic author filter, and langID filter (has some effect on France subreddit)

## **4. Reporting stets on the data collected**

Uploading the master_log in the notebook and reading the number of records and number of words.
