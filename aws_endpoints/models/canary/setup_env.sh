sudo apt-get update
sudo apt install gcc
sudo apt install g++
cd prosocial-dialog
conda env create -f environment.yml
eval "$(conda shell.bash hook)"
conda deactivate
conda activate prosocial-dialog
cd ..
pip install -r requirements.txt