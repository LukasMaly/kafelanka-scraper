import unittest

from bs4 import BeautifulSoup
import requests

import kafelanka_scraper


class TestKafelankaScraper(unittest.TestCase):
    def setUp(self):
        self.sites = {'Brno': kafelanka_scraper.get_soup('https://www.kafelanka.cz/index.php'),
                      'Lokality': kafelanka_scraper.get_soup('https://www.kafelanka.cz/akce/index.php')}

    def test_connection(self):
        response = requests.get('https://www.kafelanka.cz/index.php')
        self.assertEqual(response.status_code, 200)

    def test_get_valid_place_from_map(self):
        url = 'https://www.kafelanka.cz/user/place.map.php?id=42'
        place = kafelanka_scraper.get_place_from_map(self.sites, url)
        self.assertEqual(place['name'], 'Zídka')
        self.assertEqual(place['area'], 'Brno - Wilsonův les')
        self.assertEqual(place['description'], 'Zbytky budovy ve Wilsonově lese')
        self.assertEqual(place['link'], 'https://www.kafelanka.cz/mista/zidka.php')
        self.assertEqual(place['map'], 'https://www.kafelanka.cz/user/place.map.php?id=42')
        self.assertEqual(place['image'], 'https://www.kafelanka.cz/v/zidka-1.jpg')
        self.assertEqual(place['latitude'], '49.2045005528')
        self.assertEqual(place['longitude'], '16.5794205666')
        self.assertEqual(place['accessibility'], 'přístupné')

    def test_get_empty_place_from_map(self):
        url = 'https://www.kafelanka.cz/user/place.map.php?id=0'
        place = kafelanka_scraper.get_place_from_map(self.sites, url)
        self.assertEqual(place, None)

    def test_get_invalid_place_from_map(self):
        url = 'https://www.kafelanka.cz/user/place.map.php?id=239'
        place = kafelanka_scraper.get_place_from_map(self.sites, url)
        self.assertEqual(place, None)


if __name__ == '__main__':
    unittest.main()