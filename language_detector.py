import fasttext
import urllib.request
import os
from typing import List, Dict, Optional


class LanguageDetector:
    """
    Класс для определения языка текста с использованием FastText модели lid.176.
    Поддерживает 176 языков, включая русский, татарский, якутский и английский.
    """

    # Словарь популярных кодов языков (ISO 639) -> названия
    LANGUAGE_NAMES = {
        "ru": "Русский",
        "tt": "Татарский",
        "sah": "Якутский (Саха)",
        "en": "Английский",
        "de": "Немецкий",
        "fr": "Французский",
        "es": "Испанский",
        "it": "Итальянский",
        "pt": "Португальский",
        "zh": "Китайский",
        "ja": "Японский",
        "ko": "Корейский",
        "ar": "Арабский",
        "tr": "Турецкий",
        "uk": "Украинский",
        "be": "Белорусский",
        "kk": "Казахский",
        "uz": "Узбекский",
        "ky": "Киргизский",
        "ba": "Башкирский",
        "cv": "Чувашский",
    }

    MODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"

    def __init__(self, model_path: str = "lid.176.bin", auto_download: bool = True):
        """
        Инициализация детектора. При первом запуске автоматически скачивает модель.

        :param model_path: Путь к файлу модели lid.176.bin
        :param auto_download: Если True, модель будет скачана при отсутствии
        """
        self.model_path = model_path

        if not os.path.exists(model_path):
            if not auto_download:
                raise FileNotFoundError(
                    f"Модель не найдена по пути: {model_path}. "
                    "Скачайте её вручную или установите auto_download=True."
                )
            self._download_model()

        print(f"⏳ Загрузка модели '{model_path}' в память...")
        # ВАЖНО: fasttext выводит много служебной информации в stdout при загрузке.
        # Подавляем её через перенаправление, если нужно.
        self.model = fasttext.load_model(model_path)
        print("✅ Модель готова к работе!\n")

    def _download_model(self) -> None:
        """Скачивает модель lid.176.bin с серверов Meta."""
        print(f"⏳ Модель не найдена. Скачиваю {self.model_path} (~126 МБ)...")
        urllib.request.urlretrieve(self.MODEL_URL, self.model_path)
        print("✅ Модель успешно скачана!\n")

    def detect(self, text: str, top_k: int = 3) -> List[Dict[str, any]]:
        """
        Определяет язык текста и возвращает топ-K наиболее вероятных вариантов.

        :param text: Текст для анализа
        :param top_k: Количество вариантов для возврата (по умолчанию 3)
        :return: Список словарей вида:
                 [{"code": "ru", "name": "Русский", "confidence": 99.85}, ...]
        """
        if not text or not text.strip():
            return []

        # Подготовка текста: модель обучалась на lowercase, не любит переносы строк
        clean_text = text.lower().replace("\n", " ").replace("\r", " ")

        # Предсказание
        labels, probabilities = self.model.predict(clean_text, k=top_k)

        # Формирование красивого результата
        results = []
        for label, prob in zip(labels, probabilities):
            code = label.replace("__label__", "")
            results.append({
                "code": code,
                "name": self.LANGUAGE_NAMES.get(code, code.upper()),
                "confidence": round(prob * 100, 2),
            })

        return results

    def detect_language(self, text: str) -> Optional[Dict[str, any]]:
        """
        Упрощенный метод — возвращает только самый вероятный язык.

        :param text: Текст для анализа
        :return: Словарь с информацией о языке или None, если текст пустой
        """
        results = self.detect(text, top_k=1)
        return results[0] if results else None


# ============================================
# Пример использования
# ============================================
if __name__ == "__main__":
    # 1. Создаем детектор (модель скачается автоматически при первом запуске)
    detector = LanguageDetector()

    # 2. Тестовые данные
    test_texts = [
        ("Русский", "Привет! Как дела? Это тест на определение языка с помощью нейросети."),
        ("Татарский", "Сәлам! Хәлләр ничек? Бу телне ачыклау өчен махсус тест."),
        ("Якутский (Саха)", "Эҕэрдэ! Туох сонун? Бу тылы быһаарарга аналлаах тургутуу."),
        ("Английский", "Hello! How are you? This is a language detection test using fasttext."),
        ("Немецкий", "Hallo! Wie geht es dir? Dies ist ein Test zur Spracherkennung."),
    ]

    # 3. Проверка
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ДЕТЕКТОРА ЯЗЫКОВ")
    print("=" * 60)

    for expected_lang, text in test_texts:
        # Используем упрощенный метод detect_language
        result = detector.detect_language(text)

        print(f"\n📝 Ожидался: {expected_lang}")
        print(f"💬 Текст: '{text}'")
        print(
            f"🎯 Распознано: {result['name']} ({result['code'].upper()}) "
            f"— уверенность {result['confidence']:.2f}%"
        )
        print("-" * 60)

    # 4. Бонус: посмотрим топ-3 варианта для смешанного/непонятного текста
    print("\n🔍 Топ-3 гипотезы для короткого текста 'Сәлам':")
    top3 = detector.detect("Сәлам", top_k=3)
    for i, r in enumerate(top3, 1):
        print(f"   {i}. {r['name']} ({r['code']}) — {r['confidence']:.2f}%")

    print("\n🎉 Тест завершен!")