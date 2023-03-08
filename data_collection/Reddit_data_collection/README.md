# **Reddit Data Instructions**

  This document provides instructions on the following tasks:
  1. **Live streaming** Reddit data to build the master log dataset
  2. **Reporting stats** on the data collected
  3. Collecting comments again after delay to **capture comment moderation**
  4. **Building threads** from the data collected
 
```
Server details
Server Name:            redditdata.isi.edu
IP Address:             128.9.36.23
```
Professor Jonathan May have the access to this server.

**Location of data**: /nas/home/asharma/data

**Location of live streaming scripts**: /nas/home/asharma/ISI_reddit


## **1. Live streaming Reddit data to build the master log dataset**

**Current Status**: Live streaming scripts for 6 subreddits are running in the background on the **reddit data** server. These scripts are collecting the comments and posts as and when they are being posted on Reddit.

**Note:** The data is being collected by a generator object **subreddit.stream.comments()**, which runs indefinitely waiting for the next commment.
Thus a single function could not be made for live streaming process because if that function was called for 1 subreddit, it would run indefinitely and the compiler would never run the second call for another sub reddit. Example below: after running line 1, the code in line 2 would never be executed.

```
live_stream('france')
live_stream('science')
```
Therefore, it was best to run independent scripts for different subreddits

**Note:** The While True loop is to make sure that if an exception occurs the compiler goes back to the generator object's for loop.

**How I started live streaming**:
- Connect to the **reddit data** server in FileZilla.
- Transfer scripts and Reddit credentials .json using FileZilla to the **reddit data** server
- Made these files readable and executable
- SSH to the **reddit data** server using terminal
- Run the live streaming script using nohup in order to run in the background.
Example:
First I changed the dir to /nas/home/asharma/data, then run the following command, so that nohup.out is generated in the data folder.
```
nohup python3 -u ../ISI_reddit/submission_stream_scripts/submission_stream_science.py &
```

  - The script connects to the Reddit server using Reddit API
  - Then, calls a generator object which generates comments as and when they are posted.
  - For each comment, a dictionary is created and collected in a dataframe.
  - Every hour, the dataframe is saved to a master log .csv file names like **com_stream_subreddit** in append mode.
- For downloading the collected data on your system, connect to **reddit data** server using FileZilla and transfer the .csv master log files from */nas/home/asharma/data* on the **reddit data** server to local machine.
- The script is programmed to run till the time Reddit gets comments, which is forever.
- To stop the script, run “ps ax” command to find the process id of the script and run “kill -9 <pid>” to kill the process on the **reddit data** server.
```
ps ax
kill -9 <pid>
```

## **2. Reporting stats on the data collected**
**Notebook: Stats_reporting_notebook.ipynb**

**Google sheet with stats: [reddit_live_streamed_data](https://docs.google.com/spreadsheets/d/1-hg9-o_x-K--JzjOr-cx4-2jPOsEDG5uB83DHPouAMQ/edit?usp=sharing)**

- Uploading the master log csv files downloaded from the **reddit data** server, in the notebook, for both comments and posts.
- Collecting the number of records and number of words.
(See notebook for details)
## **3. Collecting comments again after delay to capture comment moderation** 
**Notebook: Removed_com_collection_notebook.ipynb**

**Steps:**
- Upload the downloaded master log .csv file to the notebook.
- In the notebook (details provided in notebook):
  - Comments in the master log .csv file are loaded as a dataframe.
  - Define timestamp and selected comments from master log within that timestamp
  - Cleaning and processing the master log.
  - Comments IDs of comments from the master log .csv file are collected.
  - Then, using Reddit API, the above comment IDs are used to collect the comment’s body from Reddit when the time elapsed is greater than 24hrs.
  - Then, for the comments with body == “[removed]”, comments ids are collected as a list (removed_ids).
  - Now, a “removed" column is created in the master log dataframe which is True for comments ids in the removed_ids list and False for other comments.
  - After, the master log dataframe is updated with the removed column, we create a “darma_author” column that maps the original “author” to a drama author using a hash function.
  - Updated master log dataframe is saved as .csv files.
  - Removed comments can also be saved as a .csv file by selecting removed==True.
  
## **4. Building discussion threads from the data collected**
**Notebook: thread_generation_notebook.ipynb**

Using a bottom-up approach to generate threads: starting from the child node (removed comment) and going up each level by finding the parent of the leaf node until root (post) is reached.

**Steps:**
- For a particular timestamp 
- Upload the new master log .csv file for comments generated by removed_com_collection notebook. (see mote instruction in notebook)
- The thread generation script can be run for complete or a range of comments from .csv files. In the noteobook, we define the timestamp.
- Sort the generated thread from root to leaf.
- Generating threads with author, text, and permalink (for verification)
- Cleaning and Formating final json file according to offline protocol
- Generating .json file for offline protocol
- Applying 3 filters: gap removal filter (has a significant effect on science subreddit which is high volume), toxic author filter, and langID filter (has some effect on France subreddit)
  

