from src.server import Client

def main():
    client = Client(config_path="config.json")
    client.run(port=8000)

if __name__ == "__main__":
    main()