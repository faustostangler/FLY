print("Start!")
from infrastructure.config import ConfigAdapter

def main() -> None:
    try:
        config = ConfigAdapter()

    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
    print('done!')
