import csv
import re

from bs4 import BeautifulSoup
import requests


ACCESSIBILITY = ['přístupné', 'po domluvě', 'nepřístupné', 'neexistuje']

def get_place_from_map(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    if soup.body.string != '\n':
        place = {}
        marker = soup.find(string=re.compile('var points'))
        place['name'] = re.search('<h2>(.*)</h2>', marker).group(1)
        place['link'] = 'http://www.kafelanka.cz' + soup.find('a', string='zpět')['href']
        place['map'] = url
        place['image'] = 'http://www.kafelanka.cz' + re.search(r'src="(.*)" height', marker).group(1)
        m = re.search('latLng\((.*), (.*)\)', marker)
        place['latitude'] = m.group(1)
        place['longitude'] = m.group(2)
        place['accessibility'] = ACCESSIBILITY[int(re.search('stateIcons\[(\d)\]', marker).group(1)) - 1]
        return place
    else:
        return None


def write_csv(filename, places):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['name', 'link', 'map', 'image', 'latitude', 'longitude', 'accessibility']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for place in places:
            writer.writerow(place)


if __name__ == '__main__':
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
