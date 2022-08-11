# Machine Translation Backend Setup

MT services have been configured to auto start inside an AWS instance linked to Prof. Jonathan May's AWS billing a/c. 

Sign-in URL: https://708591782446.signin.aws.amazon.com/console


* Name: ISI Darma MT
* Instance-ID: `i-050bc291661a69353`	
* IP address: `54.68.184.232`. 
  > This is a static elastic IP. 
    They charge money for the static address if the node is _not_ running.  
    Please release the address when this project is completed.


## Start / Stop Services

RTG 500Eng v1 and Meta's NLLB MT services are configured to autorun upon boot. So all you have to do is start / stop instance on AWS web console.

When the instance is running, you would see services

* RTG: http://54.68.184.232:6060/many-eng/v1
* NLLB: http://54.68.184.232:6062/nllb


## Development and Debugging 

While `ubuntu` user is the sudoer, we use `darma`, a non-sudoer to run these services.
You may run `sudo su darma` to switch from ubuntu to darma user, and add your ssh publickey to authorized_keys file.


### RTG 

Service file: `/home/darma/apps/rtg-many-eng/rtg-500engv1.service`

`sudo systemctl (status|start|stop|enable) rtg-500engv1`


### NLLB

Service file: `/home/darma/apps/nllb-serve/nllb-serve.service`

`sudo systemctl (status|start|stop|enable) nllb-serve`
