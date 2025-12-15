## Bootcamp LLM – Python project

### Установка окружения

1. Создайте виртуальное окружение (рекомендуется Python 3.12):

```bash
python3 -m venv .venv
```

2. Активируйте виртуальное окружение:

- macOS / Linux:

```bash
source .venv/bin/activate
```

- Windows (PowerShell):

```bash
.venv\\Scripts\\Activate.ps1
```

3. Установите зависимости:

```bash
pip install -r requirements.txt
```

### Переменные окружения (.env)

1. Скопируйте шаблон:

```bash
cp .env.example .env
```

2. Отредактируйте `.env` и заполните реальные значения.

Пример использования переменных окружения есть в файле `config.py`.


