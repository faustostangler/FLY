# print("Start!")
from infrastructure.config import ConfigAdapter


def main() -> None:
    try:
        config = ConfigAdapter()
        print(f"{config.fly_settings.app_name}")
        pass

    except Exception as e:
        print(e)

if __name__ == "__main__":
    main()
    print('done!')
