import re
from typing import List, Dict, Set
from language_detector import LanguageDetector


class LanguageSwitchDetector:
    """
    Класс для определения языковых переходов (code-switching) в тексте.
    Анализирует последовательность слов и фиксирует переходы между языками.
    """

    # Минимальная длина слова для анализа
    MIN_WORD_LENGTH = 3

    # Минимальная уверенность детектора
    MIN_CONFIDENCE = 70.0

    # Словари частых слов для коррекции ошибок детекции
    # (проблема: короткие слова на кириллице часто определяются как sr/bg/mk)
    RUSSIAN_WORDS = {
        "дела", "дело", "дел", "делах", "делам", "делами",
        "как", "какая", "какой", "какая", "какие",
        "что", "чего", "чему", "чем", "чём",
        "это", "этой", "этом", "этот", "эта", "эти",
        "все", "всё", "всех", "всем", "всами",
        "меня", "мне", "мной", "мною",
        "тебя", "тебе", "тобой", "тобою",
        "нас", "нам", "нами",
        "вас", "вам", "вами",
        "них", "ним", "ними",
        "был", "была", "было", "были", "быть",
        "есть", "будет", "будут",
        "здесь", "там", "тут",
        "да", "нет",
        "уже", "ещё", "еще",
        "очень", "много", "мало",
        "хорошо", "плохо",
        "можно", "нужно", "надо",
        "только", "также", "тоже",
        "потому", "поэтому",
        "когда", "где", "куда", "откуда",
    }

    # Сербские слова (для сравнения)
    SERBIAN_WORDS = {
        "шта", "како", "где", "када", "зашто",
        "овде", "тамо", "ово", "оно", "она",
        "је", "су", "бити", "сам", "си",
    }

    def __init__(self, detector: LanguageDetector):
        """
        :param detector: Экземпляр LanguageDetector для определения языка слов
        """
        self.detector = detector

    def _extract_words(self, text: str) -> List[str]:
        """
        Извлекает слова из текста, поддерживая кириллицу и латиницу.
        """
        pattern = r'[a-zA-Zа-яёӘӨҮҖҢҺәөүҗңһҕ]+(?:-[a-zA-Zа-яёӘӨҮҖҢҺәөүҗңһҕ]+)*'
        words = re.findall(pattern, text, re.IGNORECASE)
        return words

    def _correct_language(self, word: str, detected_lang: str) -> str:
        """
        Корректирует определение языка для проблемных случаев.
        Если слово определено как sr/bg/mk, но есть в русском словаре - меняем на ru.

        :param word: Слово (в нижнем регистре)
        :param detected_lang: Определенный язык
        :return: Скорректированный язык
        """
        word_lower = word.lower()

        # Проблемные славянские языки
        problematic_langs = {'sr', 'bg', 'mk', 'me', 'bs'}

        if detected_lang in problematic_langs:
            # Если слово есть в русском словаре - это русский
            if word_lower in self.RUSSIAN_WORDS:
                return 'ru'

            # Если слово есть в сербском словаре - оставляем как есть
            if word_lower in self.SERBIAN_WORDS:
                return detected_lang

            # Если слово содержит типично русские буквы (ы, э, ё) - скорее всего русский
            russian_specific_chars = set('ыэё')
            if any(char in russian_specific_chars for char in word_lower):
                return 'ru'

        return detected_lang

    def analyze_text(self, text: str) -> Dict[str, any]:
        """
        Анализирует один текст и возвращает статистику языковых переходов.
        """
        words = self._extract_words(text)

        if len(words) < 2:
            return {
                "total_switches": 0,
                "switches": {},
                "words_analyzed": 0,
                "sequence": []
            }

        # Определяем язык каждого слова с коррекцией
        word_languages = []
        for word in words:
            if len(word) < self.MIN_WORD_LENGTH:
                continue

            result = self.detector.detect_language(word)

            if not result or result['confidence'] < self.MIN_CONFIDENCE:
                continue

            detected_lang = result['code']

            # КОРРЕКЦИЯ: исправляем ошибки детекции
            corrected_lang = self._correct_language(word, detected_lang)

            word_languages.append((word, corrected_lang))

        if len(word_languages) < 2:
            return {
                "total_switches": 0,
                "switches": {},
                "words_analyzed": len(word_languages),
                "sequence": word_languages
            }

        # Считаем переходы
        switches = {}
        total_switches = 0

        for i in range(1, len(word_languages)):
            prev_word, prev_lang = word_languages[i - 1]
            curr_word, curr_lang = word_languages[i]

            if prev_lang != curr_lang:
                switch_key = f"{prev_lang}->{curr_lang}"
                switches[switch_key] = switches.get(switch_key, 0) + 1
                total_switches += 1

        return {
            "total_switches": total_switches,
            "switches": switches,
            "words_analyzed": len(word_languages),
            "sequence": word_languages
        }

    def analyze_texts(self, texts: List[str]) -> Dict[str, any]:
        """
        Анализирует список текстов и возвращает общую статистику.
        """
        total_texts = len(texts)
        texts_with_switches = 0
        total_switches = 0
        all_switches = {}

        for text in texts:
            result = self.analyze_text(text)

            if result['total_switches'] > 0:
                texts_with_switches += 1
                total_switches += result['total_switches']

                for switch_key, count in result['switches'].items():
                    all_switches[switch_key] = all_switches.get(switch_key, 0) + count

        average = total_switches / total_texts if total_texts > 0 else 0

        return {
            "total_texts": total_texts,
            "texts_with_switches": texts_with_switches,
            "total_switches": total_switches,
            "switches": all_switches,
            "average_switches_per_text": round(average, 2)
        }


