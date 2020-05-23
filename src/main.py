from pathlib import Path

from notifier import fetch, send


def main():
    print("STARTING!")
    config_path = Path(__file__).parent / 'resources' / 'config.json'
    fetch.run(config_path)
    send.run()


if __name__ == "__main__":
    main()
