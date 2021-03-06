# coding: utf-8
# Author: dandy

#<setting id="value1" type="text" label="Value 1" default="19f15a0031b8548acfa8da1f2cdf7f73179aa13f3c4938c8bad5a1c93dd8fe06" />
#<setting id="value2" type="text" label="Value 2" default="79e4add175162a762071a11fe45d249f" />
#<setting id="vurl" type="text" label="Values URL" default="http://wonky.lostcut.net/moonwalk_key.php" />
#<setting id="vurl2" type="text" label="Values URL 2" default="http://www.u2csp01.ml/hdrez/hdr_key.php" />

import urllib, urllib2
import xbmc
import xbmcaddon
import xbmcgui
import XbmcHelpers
import socket
common = XbmcHelpers

import re
import json
import base64
import binascii
import pyaes

import tools

USER_AGENT = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0"

socket.setdefaulttimeout(120)

id = 'script.module.videohosts'
addon = xbmcaddon.Addon(id)
vurl =  addon.getSetting('vurl')

class EncryptedData:
    def __init__(self):
        pass

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, separators=(',', ':'))

def reload_values(content, url):
    i = 3
    e_value = None
    n_value = None
    while (i > 0): 
        response = common.fetchPage({"link": vurl})
        if response["status"] == 200:
          data = response["content"]
          if data and "value1" in data:
              e_value = data.split("value2=")[0].replace("value1=", "").strip()
              n_value = data.split("value2=")[1]
              break  
        i-=1
    if e_value and n_value:
      xbmc.log("v1=" + repr(e_value) + " v2=" + repr(n_value)) 	
      addon.setSetting('value1', e_value)
      addon.setSetting('value2', n_value)
    return get_access_attrs(content, url, False)

#http://wonky.lostcut.net/moonwalk_key.php
def reload_values2(content, url):
    i = 3
    e_value = None
    n_value = None
    while (i > 0): 
        response = common.fetchPage({"link": vurl})
        if response["status"] == 200:
          data = response["content"]
          if data and "key" in data:
              json_data = json.loads(data)
              e_value = json_data["key"]
              n_value = json_data["iv"]
              break  
        i-=1
    if e_value and n_value:
      xbmc.log("v1=" + repr(e_value) + " v2=" + repr(n_value))    
      addon.setSetting('value1', e_value)
      addon.setSetting('value2', n_value)
    return get_access_attrs(content, url, False)

def get_cookies(content):
    cookie = re.compile(r"window\[\'(\w*)\'\]\s=\s\'(\w*)\';").findall(content)[0]
    cookie_header = cookie[0]
    cookie_header = re.sub('\'|\s|\+', '', cookie_header)
    cookie_data = cookie[1]
    cookie_data = re.sub('\'|\s|\+', '', cookie_data)
    cookies = [cookie_header, cookie_data]
    return cookies

def get_access_attrs(content, url, check=True):
    values = {}
    attrs = {}

    mw_pid = re.compile(r"partner_id:\s*(\w*),").findall(content)[0]
    p_domain_id = re.compile(r"domain_id:\s*(\w*),").findall(content)[0]

    _mw_adb = False

    video_token = re.compile(r"video_token:\s*\S?\'([0-9a-f]*)\S?\'").findall(content)[0]
    ref = re.compile('ref: \'(.+?)\'').findall(content)[0]

    js_path = re.compile(r'script src=\"(.*)\"').findall(content)[0]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
    }
    if "://" in js_path:
        request = urllib2.Request(js_path, "", headers)
    else:
        request = urllib2.Request("http://" + url.split('/')[2] + js_path, "", headers)
    request.get_method = lambda: 'GET'
    js_page = urllib2.urlopen(request).read()

    t = EncryptedData()
    t.a = mw_pid
    t.b = p_domain_id
    t.c = _mw_adb
    #t.d = window_value
    t.e = video_token
    t.f = USER_AGENT

    json_string = t.to_json()

    e_value = addon.getSetting('value1')
    n_value = addon.getSetting('value2')
    encrypted = ''

    try:
        encrypt_mode = pyaes.AESModeOfOperationCBC(binascii.a2b_hex(e_value), binascii.a2b_hex(n_value))
        encrypter = pyaes.Encrypter(encrypt_mode)
        encrypted += encrypter.feed(json_string)
        encrypted += encrypter.feed()
    except:
        pass

    host = re.compile(r"host: \'(.+?)\'").findall(content)[0]
    attrs['purl'] = "http://" + host + "/vs"
    values["q"] = base64.standard_b64encode(encrypted)
    values["ref"] = ref

#check
    if (check == True) and vurl:
        response = ''
        try: 
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
            opener.addheaders = [("User-Agent", USER_AGENT)]
            request = urllib2.Request(attrs["purl"], urllib.urlencode(values), {})
            connection = opener.open(request)
            response = connection.read()
        except:
            values, attrs = reload_values2(content, url)
        if response and (not ("mp4" in response)):
            values, attrs = reload_values2(content, url)

    xbmc.log("param=" + repr(values) + " " + repr(attrs))
    return values, attrs


def get_key(content, content2):
    key = ''
    value = '' 
    try:  
        data = content.split("window['")[-1].split("';")[0]
        value = data.split("'")[2]
        key = content2.split('};n.')[-1].split('=e[')[0] 
    except:
        pass 
    return key, value

