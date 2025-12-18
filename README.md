## Bootcamp LLM – Telegram-бот для аналитики вакансий

Проект представляет собой Telegram-бота, который использует LLM (Groq API с моделью `llama-3.3-70b-versatile`) для выполнения аналитических задач по данным о вакансиях на естественном языке.

### Как это работает

1. Пользователь отправляет запрос на естественном языке в Telegram (например: _"Посчитай средние зарплаты по seniority"_)
2. Бот проверяет релевантность запроса к данным о вакансиях
3. LLM генерирует Python-код для выполнения анализа
4. Код безопасно выполняется в sandbox-окружении
5. Результаты (метрики + графики) отправляются пользователю с кратким текстовым отчётом

### Структура проекта

```
├── telegram_bot.py        # Telegram-бот (основной entry point)
├── main.py                # CLI-версия для локального тестирования
├── llm_request.py         # Запросы к Groq API + промпты
├── code_executor.py       # Безопасное выполнение сгенерированного кода
├── data_utils.py          # Загрузка данных и описаний
├── config.py              # Конфигурация и переменные окружения
├── data/
│   ├── o.json             # Очищенные данные о вакансиях
│   ├── description.json   # Описание структуры данных для LLM
│   └── o_llm_example.json # Пример извлечённых LLM-данных из описаний
├── parser_scripts/
│   ├── parser.py          # Скрипт очистки и нормализации данных
│   └── parserWithLLM.py   # LLM-парсер для извлечения признаков из описаний
├── presentation/
│   └── Буткемп Защита 17_12.ipynb  # Jupyter Notebook для презентации
└── generated_code/        # Папка со сгенерированными скриптами (создаётся автоматически)
```

### Подготовка данных

Исходные данные (`vacancies.json`) были обработаны командой:

1. **Очистка и нормализация** (`parser_scripts/parser.py`):
   - Нормализация зарплат (от/до, валюта, налоги)
   - Извлечение локации (город, страна, remote/relocate)
   - Очистка HTML-тегов из описаний
   - Унификация полей

   ```bash
   python parser_scripts/parser.py --input vacancies.json --output data/o.json
   ```

2. **LLM-извлечение признаков** (`parser_scripts/parserWithLLM.py`) — опционально:
   - Извлечение soft/hard skills, требований к английскому, бенефитов и т.д.
   - Использует локальную Ollama с моделью Gemma3

   ```bash
   python parser_scripts/parserWithLLM.py --input vacancies.json --output data/o_llm_example.json
   ```

### Установка окружения для запуска бота и запросов в грок

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
.venv\Scripts\Activate.ps1
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

2. Отредактируйте `.env` и заполните значения:

```env
# Groq API Key (https://console.groq.com/)
API_KEY=gsk_...

# Telegram Bot Token (от @BotFather)
TELEGRAM_BOT_TOKEN=1234567890:ABC...

# Режим отладки (опционально)
DEBUG=false
```

### Запуск

**Telegram-бот:**

```bash
python telegram_bot.py
```

**CLI-версия (для тестирования):**

```bash
python main.py
```

### Примеры запросов

- _"Посчитай средние зарплаты по seniority"_
- _"Построй график распределения зарплат"_
- _"Сравни зарплаты в Москве и Санкт-Петербурге"_
- _"Какие технологии самые популярные в стеке?"_
- _"Покажи топ-10 компаний по количеству вакансий"_

### Безопасность

Сгенерированный код проходит валидацию перед выполнением:
- Разрешены только безопасные модули (`pandas`, `matplotlib`, `seaborn`, `numpy`, `os`, `pathlib`, `datetime`)
- Запрещены опасные вызовы (`exec`, `eval`, `open`, `system`, `popen`)
- Запрещены сетевые библиотеки и системные вызовы

### Технологии

- **LLM**: Groq API (`llama-3.3-70b-versatile`)
- **Telegram**: aiogram 3.x
- **Аналитика**: pandas, matplotlib, seaborn
- **Локальный LLM (для парсинга)**: Ollama + Gemma3
