import csv
import json
import re

from bs4 import BeautifulSoup
import geojson
from requests_html import HTMLSession


class KafelankaScraper():
    accessibilities = ['přístupné', 'po domluvě', 'nepřístupné', 'neexistuje']

    def __init__(self):
        self.sites = {'Brno': self._get_soup('https://www.kafelanka.cz/index.php'),
                      'Lokality': self._get_soup('https://www.kafelanka.cz/akce/index.php')}
        self.map_2013 = self._load_map_2013()

    @staticmethod
    def _get_soup(url, render=False):
        session = HTMLSession()
        r = session.get(url)
        r.encoding = 'utf-8'
        if render:
            r.html.render()
        soup = BeautifulSoup(r.html.html, 'html.parser')
        return soup

    def _get_details_at_map(self, place):
        soup = self._get_soup(place['map'])
        script = soup.find(string=re.compile('var points'))
        pattern = r"""L.marker\(pos,\{title : "(.*)", icon : stateIcons\[(\d)\]\}\).addTo\(map\).bindPopup\('<h2>.*</h2><img src="(.*)" height="100" /><p>GPS: (.*), (.*)</p>'\);"""
        matches = re.findall(pattern, script)
        markers = []
        for match in matches:
            marker = {'title': match[0],
                      'image': 'https://www.kafelanka.cz' + match[2],
                      'latitude': float(match[3]),
                      'longitude': float(match[4]),
                      'accessibility': self.accessibilities[int(match[1]) - 1]}
            markers.append(marker)
        place['image'] = markers[0]['image']
        place['latitude'] = markers[0]['latitude']
        place['longitude'] = markers[0]['longitude']
        place['accessibility'] = markers[0]['accessibility']
        place['markers'] = markers
        pattern = r'L.geoJSON\(([\s\S]*)\).addTo\(map\);'
        match = re.search(pattern, script)
        if match:
            feature_collection = geojson.loads(match.group(1))
            place['features'] = feature_collection['features']
        return place

    def _get_details_at_page(self, place):
        soup = self._get_soup(place['url'], render=True)
        map_link = soup.find('div', attrs={'id': 'mapLink'})
        if len(map_link.contents) > 0:
            a = map_link.find('a', attrs={'class': 'showOnMap iframe'})
            place['map'] = 'https://www.kafelanka.cz' + a['href']
            place = self._get_details_at_map(place)
        else:
            place = self._get_details_at_map_2013(place)
        return place

    def places_generator(self):
        for name in self.sites:
            soup = self.sites[name]
            for ul in soup.find_all('ul', attrs={'class': 'mista'}):
                for a in ul.find_all('a'):
                    place = {'area': None, 'name': None, 'description': None, 'url': None,
                             'map': None, 'image': None, 'latitude': None, 'longitude': None,
                             'accessibility': None}
                    place['area'] = a.findPrevious('li', {'class': 'lokalita'}).string
                    if name == 'Brno':
                        place['area'] = 'Brno - ' + place['area']
                    place['name'] = a.string
                    place['description'] = a['title']
                    place['url'] = 'https://www.kafelanka.cz' + a['href']
                    place = self._get_details_at_page(place)
                    yield place

    def places_couter(self):
        counter = 0
        for name in self.sites:
            soup = self.sites[name]
            for ul in soup.find_all('ul', attrs={'class': 'mista'}):
                counter += len(ul.find_all('a'))
        return counter

    def _load_map_2013(self, filename='map_2013.csv'):
        places = []
        with open(filename) as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                place = {'name': row[0], 'url': row[1], 'image': row[2],
                         'latitude': float(row[3]), 'longitude': float(row[4]), 
                         'accessibility': row[5]}
                places.append(place)
        return places

    def _get_details_at_map_2013(self, place):
        for map_2013_place in self.map_2013:
            if place['url'] == map_2013_place['url']:
                place['image'] = map_2013_place['image']
                place['latitude'] = map_2013_place['latitude']
                place['longitude'] = map_2013_place['longitude']
                place['accessibility'] = map_2013_place['accessibility']
                return place
        return place

    @staticmethod
    def write_csv(filename, places):
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['area', 'name', 'description', 'url', 'map',
                          'image', 'latitude', 'longitude', 'accessibility']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for place in places:
                writer.writerow(place)

    @staticmethod
    def write_json(filename, places):
        with open(filename, 'w') as jsonfile:
            json.dump(places, jsonfile, ensure_ascii=False)


if __name__ == '__main__':
    kafelanka_scraper = KafelankaScraper()

    places = []
    i = 0
    counter = kafelanka_scraper.places_couter()
    for place in kafelanka_scraper.places_generator():
        places.append(place)
        i += 1
        print('{}/{}: {}: {}'.format(str(i).zfill(3), str(counter).zfill(3), place['area'], place['name']))
    kafelanka_scraper.write_csv('places.csv', places)
    kafelanka_scraper.write_json('places.json', places)
