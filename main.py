from language_detector import LanguageDetector
from language_switch_detector import LanguageSwitchDetector
from language_switch_graph import LanguageSwitchGraph
from text_cleaner import TextCleaner
from vk_parser import VKParser

TOKEN = "vk1.a.y2Et6CVvVi_0VRruJlaTgn8nizwjj-z7AmM8a4fYGgpHGOslZKT6mBEjMymVvb2AXqIBuORhTSLti4gxH6WeqVnQrgnsVl4-mAteGZexpE1FNIoZEIH8uvEMVxZdhGkLrbzf0c4LsLUuldAQYfzSu81a6U3xZwc0mbZkPGTEjrrT1AaJSDB6Uv1V86eK8XJpVwGRnOaYYz9p6p3FRzVxmg"

# Списки сообществ
TATARSTAN_COMMUNITIES = [
    "https://vk.com/kazan161",
    "https://vk.com/nashtatarstan",
    "https://vk.com/paznakaevo",
    "https://vk.com/vatanym",
    "https://vk.com/resptatarstan",
    "https://vk.com/hezmetdani",
    "https://vk.com/intertatgazeta",
    "https://vk.com/businessgazeta",
    "https://vk.com/shahrikazanda",
    "https://vk.com/smi_menzela",
    "https://vk.com/kizik_mizik",
]

YAKUTIA_COMMUNITIES = [
    "https://vk.com/crimlife_yakutia",
    "https://vk.com/news_yakutia",
    "https://vk.com/novosty_yakutia14",
    "https://vk.com/sakhagov",
    "https://vk.com/club228368064",
    "https://vk.com/club228369416",
    "https://vk.com/saha_yakutia",
    "https://vk.com/club201210319",
    "https://vk.com/club211747683",
    "https://vk.com/pod_ykt",
]

# Создаем парсер
parser = VKParser(token=TOKEN)

# Парсим все сообщества (по 20 постов)
print("=" * 60)
print("НАЧИНАЮ ПАРСИНГ СООБЩЕСТВ")
print("=" * 60)

all_data = parser.parse_communities(
    TATARSTAN_COMMUNITIES + YAKUTIA_COMMUNITIES,
    posts_count=20
)

# Собираем все тексты в один список
all_texts = []
for community_url, comments in all_data.items():
    all_texts.extend(comments)

print("\n" + "=" * 60)
print("РЕЗУЛЬТАТЫ ПАРСИНГА")
print("=" * 60)

for community_url, comments in all_data.items():
    print(f"\n📊 {community_url}:")
    print(f"   Собрано комментариев: {len(comments)}")
    if comments:
        print(f"   Пример первого: '{comments[0][:100]}...'")

print(f"\n🎉 Всего собрано текстов: {len(all_texts)}")


print(f"\n📝 Исходных текстов: {len(all_texts)}")
# Очищаем
cleaned = TextCleaner.clean_texts(all_texts)
print(f"\n✅ После очистки: {len(cleaned)}")


print("\n" + "=" * 70)
print("АНАЛИЗ ЯЗЫКОВЫХ ПЕРЕХОДОВ (С КОРРЕКЦИЕЙ)")
print("=" * 70)

print("\n📝 ДЕТАЛЬНЫЙ АНАЛИЗ КАЖДОГО ТЕКСТА:")
print("-" * 70)

detector = LanguageDetector()
switcher = LanguageSwitchDetector(detector)

for i, text in enumerate(cleaned, 1):
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

print("\n📊 Анализ языковых переходов...")
result = switcher.analyze_texts(cleaned)

print("\n📊 Все найденные переходы (до фильтрации):")
for switch, count in result['switches'].items():
    print(f"   • {switch}: {count}")

print("\n" + "=" * 60)
print("🎨 ПОСТРОЕНИЕ ГРАФА С ФИЛЬТРАЦИЕЙ")
print("=" * 60)

# Указываем ТОЛЬКО интересующие нас языки
TARGET_LANGUAGES = "ru tt sah en"

print(f"🔍 Отображаем только переходы между: {TARGET_LANGUAGES.upper()}")

# Создаем граф с фильтром
graph_filtered = LanguageSwitchGraph(
    detector=detector,
    use_names=True,
    allowed_languages=TARGET_LANGUAGES
)

graph_filtered.build_from_result(result)

# Теперь этот вызов сработает корректно!
stats = graph_filtered.get_statistics()
print(f"\n📈 Статистика отфильтрованного графа:")
print(f"   Вершин: {stats['nodes_count']}")
print(f"   Рёбер: {stats['edges_count']}")
print(f"   Всего переходов: {stats['total_transitions']}")

# Рисуем
graph_filtered.plot_matplotlib(
    title=f"Языковые переходы ({TARGET_LANGUAGES.upper()})",
    save_path="language_switches_filtered.png"
)

print("\n🎉 Готово! Проверьте файл language_switches_filtered.png")

# Словарь для глобального подсчета слов-триггеров по всем текстам
trigger_words_stats = {}

for i, text in enumerate(cleaned, 1):
    result = switcher.analyze_text(text)

    print(f"\n{i}. Текст: '{text}'")
    print(f"   Проанализировано слов: {result['words_analyzed']}")
    print(f"   Переходов: {result['total_switches']}")

    # --- НОВАЯ ЛОГИКА: Поиск слов-триггеров в этом тексте ---
    sequence = result['sequence']
    for j in range(len(sequence) - 1):
        current_word, current_lang = sequence[j]
        next_word, next_lang = sequence[j + 1]

        # Если язык следующего слова отличается от текущего
        if current_lang != next_lang:
            # Приводим к нижнему регистру, чтобы "Привет" и "привет" считались как одно слово
            trigger_word = current_word.lower()
            trigger_words_stats[trigger_word] = trigger_words_stats.get(trigger_word, 0) + 1
    # ---------------------------------------------------------

    if result['switches']:
        print(f"   Детализация переходов:")
        for switch, count in result['switches'].items():
            print(f"      • {switch}: {count} раз(а)")

# ==========================================
# ФИНАЛЬНЫЙ ВЫВОД ТОЛЬКО СЛОВ-ТРИГГЕРОВ
# ==========================================
print("\n" + "=" * 70)
print("🔥 СТАТИСТИКА СЛОВ-ТРИГГЕРОВ ПЕРЕХОДА ЯЗЫКА")
print("=" * 70)
print("Слова, после которых чаще всего происходит смена языка:\n")

# Сортируем словарь по количеству переходов (от большего к меньшему)
sorted_triggers = sorted(trigger_words_stats.items(), key=lambda x: x[1], reverse=True)

if not sorted_triggers:
    print("   Переходов языка не обнаружено.")
else:
    for word, count in sorted_triggers:
        # Красивое форматирование вывода
        if count > 1:
            print(f"   • '{word}': {count} раз(а)")

print("=" * 70)