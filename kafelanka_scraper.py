import csv
import json
import re

from bs4 import BeautifulSoup
import requests


ACCESSIBILITY = ['přístupné', 'po domluvě', 'nepřístupné', 'neexistuje']


def get_soup(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup


def get_details_at_map(place):
    soup = get_soup(place['map'])
    marker = soup.find(string=re.compile('var points'))
    image = re.search(r'src="(.*)" height', marker).group(1)
    if image != '/v/':
        place['image'] = 'https://www.kafelanka.cz' + image
    else:
        place['image'] = None
    m = re.search('latLng\((.*), (.*)\)', marker)
    place['latitude'] = m.group(1)
    place['longitude'] = m.group(2)
    place['accessibility'] = ACCESSIBILITY[int(re.search('stateIcons\[(\d)\]', marker).group(1)) - 1]
    return place


def get_details_at_page(place):
    soup = get_soup(place['url'])
    page_id = re.search('getMapLink\((\d[0-9]+)\)', soup.text).group(1)
    map_link = get_soup('https://www.kafelanka.cz/user/map.link.php?id=' + page_id)
    a = map_link.find('a', attrs={'class': 'showOnMap iframe'})
    if a:
        place['map'] = 'https://www.kafelanka.cz/' + a['href']
        place = get_details_at_map(place)
    return place


def places_generator(sites):
    for name in sites:
        soup = sites[name]
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
                place = get_details_at_page(place)
                yield place


def write_csv(filename, places):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['area', 'name', 'description', 'url', 'map', 'image', 'latitude', 'longitude', 'accessibility']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for place in places:
            writer.writerow(place)


def write_json(filename, places):
    with open(filename, 'w') as jsonfile:
        json.dump(places, jsonfile, ensure_ascii=False)


if __name__ == '__main__':
    sites = {'Brno': get_soup('https://www.kafelanka.cz/index.php'),
             'Lokality': get_soup('https://www.kafelanka.cz/akce/index.php')}
    
    places = []
    i = 0
    for place in places_generator(sites):
        places.append(place)
        i += 1
        print('{}: {}: {}'.format(str(i).zfill(3), place['area'], place['name']))

    write_csv('places.csv', places)
    write_json('places.json', places)
