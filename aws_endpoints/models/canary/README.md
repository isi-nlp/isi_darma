# Canary endpoint set up instruction

Note: Please make sure your current working directory is ```isi_darma/aws_endpoints/models/canary``` before you start.

1. Clone the ```ProsocialDialog``` repository with ```git clone https://github.com/skywalker023/prosocial-dialog.git```.
2. Create and set up the conda environment with ```bash setup_env.sh```.
3. ```conda activate prosocial-dialog```
4. ```cd api```
5. Start the API server with ```uvicorn main:app --host 0.0.0.0 --port 7860```.

Please refer to https://github.com/skywalker023/prosocial-dialog for more information about Canary.
