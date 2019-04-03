import csv
import json
import re

from bs4 import BeautifulSoup
import requests


class KafelankaScraper():
    accessibilities = ['přístupné', 'po domluvě', 'nepřístupné', 'neexistuje']

    def __init__(self):
        self.sites = {'Brno': self.__get_soup('https://www.kafelanka.cz/index.php'),
                      'Lokality': self.__get_soup('https://www.kafelanka.cz/akce/index.php')}
        self.map_2013 = self.__load_map_2013()

    @staticmethod
    def __get_soup(url):
        response = requests.get(url)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup

    def __get_details_at_map(self, place):
        soup = self.__get_soup(place['map'])
        marker = soup.find(string=re.compile('var points'))
        image = re.search(r'src="(.*)" height', marker).group(1)
        if image != '/v/':
            place['image'] = 'https://www.kafelanka.cz' + image
        else:
            place['image'] = None
        m = re.search('latLng\((.*), (.*)\)', marker)
        place['latitude'] = m.group(1)
        place['longitude'] = m.group(2)
        place['accessibility'] = self.accessibilities[int(re.search('stateIcons\[(\d)\]', marker).group(1)) - 1]
        return place

    def __get_details_at_page(self, place):
        soup = self.__get_soup(place['url'])
        page_id = re.search('getMapLink\((\d[0-9]+)\)', soup.text).group(1)
        map_link = self.__get_soup('https://www.kafelanka.cz/user/map.link.php?id=' + page_id)
        a = map_link.find('a', attrs={'class': 'showOnMap iframe'})
        if a:
            place['map'] = 'https://www.kafelanka.cz/' + a['href']
            place = self.__get_details_at_map(place)
        else:
            place = self.__get_details_at_map_2013(place)
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
                    place = self.__get_details_at_page(place)
                    yield place

    def __load_map_2013(self, filename='map_2013.csv'):
        places = []
        with open(filename) as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                place = {'name': row[0], 'url': row[1], 'image': row[2],
                         'latitude': row[3], 'longitude': row[4], 'accessibility': row[5]}
                places.append(place)
        return places

    def __get_details_at_map_2013(self, place):
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
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
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
    for place in kafelanka_scraper.places_generator():
        places.append(place)
        i += 1
        print('{}: {}: {}'.format(str(i).zfill(3), place['area'], place['name']))
        if i > 10:
            break

    kafelanka_scraper.write_csv('places.csv', places)
    kafelanka_scraper.write_json('places.json', places)
