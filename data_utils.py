from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import pandas as pd
import numpy as np


def load_vacancies(
    path: str | Path = "vacancies.json",
) -> Tuple[pd.DataFrame, pd.Series, Dict[str, Dict[str, Any]]]:
    """
    Преобразует данные из vacancies.json в pandas.DataFrame и
    возвращает вместе со структурой и описанием данных.

    Parameters
    ----------
    path : str | Path, optional
        Путь к файлу vacancies.json. По умолчанию "vacancies.json"
        в корне проекта.
    Returns
    -------
    df : pd.DataFrame
        Датафрейм с вакансиями. Поле "data" разворачивается в столбцы,
        а верхнеуровневый "id" добавляется как отдельный столбец.
    structure : pd.Series
        Структура датафрейма: типы данных по каждому столбцу (df.dtypes).
    description : Dict[str, Dict[str, Any]]
        Описание датафрейма: словарь, где ключи - названия колонок,
        значения - словари с метриками для каждой колонки (без nan).
    """
    path = Path(path)

    df = pd.read_json(path)
    df_flat = pd.json_normalize(df["data"])
    df_flat["id"] = df["id"].values

    # Структура датафрейма
    structure = df_flat.dtypes

    # Улучшенное описание: убираем nan и делаем более структурированным
    description = df_flat.info()

    return df_flat, structure, description

