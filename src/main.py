from backend.server import Client

def main():
    client = Client()
    client.run(port=8000)

if __name__ == "__main__":
    main()