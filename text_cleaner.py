import re
from typing import List


class TextCleaner:
    """
    Класс для очистки текстов комментариев ВКонтакте.
    Удаляет упоминания пользователей, эмодзи и пустые комментарии.
    """

    # Регулярное выражение для удаления упоминаний [id123|Имя] или [club123|Название]
    MENTION_PATTERN = re.compile(r'\[.*?\]')

    # Более точное регулярное выражение для эмодзи
    # Удаляем только конкретные диапазоны эмодзи, не затрагивая кириллицу
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols extended-A
        "\U00002600-\U000026FF"  # misc symbols
        "\U0000FE00-\U0000FE0F"  # variation selectors
        "\U0000200D"  # zero width joiner
        "\U000020E3"  # combining enclosing keycap
        "]+",
        flags=re.UNICODE
    )

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Очищает один текст:
        1. Удаляет упоминания [id123|Имя]
        2. Удаляет все эмодзи
        3. Убирает лишние пробелы

        :param text: Исходный текст
        :return: Очищенный текст (может быть пустым)
        """
        # Удаляем упоминания в квадратных скобках
        cleaned = TextCleaner.MENTION_PATTERN.sub('', text)

        # Удаляем эмодзи
        cleaned = TextCleaner.EMOJI_PATTERN.sub('', cleaned)

        # Убираем лишние пробелы и переносы строк
        cleaned = ' '.join(cleaned.split())

        # Удаляем знаки препинания в начале и конце
        cleaned = cleaned.strip(' ,.!?:;')

        return cleaned

    @classmethod
    def clean_texts(cls, texts: List[str]) -> List[str]:
        """
        Очищает список текстов и удаляет пустые/только из смайликов.

        :param texts: Список исходных текстов
        :return: Список очищенных непустых текстов
        """
        cleaned_texts = []

        for text in texts:
            cleaned = cls.clean_text(text)

            # Добавляем только если после очистки остался осмысленный текст
            # (минимум 2 символа, чтобы исключить одиночные знаки препинания)
            if cleaned and len(cleaned) >= 2:
                cleaned_texts.append(cleaned)

        return cleaned_texts

    @classmethod
    def clean_dict(cls, data: dict) -> dict:
        """
        Очищает словарь вида {url: [тексты]} и удаляет пустые комментарии.

        :param data: Словарь {url: [список текстов]}
        :return: Очищенный словарь
        """
        cleaned_data = {}

        for url, texts in data.items():
            cleaned_texts = cls.clean_texts(texts)
            cleaned_data[url] = cleaned_texts

        return cleaned_data


# ============================================
# Пример использования
# ============================================
if __name__ == "__main__":
    # Тестовые данные
    test_texts = [
        "[id123456|Иван], отличная новость! 👍🔥👏",
        "🎉🎊🎈",  # только смайлики
        "[club789|Группа] Спасибо за информацию!",
        "Просто текст без ничего",
        "[id111|Петр] [id222|Анна] 👍",  # только упоминания и смайлики
        "   ",  # пустой
        "Привет! Как дела? 😊",
        "Сәлам! Хәлләр ничек?",  # татарский
        "Эҕэрдэ! Туох сонун?",  # якутский
    ]

    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ОЧИСТКИ ТЕКСТОВ")
    print("=" * 60)

    print(f"\n📝 Исходных текстов: {len(test_texts)}")
    print("\nИсходные тексты:")
    for i, text in enumerate(test_texts, 1):
        print(f"   {i}. '{text}'")

    # Очищаем
    cleaned = TextCleaner.clean_texts(test_texts)

    print(f"\n✅ После очистки: {len(cleaned)}")
    print("\nОчищенные тексты:")
    for i, text in enumerate(cleaned, 1):
        print(f"   {i}. '{text}'")

    # Тест с словарем
    test_dict = {
        "https://vk.com/test1": ["[id1|Имя] 👍", "Нормальный текст"],
        "https://vk.com/test2": ["🎉🎊", "Еще текст"],
    }

    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ОЧИСТКИ СЛОВАРЯ")
    print("=" * 60)

    cleaned_dict = TextCleaner.clean_dict(test_dict)

    for url, texts in cleaned_dict.items():
        print(f"\n📊 {url}:")
        print(f"   Текстов: {len(texts)}")
        for text in texts:
            print(f"   - '{text}'")

    print("\n🎉 Тест завершен!")