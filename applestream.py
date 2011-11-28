#!/usr/bin/env python3

#
# Configuration utilisateur
#

# Un répertoire temporaire où sauvegarder le flux à jouer
TMP_DIR="/home/boli/downloads/tv"
# La commande pour lancer le lecteur (streaming sur un fichier local)
# % est remplacé par l'url du fichier à streamer
PLAYER_COMMAND="mplayer -correct-pts -nocache -really-quiet %"

CHANNELS = dict()
CHANNELS["France 2"] = "http://94.247.234.2/streaming/francetv_ft2/ipad.m3u8"
CHANNELS["France 3"] = "http://94.247.234.2/streaming/francetv_ft3/ipad.m3u8"
CHANNELS["France 4"] = "http://94.247.234.2/streaming/francetv_ft4/ipad.m3u8http://94.247.234.2/streaming/francetv_ft4/ipad."
CHANNELS["France 5"] = "http://94.247.234.4/streaming/francetv_ft5/ipad.m3u8"
CHANNELS["France O"] = "http://94.247.234.4/streaming/francetv_fto/ipad.m3u8"
CHANNELS["M6"] = "http://m6-hls-live.adaptive.level3.net/apple/m6replay_iphone/m6live/m6live_ipad.m3u8"
CHANNELS["W9"] = "http://m6-hls-live.adaptive.level3.net/apple/m6replay_iphone/m6live/w9live.m3u8"
CHANNELS["NRJ 12"] = "http://nrj-apple-live.adaptive.level3.net/apple/nrj/nrj/nrj12.m3u8"
CHANNELS["Direct Star"] = "http://cupertino-streaming-1.hexaglobe.com/rtpdirectstarlive/smil:directstar-ipad.smil/playlist.m3u8"
CHANNELS["France 24"] = "http://stream7.france24.yacast.net/iphone/france24/fr/iPad.f24_fr.m3u8"
CHANNELS["BFMTV"] = "http://http5.iphone.yacast.net/iphone/bfmtv/bfmtv_ipad.m3u8"
CHANNELS["BFM Business"] = "http://stream7.bfmbiz.yacast.net/iphone/bfmbiz/bfmbiz_live01.m3u8"
CHANNELS["NRJ Pop Rock"] = "http://nrjlive-apple-live.adaptive.level3.net/apple/nrj/nrjlive-4/appleman.m3u8"
CHANNELS["NRJ Pure"] = "http://nrjlive-apple-live.adaptive.level3.net/apple/nrj/nrjlive-3/appleman.m3u8"
CHANNELS["NRJ Dance"] = "http://nrjlive-apple-live.adaptive.level3.net/apple/nrj/nrjlive-2/appleman.m3u8"
CHANNELS["NRJ Urban"] = "http://nrjlive-apple-live.adaptive.level3.net/apple/nrj/nrjlive-1/nrjurban.m3u8"

#
# Début du script
#

import urllib.request
import os
import subprocess
import time
import sys
import signal

channel_url = ""                # L'url du canal de base
sub_channel_url = ""         # L'url non résolue du sous canal
files = []                            # Les fichiers à télécharger pour la lecture
tmp_file = TMP_DIR + "/stream"
current_file = 0

# L'utilisateur choisit son canal
def get_channel():
    global channel_url
    i = 1
    for key in CHANNELS:
        print(i, "\t" + key)
        i += 1
    channel_choice = int(input("Channel ? "))
    print("")
    i = 1
    for value in CHANNELS.values():
        if i == channel_choice:
            channel_url = value
            break
        i += 1
# L'utilisateur choisit sont sous-canal
def get_sub_channel(url):
    global sub_channel_url
    f = urllib.request.urlopen(url)
    data = f.read().decode(encoding="UTF-8").replace("\x0D", "")
    f.close()
    i = 1
    sub_channels = []
    for line in data.split('\n'):
        if len(line) > 0 and line[0] != "#" and line.find("m3u") != -1:
            sub_channels.append(line)
            print (i, "\t" + line)
            i += 1
    choice = int(input("Sub channel ? "))
    choice -= 1
    try:
        sub_channel_url = sub_channels[choice]
    except IndexError:
        print("Index inexistant")
        get_sub_channel(url)

# Crée une url complète à partir des url du canal et du flux dans le canal
def make_url(base, unresolved):
    if not len(unresolved) > 0:
        raise Exeption("Sub channel url empty")
    resolved = ""
    if unresolved[0] != '/':
        if unresolved.find("http://") != -1:
            resolved = unresolved
        else:
            resolved = base[0:base.rfind('/')+1] + unresolved
    else:
        resolved = base[0:base.find('/', 8)] + unresolved
    return resolved

# Récupère les urls depuis le flux
# Retourne la durée totale récupérée
def fetch_urls(resolved):
    global files
    f = urllib.request.urlopen(resolved)
    data = f.read().decode(encoding="UTF-8").replace("\x0D", "")
    f.close()
    duration = 0
    for line in data.split('\n'):
        if len(line) <= 0:
            continue
        if line[0] == "#" and "EXT-X-TARGETDURATION" in line:
            duration = int(line.split(':')[1])
        elif line[0] != "#" and line.find("ts") != -1:
            resolved_file = make_url(resolved, line)
            if not resolved_file in files:
                files.append(resolved_file)
    return duration

def download_next_file():
    global files, current_file
    if len(files) == 0 or len(files) <= current_file:
        return False
    try:
        page = urllib.request.urlopen(files[current_file])
        data = page.read()
        page.close()
    except Exception:
        return False
    file = open(tmp_file, "a+b")
    file.write(data)
    file.close()
    current_file += 1
    if current_file == 100:
        files = files[1:]
        current_file -= 1
    return True

def stream(resolved):
    duration = fetch_urls(resolved)
    try:
        os.remove(tmp_file);
    except OSError:
        pass
    # un cache de 3 séquences
    print("Caching ...  0%", end="")
    sys.stdout.flush()
    for i in range(1, 4):
        download_next_file()
        print("\b\b\b" + str(i*33) + "%", end="")
        sys.stdout.flush()
    print("\b\b\bDone")
    sys.stdout.flush()
    pid = -1
    try :
        pid = subprocess.Popen(PLAYER_COMMAND.replace('%', tmp_file).split(' ')).pid
        while True:
            start = time.time()
            print('.', end='')
            sys.stdout.flush()
            if len(files) <= 100:
                duration = fetch_urls(resolved)
            download_next_file()
    except KeyboardInterrupt:
        os.kill(pid, signal.SIGKILL)
    return 0

get_channel()
get_sub_channel(channel_url)
resolved_url = make_url(channel_url, sub_channel_url)
stream(resolved_url)
