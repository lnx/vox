#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import requests

from flask import Flask
from flask import jsonify
from flask import request
from flask import redirect
from flask import render_template

from bs4 import BeautifulSoup


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

BRAND = 'CodingHonor'
DOMAIN = 'localhost:5000'
HOST = '0.0.0.0'
PORT = 5000

OFFSET = 0
LIMIT = 100

HEADERS = {'Referer': 'http://music.163.com'}


@app.route('/')
def root():
	return redirect('/v1')


@app.route('/v1')
def index():
	return render_template('api_v1.html', version='v1', domain=DOMAIN, brand=BRAND, offset=OFFSET, limit=LIMIT)


@app.route('/v1/albums/<albumId>')
def album(albumId=''):
	url = 'http://music.163.com/album?id=%s' % albumId
	soup = BeautifulSoup(requests.get(url, headers=HEADERS).text)
	data = {}
	data['id'] = albumId
	data['name'] = getText(soup.find('h2', class_='f-ff2'))
	data['artist'] = {}
	data['artist']['name'] = getText(soup.find('a', class_='s-fc7'))
	data['artist']['id'] = last('id=', soup.find('a', class_='s-fc7')['href'])
	intrNodes = soup.find_all('p', class_='intr')
	if len(intrNodes) >= 3:
		data['publishTime'] = last('：[ \n]*', getText(intrNodes[1]))
		data['company'] = last('：[ \n]*', getText(intrNodes[2]))
	data['songs'] = []
	for songNode in soup.find_all('tr', class_='ztag'):
		songDict = {}
		songDict['id'] = songNode['data-id']
		songDict['name'] = songNode.a['title']
		songDict['time'] = getText(songNode.find('td', 's-fc3'))
		data['songs'].append(songDict)
	return jsonify(**data)


@app.route('/v1/albums')
def albums():
	s, = parse_request('s')
	offset, limit = parse_offset_limit();
	url = 'http://music.163.com/api/search/get/web?csrf_token='
	payload = {'s': s, 'type': '10', 'offset': offset, 'total': 'true', 'limit': limit}
	r = requests.post(url, data=payload, headers=HEADERS)
	return jsonify(**r.json())


@app.route('/v1/artists/<artistId>')
def artist(artistId=''):
	url = 'http://music.163.com/artist?id=%s' % artistId
	soup = BeautifulSoup(requests.get(url, headers=HEADERS).text)
	data = {}
	data['id'] = artistId
	data['name'] = getText(soup.find('h2', id='artist-name'))
	data['songs'] = []
	for songNode in soup.find_all('tr', class_='ztag'):
		songDict = {}
		idNameNode = songNode.find('div', class_='ttc').a
		songDict['id'] = last('id=', idNameNode['href'] if idNameNode is not None else '')
		songDict['name'] = getText(idNameNode)
		songDict['time'] = getText(songNode.find('td', 's-fc3'))
		albumNode = songNode.find('td', class_='w4').a
		songDict['album'] = {}
		songDict['album']['id'] = last('id=', albumNode['href'] if albumNode is not None else '')
		songDict['album']['name'] = getText(albumNode)
		data['songs'].append(songDict)
	return jsonify(**data)


@app.route('/v1/artists')
def artists():
	s, = parse_request('s')
	offset, limit = parse_offset_limit();
	url = 'http://music.163.com/api/search/get/web?csrf_token='
	payload = {'s': s, 'type': '100', 'offset': offset, 'total': 'true', 'limit': limit}
	r = requests.post(url, data=payload, headers=HEADERS)
	return jsonify(**r.json())


@app.route('/v1/new/albums/<area>')
def newAlbums(area='ALL'):
	offset, limit = parse_offset_limit();
	url = 'http://music.163.com/api/album/new?area=%s&offset=%d&total=true&limit=%d&csrf_token=' % (area, offset, limit)
	r = requests.get(url, headers=HEADERS)
	return jsonify(**r.json())


@app.route('/v1/playlists/<playlistId>')
def playlist(playlistId=''):
	url = 'http://music.163.com/playlist?id=%s' % playlistId
	soup = BeautifulSoup(requests.get(url, headers=HEADERS).text)
	data = {}
	data['id'] = playlistId
	data['name'] = getText(soup.find('h2', class_='f-ff2'))
	data['songs'] = []
	for songNode in soup.find_all('tr', class_='ztag'):
		songDict = {}
		tds = songNode.find_all('td')
		if len(tds) >= 5:
			idNameNode = tds[1].find('div', class_='ttc').a
			songDict['id'] = last('id=', idNameNode['href'] if idNameNode is not None else '')
			songDict['name'] = getText(idNameNode)
			songDict['time'] = getText(tds[2])
			artistNode = tds[3].a
			songDict['artist'] = {}
			songDict['artist']['id'] = last('id=', artistNode['href'] if artistNode is not None else '')
			songDict['artist']['name'] = getText(tds[3])
			albumaNode = tds[4].a
			songDict['album'] = {}
			songDict['album']['id'] = last('id=', albumaNode['href'] if albumaNode is not None else '')
			songDict['album']['name'] = getText(albumaNode)
			data['songs'].append(songDict)
	return jsonify(**data)


@app.route('/v1/playlists')
def playlists():
	s, = parse_request('s')
	offset, limit = parse_offset_limit();
	url = 'http://music.163.com/api/search/get/web?csrf_token='
	payload = {'s': s, 'type': '1000', 'offset': offset, 'total': 'true', 'limit': limit}
	r = requests.post(url, data=payload, headers=HEADERS)
	return jsonify(**r.json())


def parse_request(*params):
	ret = []
	for p in params:
		v = request.args.get(p)
		ret.append(v if v is not None else '')
	return ret


def parse_offset_limit(*params):
	ret = parse_request('offset', 'limit')
	try:
		ret[0] = int(ret[0])
	except ValueError:
		ret[0] = OFFSET
	try:
		ret[1] = int(ret[1])
	except ValueError:
		ret[1] = LIMIT
	return ret


def getText(node):
	return node.get_text() if node is not None else ''


def last(sp, s):
	return re.split(sp, s if s is not None else '')[-1].strip()


if __name__ == '__main__':
	app.run(host=HOST, port=PORT, debug=True)
