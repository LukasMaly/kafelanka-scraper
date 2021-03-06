import csv
import json
import os
import re

from bs4 import BeautifulSoup
import geojson
import requests
import simplekml


class KafelankaScraper():
    accessibilities = ['přístupné', 'po domluvě', 'nepřístupné', 'neexistuje']

    def __init__(self):
        self.sites = {'Brno': self._get_soup('https://www.kafelanka.cz/index.php'),
                      'Lokality': self._get_soup('https://www.kafelanka.cz/akce/index.php')}
        self.map_2013 = self._load_map_2013()

    @staticmethod
    def _get_soup(url):
        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
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
        soup = self._get_soup(place['url'])
        place['id'] = int(soup.find('body').attrs['data-id'])
        if len(requests.get('https://www.kafelanka.cz/user/map.link.php?id=' + str(place['id'])).content) > 0:
            place['map'] = 'https://www.kafelanka.cz/user/place.map.php?id=' + str(place['id'])
            place = self._get_details_at_map(place)
        else:
            place = self._get_details_at_map_2013(place)
        return place

    def places_generator(self, skip=0):
        counter = 0
        for name in self.sites:
            soup = self.sites[name]
            for ul in soup.find_all('ul', attrs={'class': 'mista'}):
                for a in ul.find_all('a'):
                    counter += 1
                    if counter <= skip:
                        continue
                    place = {'id': None, 'area': None, 'name': None, 'description': None, 'url': None,
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

    @staticmethod
    def write_kml(filename, places):
        kml = simplekml.Kml()
        for place in places:
            if place['latitude'] is not None:
                multipnt = kml.newmultigeometry(
                    name=place['name'],
                    description=place['description'])
                if 'markers' in place:
                    for marker in place['markers']:
                        multipnt.newpoint(
                            name=marker['title'],
                            coords=[(marker['longitude'], marker['latitude'])]
                        )
                else:
                    multipnt.newpoint(
                        coords=[(place['longitude'], place['latitude'])]
                    )
                if 'features' in place:
                    for feature in place['features']:
                        if feature['geometry']['type'] == 'LineString':
                            multipnt.newlinestring(
                                coords=[(lon, lat) for lon, lat in feature['geometry']['coordinates']]
                            )
                        elif feature['geometry']['type'] == 'Polygon':
                            multipnt.newpolygon(
                                outerboundaryis=[(lon, lat) for lon, lat in feature['geometry']['coordinates'][0]]
                    )
        kml.save(filename)


if __name__ == '__main__':
    kafelanka_scraper = KafelankaScraper()
    places = []
    if os.path.isfile('./places.json'):
        with open('./places.json') as fp:
            places = json.load(fp)
    i = len(places)
    counter = kafelanka_scraper.places_couter()
    try:
        for place in kafelanka_scraper.places_generator(skip=i):
            places.append(place)
            i += 1
            print('{}/{}: {}: {}'.format(str(i).zfill(3), str(counter).zfill(3), place['area'], place['name']))
    finally:
        kafelanka_scraper.write_csv('places.csv', places)
        kafelanka_scraper.write_json('places.json', places)
        kafelanka_scraper.write_kml('places.kml', places)
