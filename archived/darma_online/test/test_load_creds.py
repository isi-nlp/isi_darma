from darma_online.utils import load_credentials


def test_load_credentials(): 
    creds = load_credentials()
    print(creds)
    return 

if __name__ == "__main__": 
    test_load_credentials()