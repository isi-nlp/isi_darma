conda create --name cosmo-xl python=3.9 -y
eval "$(conda shell.bash hook)"
conda deactivate
conda activate cosmo-xl
pip install -r requirements.txt