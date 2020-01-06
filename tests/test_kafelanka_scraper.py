import unittest

from requests_html import HTMLSession

from kafelankascraper import KafelankaScraper


class TestKafelankaScraper(unittest.TestCase):
    def test_connection(self):
        session = HTMLSession()
        r = session.get('https://www.kafelanka.cz/index.php')
        self.assertEqual(r.status_code, 200)

    def test_get_place_from_map(self):
        kafelanka_scraper = KafelankaScraper()
        place = next(kafelanka_scraper.places_generator())
        self.assertEqual(place['area'], 'Brno - Kraví hora')
        self.assertEqual(place['name'], 'Bufet')
        self.assertEqual(place['description'], 'Ruiny bývalého bufetu Pod Topoly na Kraví hoře')
        self.assertEqual(place['url'], 'https://www.kafelanka.cz/mista/topoly.php')
        self.assertEqual(place['map'], 'https://www.kafelanka.cz/user/place.map.php?id=11')
        self.assertEqual(place['image'], 'https://www.kafelanka.cz/v/topoly-1.jpg')
        self.assertEqual(place['latitude'], 49.2040904775)
        self.assertEqual(place['longitude'], 16.58842206)
        self.assertEqual(place['accessibility'], 'neexistuje')


if __name__ == '__main__':
    unittest.main()