def get_access_attrs_old(content):
    values = {}
    attrs = {}

    script = "http://s9.cdnapponline.com" + common.parseDOM(content, "script", ret="src")[0]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
    }
    request = urllib2.Request(script, "", headers)
    request.get_method = lambda: 'GET'
    response = urllib2.urlopen(request).read()

    attrs['purl'] = '/manifests/video/' + content.split("video_token: '")[-1].split("',")[0]  + "/all"

    values['mw_key'] = response.split('mw_key:"')[-1].split('",')[0] 
    values['ad_attr'] = response.split('ad_attr:')[-1].split(',')[0] 
    values['iframe_version'] = response.split('iframe_version:"')[-1].split('"')[0] 
    values['mw_pid'] = content.split("partner_id: ")[-1].split(",")[0] 
    values['adb'] = 'false'    
    
    values[response.split(',mw_pid:this.options.partner_id,')[-1].split(':this.options.domain_id')[0]] = content.split("domain_id: ")[-1].split(",")[0]     
    
    param = response.split('t,e.')[-1].split('";var')[0]
    values[param.split('="')[0]] = param.split('="')[1]

    param = response.split('window._mw_adb};e.')[-1].split('=window[')[0]
    value = response.split('"]="')[-1].split('"},loadSecondLayer')[0]
    values[param] = value

    #key, value = get_key(content, response) 
    #values[key] = value

    xbmc.log("param=" + repr(values) + " " + repr(attrs))

    return values, attrs

#####################################################################################################################

QUALITY_TYPES = (360, 480, 720, 1080)
PLAYLIST_DOMAIN = "moonwalk.cc"
PLAYLIST_DOMAIN2 = "streamblast.cc"

def select_translator(content, url):
    if not ("translations: [[" in content):
        return content, url

    translators = []
    tr_values = []

    data = content.split("translations: [[")[-1].split("]],")[0]
    datal = data.split("],[")

    for item in datal:
        translators.append(item.split(',')[1].replace('"', ''))
        tr_values.append(item.split(',')[0].replace('"', ''))

    if len(translators) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select translator", translators)
        if int(index_) < 0:
            index_ = 0    
    else:
        index_ = 0    
    tr_value = tr_values[index_]

    headers = {
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }

    url_ =  url.replace(url.split("serial/")[-1].split("/iframe")[0], tr_value)
    request = urllib2.Request(url_, "", headers)
    request.get_method = lambda: 'GET'
    response = urllib2.urlopen(request).read()
    return response, url_

def select_season(data):
    seasons =  data.split("seasons: [")[-1].split("],")[0].split(",")
    values = seasons
    if len(seasons) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select season", seasons)
        if int(index_) < 0:
            index_ = -1    
    else:
        index_ = 0    
    if index_ < 0:
        return "", ""
    else:
        return values[index_], str(index_ + 1)


def select_episode(data, url):
    data_, url_ = select_translator(data, url)
    url_ = url_.split('?')[0]
    sindex = None
    eindex = None
    season, sindex = select_season(data_)
    if season == "":
        return "", sindex, eindex

    headers = {
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    values = {
        "season": season,
        "episode": "1"
    }  
    response = tools.get_response(url_, headers, values, "GET")
    
    series = []
    series_ =  response.split("episodes: [")[-1].split("],")[0].split(",")
    for seria in series_:
        series.append(seria)

    if len(series) > 1:
        dialog = xbmcgui.Dialog()
        index_ = dialog.select("Select episode", series)
        if int(index_) < 0:
            return "", sindex, eindex        
    else:
        index_ = 0
    episode = series[index_]
    eindex = str(index_ + 1)
    if episode < 0:
        return "", season, episode

    values = {
        "season": season,
        "episode": episode
    }  
    try: 
        return tools.get_response(url_, headers, values, "GET"), season, episode
    except:
        return "", season, episode


def get_playlist(url):
    manifest_links = {}
    subtitles = None
    season = None
    episode = None

    headers = {
        "Referer": url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    try: 
        request = urllib2.Request(url, "", headers)
        request.get_method = lambda: 'GET'
        response = urllib2.urlopen(request).read()
    except urllib2.HTTPError, error:
        try:
            url_ = dict(error.info())['location']
            request = urllib2.Request(url_, "", headers)
            request.get_method = lambda: 'GET'
            response = urllib2.urlopen(request).read()
        except:
            return manifest_links, subtitles, season, episode 

    #tvshow
    tvshow = response.split("serial_token: '")[-1].split("',")[0]
    if (tvshow != "null"):
        response, season, episode = select_episode(response, url)
        if response == "":
            return manifest_links, subtitles, season, episode 

    if 'subtitles: {"master_vtt":"' in response:
        subtitles = response.split('subtitles: {"master_vtt":"')[-1].split('"')[0]

    values, attrs = get_access_attrs(response, url)

    headers = {}
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    opener.addheaders = [("User-Agent", USER_AGENT)]
    request = urllib2.Request(attrs["purl"], urllib.urlencode(values), headers)
    connection = opener.open(request)
    response = connection.read()
    data = json.loads(response.decode('unicode-escape'))
    playlisturl = data["m3u8"]

    headers = {
        "Host": PLAYLIST_DOMAIN2,
        "Origin": "http://" + PLAYLIST_DOMAIN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
    }
    request = urllib2.Request(playlisturl, "", headers)
    request.get_method = lambda: 'GET'
    response = urllib2.urlopen(request).read()

    urls = re.compile("http:\/\/.*?\n").findall(response)
    for i, url in enumerate(urls):
        manifest_links[QUALITY_TYPES[i]] = url.replace("\n", "")

    return manifest_links, subtitles, season, episode 
   