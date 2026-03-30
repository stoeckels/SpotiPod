from pathlib import Path

from src.server import Client

def main():
    config_path = Path(__file__).resolve().parent / "config.json"
    client = Client(config_path=str(config_path))
    client.run(port=8000)

if __name__ == "__main__":
    main()