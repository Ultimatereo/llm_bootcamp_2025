from config import API_KEY, DEBUG

import pandas as pd
import requests


def main() -> None:
    print(f"DEBUG={DEBUG}")
    print(f"API_KEY={'set' if API_KEY else 'not set'}")

    # Пример использования pandas и requests, чтобы было понятно, что всё работает
    response = requests.get("https://httpbin.org/json")
    response.raise_for_status()
    data = response.json()

    df = pd.json_normalize(data)
    print("DataFrame head:")
    print(df.head())


if __name__ == "__main__":
    main()


