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


def get_site(sites, link):
    for name in sites:
        a = sites[name].find('a', href=link)
        if a is not None:
            return name, a
    else:
        return None


def get_description(a):
    return a['title']


def get_area(name, a):
    if name == 'Brno':
        return 'Brno - ' + a.findPrevious('li', {'class': 'lokalita'}).string
    else:
        return a.findPrevious('li', {'class': 'lokalita'}).string


def get_place_from_map(sites, url):
    soup = get_soup(url)

    if soup.body.string != '\n':
        place = {}
        marker = soup.find(string=re.compile('var points'))
        place['name'] = re.search('<h2>(.*)</h2>', marker).group(1)
        link = soup.find('a', string='zpět')['href']
        site = get_site(sites, link)
        if site is None:
            return None
        name, a = site
        place['area'] = get_area(name, a)
        place['description'] = get_description(a)
        place['link'] = 'https://www.kafelanka.cz' + link
        place['map'] = url
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
    else:
        return None


def write_csv(filename, places):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['name', 'area', 'description', 'link', 'map', 'image', 'latitude', 'longitude', 'accessibility']
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
    for i in range(570):
        url = 'https://www.kafelanka.cz/user/place.map.php?id=' + str(i)
        place = get_place_from_map(sites, url)
        if place is not None:
            places.append(place)
            print('{}: {}: {}'.format(str(i).zfill(3), place['area'], place['name']))
        else:
            print('{}:'.format(str(i).zfill(3)))

    write_csv('places.csv', places)
    write_json('places.json', places)
