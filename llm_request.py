import os
import re
from typing import Any, Dict

import requests


def get_system_prompt() -> str:
    """
    System prompt for the LLM that enforces:
    - pure Python code output (no explanations, no markdown),
    - local executability,
    - reading data from vacancies.json,
    - saving plots to disk and returning paths to them in a dictionary.
    """
    return (
        "You are an expert Python data analyst and engineer. "
        "You write **only** pure executable Python 3 code (no markdown, "
        "no backticks, no shell or bash commands, no comments outside of Python code). "
        "Your code will be executed in a local environment that already has "
        "pandas, matplotlib, seaborn, numpy and the standard library installed.\n\n"
        "You receive a natural-language user task and a description of a dataset "
        "that has already been preprocessed in the caller. The caller uses a helper "
        "function 'load_vacancies' from the local module 'data_utils' to load the "
        "data from 'vacancies.json' and flatten the nested 'data' field into a "
        "convenient DataFrame.\n\n"
        "Your job is to:\n"
        "1. Import and use the helper function from 'data_utils' instead of reading "
        "the JSON file directly. Your typical pattern should be:\n"
        "   from data_utils import load_vacancies\n"
        "   df, structure, description = load_vacancies()\n"
        "2. Compute exactly the analytics requested by the user (aggregations, "
        "statistics, segments, time series, etc.).\n"
        "3. If the user asks for plots, create them using matplotlib or seaborn, "
        "save them to PNG files on disk, and include their file paths in the result.\n"
        "4. At the end of the script, construct a Python dictionary named "
        "'ANALYTICS_RESULT' that contains:\n"
        "   - a key 'metrics' with a nested dict of all numeric and other metrics you computed;\n"
        "   - a key 'plots' with a list of dicts, each containing at least 'name' and 'path' "
        "for every saved plot.\n"
        "5. Do not print huge dataframes; if needed, aggregate or sample them. Focus on "
        "meaningful metrics.\n\n"
        "Important constraints:\n"
        "- Do not import or use any network libraries or call remote APIs.\n"
        "- Do not read from or write to any files other than 'vacancies.json' (through "
        "the provided helper function) and image files for plots.\n"
        "- Do not install packages. Use only pandas, matplotlib, seaborn, numpy, os, pathlib, datetime.\n"
        "- Never output any bash/shell snippets or commands (such as rm, cd, ls, chmod, curl, wget, etc.).\n"
        "- The ONLY thing you must return to the caller is valid Python code. "
        "No explanations, no comments outside the code block, no additional text."
    )


def get_user_prompt(
    user_task: str,
    structure: Dict[str, Any],
    df_description: Dict[str, Any],
    previous_error: str | None = None,
    previous_code: str | None = None,
) -> str:
    """
    Build the user prompt that describes:
    - the user's analytic request,
    - the high-level structure of the DataFrame,
    - precomputed description/statistics.
    - optionally: previous error and code for retry attempts.
    """
    base_prompt = (
        "User task (in natural language):\n"
        f"{user_task}\n\n"
        "Current DataFrame structure (column -> dtype as string):\n"
        f"{structure}\n\n"
        "Precomputed description/statistics of the dataset (per-column stats):\n"
        f"{df_description}\n\n"
    )
    
    if previous_error and previous_code:
        retry_section = (
            "\n"
            "⚠️ IMPORTANT: The previous code attempt failed with an error. "
            "Please fix the code based on the error message below.\n\n"
            f"Previous error: {previous_error}\n\n"
            "Previous code (for reference, fix the issues):\n"
            f"```python\n{previous_code[:2000]}\n```\n\n"
            "Please generate corrected Python code that addresses the error above. "
            "Make sure to follow all constraints from the system prompt.\n"
        )
        return base_prompt + retry_section
    else:
        return (
            base_prompt
            + "Write Python code that, when executed locally, performs the requested analysis "
            "on 'vacancies.json', builds any requested plots, saves them as PNG files, and "
            "populates the 'ANALYTICS_RESULT' dictionary as specified in the system prompt."
        )


