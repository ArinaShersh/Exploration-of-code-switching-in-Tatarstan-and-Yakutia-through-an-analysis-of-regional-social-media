import requests
import time
from typing import List, Dict
from urllib.parse import urlparse


class VKParser:
    """
    Парсер ВКонтакте для сбора комментариев из сообществ.
    Использует user token для доступа к API.
    """

    API_VERSION = '5.199'
    BASE_URL = 'https://api.vk.com/method/'

    def __init__(self, token: str):
        """
        :param token: Пользовательский токен VK
        """
        self.token = token
        self.session = requests.Session()

    def _call_api(self, method: str, params: dict) -> dict:
        """Вызов метода VK API с обработкой ошибок."""
        params['access_token'] = self.token
        params['v'] = self.API_VERSION

        response = self.session.get(self.BASE_URL + method, params=params)
        data = response.json()

        if 'error' in data:
            error = data['error']
            raise Exception(f"VK API Error {error['error_code']}: {error['error_msg']}")

        return data.get('response', {})

    def _resolve_group_id(self, url_or_screen_name: str) -> int:
        """Преобразует URL или screen_name в numeric group_id."""
        # Извлекаем screen_name из URL
        if url_or_screen_name.startswith('http'):
            parsed = urlparse(url_or_screen_name)
            screen_name = parsed.path.strip('/')
        else:
            screen_name = url_or_screen_name

        # Используем utils.resolveScreenName для получения ID
        response = self._call_api('utils.resolveScreenName', {
            'screen_name': screen_name
        })

        if not response or response.get('type') != 'group':
            raise ValueError(f"Не удалось найти сообщество: {screen_name}")

        return response['object_id']

    def get_last_posts(self, group_id: int, count: int = 20) -> List[Dict]:
        """Получает последние N постов со стены сообщества."""
        response = self._call_api('wall.get', {
            'owner_id': -group_id,  # Для сообществ owner_id отрицательный
            'count': count
        })
        return response.get('items', [])

    def get_all_comments(self, owner_id: int, post_id: int) -> List[str]:
        """
        Получает все комментарии к посту (включая ответы).
        Использует пагинацию через offset.
        """
        comments = []
        offset = 0
        count = 100  # Максимум за один запрос

        while True:
            response = self._call_api('wall.getComments', {
                'owner_id': owner_id,
                'post_id': post_id,
                'offset': offset,
                'count': count,
                'preview_length': 0,
                'thread_items_count': 3  # Получаем до 3 ответов на каждый комментарий
            })

            items = response.get('items', [])
            if not items:
                break

            # Собираем корневые комментарии
            for item in items:
                text = item.get('text', '').strip()
                if text:
                    comments.append(text)

                # Собираем ответы (replies) из thread
                thread = item.get('thread', {})
                for reply in thread.get('items', []):
                    reply_text = reply.get('text', '').strip()
                    if reply_text:
                        comments.append(reply_text)

            # Проверяем, есть ли еще комментарии
            total = response.get('count', 0)
            offset += count
            if offset >= total:
                break

            # Задержка, чтобы не превысить лимиты API (3 запроса/сек)
            time.sleep(0.35)

        return comments

    def parse_communities(
            self,
            community_urls: List[str],
            posts_count: int = 20
    ) -> Dict[str, List[str]]:
        """
        Основной метод: парсит все сообщества и собирает комментарии.

        :param community_urls: Список URL сообществ
        :param posts_count: Количество последних постов для обработки
        :return: Словарь {url: [список текстов комментариев]}
        """
        result = {}

        for url in community_urls:
            try:
                print(f"\n🔍 Обрабатываю: {url}")

                # 1. Получаем ID сообщества
                group_id = self._resolve_group_id(url)
                print(f"   ✅ Group ID: {group_id}")

                # 2. Получаем последние посты
                posts = self.get_last_posts(group_id, count=posts_count)
                print(f"   📝 Получено постов: {len(posts)}")

                # 3. Собираем комментарии ко всем постам
                all_comments = []
                for i, post in enumerate(posts):
                    post_id = post['id']
                    comments_count = post.get('comments', {}).get('count', 0)

                    if comments_count > 0:
                        comments = self.get_all_comments(-group_id, post_id)
                        all_comments.extend(comments)
                        print(f"   💬 Пост {i + 1}/{len(posts)}: {len(comments)} комментариев")
                    else:
                        print(f"   💬 Пост {i + 1}/{len(posts)}: нет комментариев")

                    # Задержка между постами
                    time.sleep(0.35)

                result[url] = all_comments
                print(f"   🎉 Итого комментариев: {len(all_comments)}")

            except Exception as e:
                print(f"   ❌ Ошибка при обработке {url}: {e}")
                result[url] = []

        return result


# ============================================
# Пример использования
# ============================================
if __name__ == "__main__":
    # ВАЖНО: Токен можно получить на сайте https://vkhost.github.io/
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

    pass

    # Теперь можно передать all_texts в ваш LanguageDetector
    # from language_detector import LanguageDetector
    # detector = LanguageDetector()
    # for text in all_texts[:10]:  # Проверяем первые 10
    #     lang = detector.detect_language(text)
    #     print(f"{lang['name']}: {text[:50]}...")