Reddit Dataset

Data from Pushshift

[Source](https://files.pushshift.io/reddit/)

[Introduction](https://arxiv.org/pdf/2001.08435.pdf) (Pushshift paper) 

=====================================================

Experiment Dataset

We download a part of the data from Pushshift Server

Year: 2019

Subreddits: r/science, r/technology

Months: 1-12 (from Jan. to Dec.)


- Submission (Post):
  - Total number: 14,384
  - Information: id, subreddit, subreddit_language, author, timestamp, title. 
  - Size: 2.4MB
  - More information in Table 1: Submissions data description in Pushshift paper 
- Comment:
  - Total number: 3,163,310
  - Information: id, subreddit, subreddit_language, text, type, author, timestamp, parent_id, controversial, score, submission_id, month.
  - Size : 722.5MB
  - Ratio of controversial comments: 5.1%
  - More information in Table 2: comments data description in Pushshift paper 


PS. comment dataset includes all levels comments.
