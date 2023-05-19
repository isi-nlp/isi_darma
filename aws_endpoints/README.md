# Create model endpoint on AWS EC2

## Set up instructions
1. Clone the ```isi_darma``` repository with ```git@github.com:isi-nlp/isi_darma.git```.
2. ```cd isi_darma/aws_endpoints```
3. Install Miniconda with ```bash install_conda.sh```. Note: This script is for Linux with x86_64 architecture. If you use a different system architecture, please change to the corresponding download link. You can find the links [here](https://conda.io/projects/conda/en/latest/user-guide/install/linux.html).
4. Create and set up the conda environment for the endpoint with ```bash setup_env.sh```
5. ```cd apis/<model_name>```
6. Start the API server with ```uvicorn main:app --host 0.0.0.0 --port 7860```.