# ============================================
# Пример использования
# ============================================
if __name__ == "__main__":
    from text_cleaner import TextCleaner

    print("⏳ Инициализация детектора языков...")
    detector = LanguageDetector()
    switcher = LanguageSwitchDetector(detector)

    # Тестовые данные с проблемными словами
    test_texts = [
        "Сәлам! Как дела?",
        "Привет! Хәлләр ничек?",
        "Рәхмәт большое за помощь!",
        "Бик яхшы, спасибо!",
        "Как дела? Что нового?",
        "Это очень хорошо!",
        "Привет! Туох сонун?",
        "Эҕэрдэ! Как дела?",
        "Hello! Как дела?",
        "Привет! How are you?",
        "Сәлам! Привет! Hello! Как дела? Хәлләр ничек?",
        "Привет! Как дела? Всё хорошо!",
        "Сәлам! Хәлләр ничек? Бик яхшы!",
        "Отличная новость! Рәхмәт за информацию! Бик файдалы!",
    ]

    cleaner = TextCleaner()
    cleaned_texts = cleaner.clean_texts(test_texts)

    print("\n" + "=" * 70)
    print("АНАЛИЗ ЯЗЫКОВЫХ ПЕРЕХОДОВ (С КОРРЕКЦИЕЙ)")
    print("=" * 70)

    print("\n📝 ДЕТАЛЬНЫЙ АНАЛИЗ КАЖДОГО ТЕКСТА:")
    print("-" * 70)

    for i, text in enumerate(cleaned_texts, 1):
        result = switcher.analyze_text(text)

        print(f"\n{i}. Текст: '{text}'")
        print(f"   Проанализировано слов: {result['words_analyzed']}")
        print(f"   Переходов: {result['total_switches']}")

        if result['switches']:
            print(f"   Детализация переходов:")
            for switch, count in result['switches'].items():
                print(f"      • {switch}: {count} раз(а)")

        if result['sequence']:
            print(f"   Последовательность:")
            seq_str = " → ".join([f"{word}({lang})" for word, lang in result['sequence']])
            print(f"      {seq_str}")

    print("\n" + "=" * 70)
    print("ОБЩАЯ СТАТИСТИКА")
    print("=" * 70)

    stats = switcher.analyze_texts(cleaned_texts)

    print(f"\n📊 Всего текстов: {stats['total_texts']}")
    print(f"📊 Текстов с переходами: {stats['texts_with_switches']}")
    print(f"📊 Процент текстов с переходами: {(stats['texts_with_switches'] / stats['total_texts'] * 100):.1f}%")
    print(f"📊 Всего переходов: {stats['total_switches']}")
    print(f"📊 Среднее переходов на текст: {stats['average_switches_per_text']}")

    print(f"\n🔄 Детализация всех переходов:")
    for switch, count in sorted(stats['switches'].items(), key=lambda x: x[1], reverse=True):
        print(f"   • {switch}: {count} раз(а)")

    print("\n🎉 Анализ завершен!")