def _extract_code_block(text: str) -> str:
    """
    Извлекает чистый Python-код из ответа модели:
    - убирает ```python ... ``` или ``` ... ``` обёртки,
    - обрезает лишние пробелы.
    """
    # Ищем тройные кавычки ```...```
    code_fence_pattern = re.compile(r"```(?:python)?(.*)```", re.DOTALL | re.IGNORECASE)
    match = code_fence_pattern.search(text)
    if match:
        code = match.group(1)
    else:
        code = text

    # Убираем возможные префиксы типа "Code:" и ведущие/хвостовые пробелы
    code = code.strip()
    if code.lower().startswith("code:"):
        code = code[5:].strip()

    return code


def get_report_system_prompt() -> str:
    """
    System prompt for generating a human-readable analytical report.
    """
    return (
        "You are an experienced data analyst preparing a brief analytical report. "
        "Your task is to write a clear, concise, and professional summary of the analysis results "
        "in natural language, as if you were presenting findings to a stakeholder.\n\n"
        "Guidelines:\n"
        "- Write in Russian (if the user's question was in Russian) or English (if in English).\n"
        "- Be extremely concise: write ONLY 1 paragraph maximum (3-5 sentences).\n"
        "- Highlight the most important findings and insights from the metrics.\n"
        "- Reference the generated plots by their names when discussing visualizations.\n"
        "- Use specific numbers from the metrics to support your conclusions.\n"
        "- Write in a professional but accessible tone.\n"
        "- Do not include technical jargon unless necessary.\n"
        "- Combine context, key findings, and conclusions in a single paragraph.\n\n"
        "Important: Always mention plot names when referring to visualizations. "
        "For example: 'Как видно на графике \"salary_distribution.png\"...' or "
        "'The chart \"median_salaries.png\" shows that...'"
    )


def get_report_user_prompt(user_task: str, analytics_result: Dict[str, Any]) -> str:
    """
    Build the user prompt for report generation that includes:
    - the original user's question/task,
    - the computed analytics results (metrics and plots).
    """
    import json
    
    # Форматируем метрики для читаемости
    metrics_str = json.dumps(analytics_result.get("metrics", {}), ensure_ascii=False, indent=2)
    
    # Форматируем информацию о графиках
    plots_info = analytics_result.get("plots", [])
    plots_str = ""
    if plots_info:
        plots_str = "\nGenerated plots:\n"
        for plot in plots_info:
            plot_name = plot.get("name", "unnamed")
            plot_path = plot.get("path", "unknown")
            plots_str += f"- {plot_name} (saved at: {plot_path})\n"
    else:
        plots_str = "\nNo plots were generated for this analysis.\n"
    
    return (
        f"Original user question/task:\n{user_task}\n\n"
        f"Analytics results:\n"
        f"Metrics:\n{metrics_str}\n"
        f"{plots_str}\n"
        "Please write a very brief analytical report (1 paragraph, 3-5 sentences) that answers the user's question, "
        "highlights the most important findings from the metrics, and references the plots when discussing visualizations. "
        "Write as if you are a data analyst presenting findings to a stakeholder. Be concise and to the point."
    )


def llm_request(user_prompt: str, system_prompt: str) -> str:
    """
    Make a request to the Groq LLM and return the cleaned code string.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['API_KEY']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
    }

    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()

    raw_content = data["choices"][0]["message"]["content"]
    return _extract_code_block(raw_content)


def llm_request_report(user_prompt: str, system_prompt: str) -> str:
    """
    Make a request to the Groq LLM for generating a text report (not code).
    Returns the raw text response without code extraction.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['API_KEY']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,  # Немного выше для более естественного текста
    }

    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()

    return data["choices"][0]["message"]["content"].strip()

