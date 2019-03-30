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


def get_description(link):
    a = SOUPS['Brno'].find('a', href=link)
    if a is not None:
        return a['title']
    else:
        a = SOUPS['Lokality'].find('a', href=link)
        if a is not None:
            return a['title']
        else:
            a = SOUPS['Clanky'].find('a', href=link)
            if a is not None:
                return a['title']
    return None


def get_place_from_map(url):
    soup = get_soup(url)

    if soup.body.string != '\n':
        place = {}
        marker = soup.find(string=re.compile('var points'))
        place['name'] = re.search('<h2>(.*)</h2>', marker).group(1)
        link = soup.find('a', string='zpět')['href']
        place['description'] = get_description(link)
        place['link'] = 'http://www.kafelanka.cz' + link
        place['map'] = url
        image = re.search(r'src="(.*)" height', marker).group(1)
        if image != '/v/':
            place['image'] = 'http://www.kafelanka.cz' + image
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
        fieldnames = ['name', 'description', 'link', 'map', 'image', 'latitude', 'longitude', 'accessibility']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for place in places:
            writer.writerow(place)


def write_json(filename, places):
    with open(filename, 'w') as jsonfile:
        json.dump(places, jsonfile, ensure_ascii=False)


if __name__ == '__main__':
    SOUPS = {'Brno': get_soup('https://www.kafelanka.cz/index.php'),
            'Lokality': get_soup('https://www.kafelanka.cz/akce/index.php'),
            'Clanky': get_soup('https://www.kafelanka.cz/projects/index.php')}

    places = []
    for i in range(570):
        url = 'https://www.kafelanka.cz/user/place.map.php?id=' + str(i)
        place = get_place_from_map(url)
        if place is not None:
            places.append(place)
            print('{}: {}'.format(str(i).zfill(3), place['name']))
        else:
            print('{}:'.format(str(i).zfill(3)))

    write_csv('places.csv', places)
    write_json('places.json', places)
