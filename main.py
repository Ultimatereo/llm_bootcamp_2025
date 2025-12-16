from config import API_KEY, DEBUG
from data_utils import load_vacancies
from llm_request import (
    get_system_prompt,
    get_user_prompt,
    llm_request,
    get_report_system_prompt,
    get_report_user_prompt,
    llm_request_report,
)
from code_executor import execute_generated_code, CodeValidationError


def main() -> None:
    print(f"DEBUG={DEBUG}")
    print(f"API_KEY={'set' if API_KEY else 'not set'}")

    # TODO: здесь нужно получать реальный запрос пользователя (например, из Телеграма)
    user_task = "Посчитай средние зарплаты по seniority"

    # Загружаем данные
    df, structure, description = load_vacancies()

    # Готовим структурированное описание для промпта
    structure_info = {col: str(dtype) for col, dtype in structure.items()}
    description_info = description  # description уже словарь, не нужно to_dict()

    # Формируем system prompt (он не меняется между попытками)
    system_prompt = get_system_prompt()

    # Механизм повторных попыток
    max_attempts = 3
    previous_error = None
    previous_code = None

    for attempt in range(1, max_attempts + 1):
        print(f"\n--- Attempt {attempt}/{max_attempts} ---")
        
        # Формируем user prompt (с ошибкой, если это повторная попытка)
        user_prompt = get_user_prompt(
            user_task, 
            structure_info, 
            description_info,
            previous_error=previous_error,
            previous_code=previous_code,
        )

        # Запрашиваем код у LLM
        code = llm_request(user_prompt=user_prompt, system_prompt=system_prompt)

        try:
            analytics_result = execute_generated_code(code)
            # Успех!
            print("\n✅ Code executed successfully!")
            print("ANALYTICS_RESULT:")
            print(analytics_result)
            
            # Генерируем краткий отчет на основе результатов
            print("\n--- Generating analytical report ---")
            report_system_prompt = get_report_system_prompt()
            report_user_prompt = get_report_user_prompt(user_task, analytics_result)
            report = llm_request_report(report_user_prompt, report_system_prompt)
            
            print("\n" + "=" * 80)
            print("ANALYTICAL REPORT:")
            print("=" * 80)
            print(report)
            print("=" * 80)
            
            return
        except CodeValidationError as e:
            error_msg = str(e)
            print(f"❌ Generated code was rejected as unsafe: {error_msg}")
            print(f"Code snippet: {code[:500]}...")
            
            if attempt < max_attempts:
                previous_error = error_msg
                previous_code = code
                print(f"Retrying with error feedback...")
            else:
                print(f"\n❌ Failed after {max_attempts} attempts. Giving up.")
                return
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"❌ Code execution failed: {error_msg}")
            print(f"Code snippet: {code[:500]}...")
            
            if attempt < max_attempts:
                previous_error = error_msg
                previous_code = code
                print(f"Retrying with error feedback...")
            else:
                print(f"\n❌ Failed after {max_attempts} attempts. Giving up.")
                return


if __name__ == "__main__":
    main()


