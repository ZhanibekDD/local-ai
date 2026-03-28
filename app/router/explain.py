"""Текст для /route: как устроен маршрутизатор (без вызова LLM)."""

ROUTE_HELP_RU = """
Маршрутизатор (до генерации ответа):

• Текст с «верни JSON», «json schema» → structured JSON (Qwen + Pydantic).
• Признаки кода (```, def, SQL, import…) → DeepSeek Coder.
• Слова про чек/накладную без файла → подсказка прислать фото/PDF.
• Документ в Telegram → OCR + извлечение (чек или накладная по имени/смыслу).
• Фото: подпись про документ → OCR; иначе → vision (Llama Vision).

Подсказки внизу ответа: модель и краткий reason (keyword_*).
"""


def route_help_short() -> str:
    return ROUTE_HELP_RU.strip()
