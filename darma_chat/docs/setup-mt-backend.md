# Machine Translation Backend Setup

MT services have been configured to auto start inside an AWS instance linked to Prof. Jonathan May's AWS billing a/c. 

Sign-in URL: https://708591782446.signin.aws.amazon.com/console


* Name: ISI Darma MT
* Instance-ID: `i-050bc291661a69353`	
* IP address: `54.68.184.232`. 
  > This is a static elastic IP. 
    AWS charges money for static addresses if the nodes are _not_ running.  
    Please release this address when this project is completed.


## Start / Stop Services

RTG 500Eng v1 and Meta's NLLB MT services are configured to autorun upon boot. So all you have to do is start / stop instance on AWS web console.

When the instance is running, you would see services

* RTG: http://54.68.184.232:6060/many-eng/v1
* NLLB: http://54.68.184.232:6062/nllb


## Development and Debugging 

While `ubuntu` user is the sudoer, we use `darma`, a non-sudoer to run these services.
You may run `sudo su darma` to switch from ubuntu to darma user, and add your ssh publickey to authorized_keys file.


### RTG 
`sudo systemctl (status|start|stop|enable) rtg-500engv1`

Service file is at `/home/darma/apps/rtg-many-eng/rtg-500engv1.service`

It has the following contents
```ini
[Unit]
    Description=RTG 500-1 server
    After=network.target

 [Service]
    User=darma
    Group=darma
    WorkingDirectory=/home/darma/apps/rtg-many-eng
    Environment="PATH=/home/darma/.conda/envs/rtg/bin"
    ExecStart=/home/darma/.conda/envs/rtg/bin/uwsgi --http 0.0.0.0:6060 --module rtg.serve.app:app --pyargv "rtg500eng-tfm9L6L768d-bsz720k-stp200k-ens05 -b /many-eng/v1"

[Install]
    WantedBy=multi-user.target

```


### NLLB

`sudo systemctl (status|start|stop|enable) nllb-serve`

Service file: `/home/darma/apps/nllb-serve/nllb-serve.service`
It has the following contents
```ini
[Unit]
    Description=NLLB 200-200 MT server
    After=network.target

 [Service]
    User=darma
    Group=darma
    WorkingDirectory=/home/darma/apps/nllb-serve
    Environment="PATH="/home/darma/.conda/envs/rtg/bin"
    ExecStart=/home/darma/.conda/envs/rtg/bin/uwsgi --http 0.0.0.0:6062 --module nllb_serve.app:app --pyargv "-b /nllb"

[Install]
    WantedBy=multi-user.target
```



