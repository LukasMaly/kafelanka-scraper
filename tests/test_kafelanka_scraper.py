import unittest

import requests

from kafelankascraper import KafelankaScraper


class TestKafelankaScraper(unittest.TestCase):
    def setUp(self):
        self.kafelanka_scraper = KafelankaScraper()

    def test_connection(self):
        response = requests.get('https://www.kafelanka.cz/index.php')
        self.assertEqual(response.status_code, 200)

    def test_get_place_from_map(self):
        place = next(self.kafelanka_scraper.places_generator())
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