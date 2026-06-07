import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Optional, List, Union
from language_detector import LanguageDetector


class LanguageSwitchGraph:
    """
    Класс для построения и визуализации графа языковых переходов.
    Вершины - языки, рёбра - переходы между ними.
    """

    LANGUAGE_COLORS = {
        'ru': '#FF6B6B',  # красный
        'tt': '#4ECDC4',  # бирюзовый
        'sah': '#45B7D1',  # голубой (якутский)
        'en': '#FFA07A',  # лососевый
        'de': '#98D8C8',  # мятный
        'fr': '#F7DC6F',  # желтый
        'es': '#BB8FCE',  # фиолетовый
        'uk': '#85C1E2',  # светло-голубой
        'be': '#82E0AA',  # светло-зеленый
        'kk': '#F8B739',  # оранжевый
    }

    DEFAULT_COLOR = '#95A5A6'  # серый для остальных

    def __init__(
            self,
            detector: Optional[LanguageDetector] = None,
            use_names: bool = False,
            allowed_languages: Optional[Union[str, List[str]]] = None
    ):
        """
        :param detector: LanguageDetector для получения названий языков
        :param use_names: Если True, использовать полные названия языков вместо кодов
        :param allowed_languages: Строка ("ru tt sah en") или список ["ru", "tt"].
                                  Если None, отображаются все языки.
        """
        self.detector = detector
        self.use_names = use_names

        # Нормализуем входной параметр в множество (set) для быстрого поиска
        if isinstance(allowed_languages, str):
            self.allowed_languages = set(allowed_languages.lower().split())
        elif isinstance(allowed_languages, list):
            self.allowed_languages = set(lang.lower() for lang in allowed_languages)
        else:
            self.allowed_languages = None

        self.graph = nx.DiGraph()

    def _get_label(self, lang_code: str) -> str:
        """Получает метку для языка (код или полное название)."""
        if self.use_names and self.detector:
            return self.detector.LANGUAGE_NAMES.get(lang_code, lang_code.upper())
        return lang_code.upper()

    def _get_color(self, lang_code: str) -> str:
        """Получает цвет для языка."""
        return self.LANGUAGE_COLORS.get(lang_code, self.DEFAULT_COLOR)

    def build_from_switches(self, switches: Dict[str, int]) -> None:
        """
        Строит граф из словаря переходов, фильтруя по allowed_languages.
        """
        self.graph.clear()

        for switch_key, count in switches.items():
            parts = switch_key.split('->')
            if len(parts) != 2:
                continue

            source_lang, target_lang = parts

            # ФИЛЬТРАЦИЯ: если задан список разрешенных языков, проверяем принадлежность
            if self.allowed_languages is not None:
                if source_lang not in self.allowed_languages or target_lang not in self.allowed_languages:
                    continue  # Пропускаем этот переход

            # Добавляем вершины
            if not self.graph.has_node(source_lang):
                self.graph.add_node(
                    source_lang,
                    label=self._get_label(source_lang),
                    color=self._get_color(source_lang)
                )

            if not self.graph.has_node(target_lang):
                self.graph.add_node(
                    target_lang,
                    label=self._get_label(target_lang),
                    color=self._get_color(target_lang)
                )

            # Добавляем ребро с весом
            self.graph.add_edge(source_lang, target_lang, weight=count)

    def build_from_result(self, result: Dict[str, any]) -> None:
        """Строит граф из результата analyze_texts()."""
        self.build_from_switches(result['switches'])

    def get_statistics(self) -> Dict[str, any]:
        """
        Возвращает статистику графа.
        """
        if not self.graph.nodes():
            return {
                'nodes_count': 0,
                'edges_count': 0,
                'total_transitions': 0,
                'languages': {}
            }

        # Подсчитываем входящие и исходящие переходы для каждого языка
        lang_stats = {}

        for node in self.graph.nodes():
            in_edges = [(u, v, d) for u, v, d in self.graph.in_edges(node, data=True)]
            out_edges = [(u, v, d) for u, v, d in self.graph.out_edges(node, data=True)]

            in_count = sum(d['weight'] for _, _, d in in_edges)
            out_count = sum(d['weight'] for _, _, d in out_edges)

            lang_stats[node] = {
                'label': self._get_label(node),
                'incoming': in_count,
                'outgoing': out_count,
                'total': in_count + out_count
            }

        # Общая статистика
        total_edges = sum(d['weight'] for _, _, d in self.graph.edges(data=True))

        return {
            'nodes_count': len(self.graph.nodes()),
            'edges_count': len(self.graph.edges()),
            'total_transitions': total_edges,
            'languages': lang_stats
        }

    def plot_matplotlib(
            self,
            figsize: tuple = (12, 10),
            node_size: int = 8000,
            font_size: int = 20,
            edge_label_size: int = 26,
            title: str = "Граф языковых переходов",
            save_path: Optional[str] = None
    ) -> None:
        """
        Визуализирует граф с улучшенными стрелками и подписями.
        Каждое направленное ребро имеет свою подпись.
        """
        if not self.graph.nodes():
            print("⚠️ Граф пуст! Нет переходов между указанными языками.")
            return

        fig, ax = plt.subplots(figsize=figsize)

        # Позиции вершин (круговая раскладка)
        pos = nx.circular_layout(self.graph)

        # Получаем цвета и метки вершин
        node_colors = [self.graph.nodes[node]['color'] for node in self.graph.nodes()]
        node_labels = {node: self.graph.nodes[node]['label'] for node in self.graph.nodes()}

        # Рисуем вершины
        nx.draw_networkx_nodes(
            self.graph, pos, ax=ax,
            node_color=node_colors,
            node_size=node_size,
            alpha=0.95,
            edgecolors='black',
            linewidths=2.5
        )

        # Рисуем рёбра с улучшенными стрелками
        # Разделяем двунаправленные ребра разным изгибом
        edges_drawn = set()
        for u, v, data in self.graph.edges(data=True):
            # Проверяем, есть ли обратное ребро
            has_reverse = self.graph.has_edge(v, u)

            # Определяем радиус изгиба
            if has_reverse:
                # Если есть обратное ребро, изгибаем в разные стороны
                rad = 0.25 if (u, v) not in edges_drawn else -0.25
            else:
                rad = 0.15  # Небольшой изгиб для одиночных ребер

            # Рисуем ребро с жирной стрелкой
            arrow = nx.draw_networkx_edges(
                self.graph, pos, ax=ax,
                edgelist=[(u, v)],
                edge_color='#555555',
                width=3 + (data['weight'] / max(1, max(d['weight'] for _, _, d in self.graph.edges(data=True)))) * 4,
                arrows=True,
                arrowsize=50,  # Крупные стрелки
                arrowstyle='-|>',  # Стиль стрелки
                connectionstyle=f'arc3,rad={rad}',
                alpha=1,
                min_source_margin=40,  # Отступ от вершины
                min_target_margin=40
            )

            edges_drawn.add((u, v))

        # Подписи вершин
        nx.draw_networkx_labels(
            self.graph, pos, ax=ax,
            labels=node_labels,
            font_size=font_size,
            font_weight='bold',
            font_family='Arial'
        )

        # Подписи рёбер - КАЖДОЕ РЕБРО ОТДЕЛЬНО
        edge_labels = {}
        for u, v, data in self.graph.edges(data=True):
            edge_labels[(u, v)] = str(data['weight'])

        # Рисуем подписи с учетом изгиба
        for (u, v), label in edge_labels.items():
            # Определяем позицию подписи
            has_reverse = self.graph.has_edge(v, u)
            if has_reverse:
                rad = 0.25
            else:
                rad = 0.15

            # Вычисляем позицию для подписи
            x0, y0 = pos[u]
            x1, y1 = pos[v]

            # Средняя точка с учетом изгиба
            mid_x = (x0 + x1) / 2
            mid_y = (y0 + y1) / 2

            # Смещение перпендикулярно линии
            dx = x1 - x0
            dy = y1 - y0
            length = (dx ** 2 + dy ** 2) ** 0.5
            if length > 0:
                offset_x = -dy / length * rad * 0.5
                offset_y = dx / length * rad * 0.5
                label_x = mid_x + offset_x
                label_y = mid_y + offset_y
            else:
                label_x = mid_x
                label_y = mid_y

            # Рисуем подпись с фоном
            ax.text(
                label_x, label_y, label,
                fontsize=edge_label_size,
                fontweight='bold',
                color='red',
                ha='center',
                va='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='red', alpha=0.9, linewidth=2)
            )

        ax.set_title(title, fontsize=18, fontweight='bold', pad=30)
        ax.axis('off')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ Граф сохранен в: {save_path}")

        plt.show()

    # ============================================


# Пример использования
# ============================================
if __name__ == "__main__":
    from language_detector import LanguageDetector
    from language_switch_detector import LanguageSwitchDetector
    from text_cleaner import TextCleaner

    print("⏳ Инициализация...")
    detector = LanguageDetector()
    switcher = LanguageSwitchDetector(detector)
    cleaner = TextCleaner()

    # Тестовые данные
    test_texts = [
        "Сәлам! Как дела?",
        "Привет! Хәлләр ничек?",
        "Рәхмәт большое за помощь!",
        "Бик яхшы, спасибо!",
        "Привет! Туох сонун?",
        "Эҕэрдэ! Как дела?",
        "Hello! Как дела?",
        "Привет! How are you?",
        "Сәлам! Привет! Hello! Как дела? Хәлләр ничек?",
        "Отличная новость! Рәхмәт за информацию! Бик файдалы!",
    ]

    cleaned_texts = cleaner.clean_texts(test_texts)
    result = switcher.analyze_texts(cleaned_texts)

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