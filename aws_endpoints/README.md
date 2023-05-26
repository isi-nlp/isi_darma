# Create model endpoint on AWS EC2

## Set up instructions
1. Clone the ```isi_darma``` repository with ```git clone git@github.com:isi-nlp/isi_darma.git```.
2. ```cd isi_darma/aws_endpoints```
3. Install Miniconda with ```bash install_conda.sh```. Note: This script is for Linux with x86_64 architecture. If you use a different system architecture, please change to the corresponding download link. You can find the links [here](https://conda.io/projects/conda/en/latest/user-guide/install/linux.html).
4. Restart shell and run ```cd isi_darma/aws_endpoints```.
5. ```cd models/<model_name>``` and follow the model specific instructions to set up the conda environment and start the API server.
