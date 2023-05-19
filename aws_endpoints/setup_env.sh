conda create --name darma python=3.9
eval "$(conda shell.bash hook)"
conda deactivate darma
conda activate darma
pip install -r requirements.txt