# Cosmo-xl endpoint set up instruction

Note: Please make sure your current working directory is ```isi_darma/aws_endpoints/models/cosmo-xl``` before you start.

1. Create and set up the conda environment with ```bash setup_env.sh```.
3. ```conda activate cosmo-xl```
4. ```cd api```
5. Start the API server with ```uvicorn main:app --host 0.0.0.0 --port 7860```.

Please refer to https://huggingface.co/allenai/cosmo-xl for more information about Cosmo-xl.
