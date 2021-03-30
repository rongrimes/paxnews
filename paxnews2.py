#!/usr/bin/python3

# Import instructions to another Pi platform
# ------------------------------------------
# 1. Stop bash accessing serial device:
#   /boot/cmdline.txt: remove console=115200 ???? (the first console string)
# 2. sudo chmod 660 /dev/ttyS0   (should not be necessary, but it is...)
# 3. Test;
#       stty -F /dev/ttyS0 ospeed 19200
#       echo abc > /dev/ttyS0    (should output "abc")
# 4. sudo pip3 install feedparser
# 5. Set pickle file location as required.


import datetime
import pickle
import serial
import signal
import string
import sys
import time
import traceback     # prints info in case of unknown exception

# Special imports for Internet libraries
try:
    import feedparser
except ModuleNotFoundError:
    print("Module not found: feedparser")
    print("Run: sudo pip3 install feedparser")
    sys.exit()

from bs4 import BeautifulSoup
from unicodedata import normalize   # to convert accented chars to non-accented

# Own libraries from immediate directory
from paxconfig import *
from paxlib import *

#-----------------------------------------------------------------
#Global assignments

pickle_file = "/home/pi/python/paxnews/rss_news.pickle"  # need full path since this runs from a service

rss_list = {
#   'Le Pointe-Actualite': 'https://www.lepoint.fr/rss.xml',
    'Top Stories': 'http://rss.cbc.ca/lineup/topstories.xml',
    'World': 'http://rss.cbc.ca/lineup/world.xml',
    'Canada': 'http://rss.cbc.ca/lineup/canada.xml',
    'Politics': 'http://rss.cbc.ca/lineup/politics.xml',
    'Business': 'http://rss.cbc.ca/lineup/business.xml',
    'Health': 'http://rss.cbc.ca/lineup/health.xml',
    'Arts & Entertainment': 'http://rss.cbc.ca/lineup/arts.xml',
    'Technology & Science': 'http://rss.cbc.ca/lineup/technology.xml',
    'Offbeat': 'http://rss.cbc.ca/lineup/offbeat.xml',
    'Aboriginal': 'http://www.cbc.ca/cmlink/rss-cbcaboriginal',

#Sports News
    'Sports': 'http://rss.cbc.ca/lineup/sports.xml',
    'MLB': 'http://rss.cbc.ca/lineup/sports-mlb.xml',
    'NBA': 'http://rss.cbc.ca/lineup/sports-nba.xml',
    'Curling': 'http://rss.cbc.ca/lineup/sports-curling.xml',
    'CFL': 'http://rss.cbc.ca/lineup/sports-cfl.xml',
    'NFL': 'http://rss.cbc.ca/lineup/sports-nfl.xml',
    'NHL': 'http://rss.cbc.ca/lineup/sports-nhl.xml',
    'Soccer': 'http://rss.cbc.ca/lineup/sports-soccer.xml',
    'Figure Skating': 'http://rss.cbc.ca/lineup/sports-figureskating.xml',

#Regional News
    'British Columbia': 'http://rss.cbc.ca/lineup/canada-britishcolumbia.xml',
    'Kamloops': 'http://rss.cbc.ca/lineup/canada-kamloops.xml',
    'Calgary': 'http://rss.cbc.ca/lineup/canada-calgary.xml',
    'Edmonton': 'http://rss.cbc.ca/lineup/canada-edmonton.xml',
    'Saskatchewan': 'http://rss.cbc.ca/lineup/canada-saskatchewan.xml',
    'Saskatoon': 'http://rss.cbc.ca/lineup/canada-saskatoon.xml',
    'Manitoba': 'http://rss.cbc.ca/lineup/canada-manitoba.xml',
    'Thunder Bay': 'http://rss.cbc.ca/lineup/canada-thunderbay.xml',
    'Sudbury': 'http://rss.cbc.ca/lineup/canada-sudbury.xml',
    'Windsor': 'http://rss.cbc.ca/lineup/canada-windsor.xml',
    'Kitchener-Waterloo': 'http://rss.cbc.ca/lineup/canada-kitchenerwaterloo.xml',
    'Toronto': 'http://rss.cbc.ca/lineup/canada-toronto.xml',
    'Ottawa': 'http://rss.cbc.ca/lineup/canada-ottawa.xml',
    'Montreal': 'http://rss.cbc.ca/lineup/canada-montreal.xml',
    'New Brunswick': 'http://rss.cbc.ca/lineup/canada-newbrunswick.xml',
    'Prince Edward Island': 'http://rss.cbc.ca/lineup/canada-pei.xml',
    'Nova Scotia': 'http://rss.cbc.ca/lineup/canada-novascotia.xml',
    'Newfoundland & Labrador': 'http://rss.cbc.ca/lineup/canada-newfoundland.xml',
    'North': 'http://rss.cbc.ca/lineup/canada-north.xml'
   }

#-----------------------------------------------------------------
def init_rssfeed():
    ''' Build list of News feeds '''
    global rssfeedlist

#   rssfeedlist.append('Le Pointe-Actualite')   # Test for French chars.
    rssfeedlist.append('Top Stories')
    rssfeedlist.append('World')
    rssfeedlist.append('Canada')
    rssfeedlist.append('Toronto')
    rssfeedlist.append('Montreal')
    rssfeedlist.append('Politics')
    rssfeedlist.append('Edmonton')
    rssfeedlist.append('British Columbia')
    rssfeedlist.append('Kamloops')
    rssfeedlist.append('Calgary')
    rssfeedlist.append('Saskatchewan')
    rssfeedlist.append('Saskatoon')
    rssfeedlist.append('Manitoba')
    rssfeedlist.append('Thunder Bay')
    rssfeedlist.append('Sudbury')
    rssfeedlist.append('Windsor')
    rssfeedlist.append('Kitchener-Waterloo')
    rssfeedlist.append('Ottawa')
    rssfeedlist.append('New Brunswick')
    rssfeedlist.append('Prince Edward Island')
    rssfeedlist.append('Nova Scotia')
    rssfeedlist.append('Newfoundland & Labrador')
    rssfeedlist.append('North')
    rssfeedlist.append('Aboriginal')
    rssfeedlist.append('Business')
    rssfeedlist.append('Health')
    rssfeedlist.append('Arts & Entertainment')
    rssfeedlist.append('Technology & Science')
    rssfeedlist.append('Offbeat')

#-----------------------------------------------------------------
def next_rssfeed(start_site):
    '''Get next News topic list being sensitive that topics can get dropped.'''
    global rssfeedlist

    delete_entry = False

    while True:
        if start_site not in rssfeedlist or start_site == rssfeedlist[-1]:
            new_site = rssfeedlist[0]
        else:
            new_site = rssfeedlist[rssfeedlist.index(start_site) + 1]

        if delete_entry:
            rssfeedlist.remove(invalid_site)
            delete_entry = False

        try:
            python_wiki_rss_url = rss_list[new_site]
        except KeyError:
            print('"' + new_site + '" is not a valid News topic. Removed.')
            start_site = new_site  # return in the loop & get the next entry
            invalid_site = new_site
            delete_entry = True     # delete entry after getting next site
            continue

        try:
            rss_feed = feedparser.parse( python_wiki_rss_url )
        except:
            # Rare case of changing network connections causes failure here.
            # Log error and force read from storage
#           print("Weird error")
#           traceback.print_exc()    # log error for review. 
            rss_feed = {"entries":[]} # build dummy entry to force read from storage 

        return new_site, rss_feed # we succeeded in getting a valid new site


#-----------------------------------------------------------------
def save_rss(rss_site, news_time, news):
    '''
    Save: 
    rss_save = (rss_site, rss_news)
    rss_news = {"rss_sitex":(date-time, news),
                "rss_sitey":(date-time, news), ...}
    '''
#   Get existing pickle file to update.
    try:
        f = open(pickle_file, "rb")
        _, rss_news = pickle.load(f)  # (rss_site, rss_news)
                                      # ignore existing rss_site value
        f.close()
    except IOError:
#       print("save_rss error")
        rss_news = {}     # create empty dictionary to rebuild rss_news 

#   Update the latest value for rss_site
    rss_news[rss_site] = (news_time, news)
    rss_save = (rss_site, rss_news)

    f = open(pickle_file, "wb")
    pickle.dump(rss_save, f)
    f.close()


def get_rss(rss_site):
    try:
        f = open(pickle_file, "rb")
#       rss_news = pickle.load(f)
        rss_site, rss_news = pickle.load(f)  # (rss_site, rss_news)
        f.close()

        news_time, news = rss_news[rss_site]
    except IOError:
        # if we get here, then we're offline, AND no pickle file to get the news from.
        # The original default action in the code was to get an empty list - which we duplicate here.
        news_time = datetime.datetime.now()
        news = []   # return an empty list. The topic will appear, but nothing else.
        rss_site = ''

#   print("get_rss:",rss_site, news_time)
    return rss_site, news_time, news

#-----------------------------------------------------------------
def show_details(details):
    soup = BeautifulSoup(details, "html.parser")
    news_line = ">>" + soup.get_text(strip=True)
    linesegments = prep(news_line)

    display_lines(linesegments, 2)
    clear_screen(0.5)

#-----------------------------------------------------------------
def prep(news_line):
    # news_line = 'unicode string'
    #clear non-visible chars from string
#   news_line = ''.join([c for c in news_line if ord(c) < 128 and ord(c) > 31])
    news_line = normalize("NFD", news_line).encode('ascii','ignore').decode("utf-8")

    linesegments = []
    start = 0
    linesize = len(news_line)

    while start <= linesize:
        if start+16 >= linesize:    # then we have the last segment - no need to break up
            #print(start, top, news_line[start:])
            linesegments.append(news_line[start:])
            break
        elif news_line[start+16:start+17] == " ": # there's a space at char 17, and we can break at char 16.
            linesegments.append(news_line[start:start+16])
            start += 17
        else:
            index = news_line.rfind(" ", start, start+16)  # find rightmost space to split at.
            #print(start, index, news_line[start:top])
            if index == -1:      # no space found, use 16 chars
                linesegments.append(news_line[start:start+16])
                start += 16
                #print(start, news_line[start], news_line[start+1])
            else:                     # found a space & we have fewer than 16 chars 
                linesegments.append(news_line[start:index])
                start = index + 1

    return linesegments

#-----------------------------------------------------------------
def help_msg():
    '''show help msg '''
    linesegments = []
    linesegments.append("1=Show Subject")
    linesegments.append("4=Next Subject")
    linesegments.append("2=Prev item")
    linesegments.append("5=Next item")
    linesegments.append("3=Get more info")
    linesegments.append("*=Configure me")
    linesegments.append("0=Help")

#   Ignore key press value
    display_lines(linesegments, 3)
    clear_screen(0.5)

#-----------------------------------------------------------------
def disp_topic(rss_site, news_time, news_is_live):
    init_screen(0.5)                     # repeated here to restore backlight each cycle.

    '''Display the topic & time. Called at start of topic or if requested.'''
    linesegments = []

#   str_time = datetime.datetime.now().strftime("%H:%M  %d %B")
    str_time = news_time.strftime("%H:%M  %d %B")
    str_time = cap(str_time, 16)
    linesegments.append(str_time)

    rss_line = cap(rss_site, 16) 
    linesegments.append(rss_line)

    if not news_is_live:
        linesegments.append('(Offline: news')
        linesegments.append('from file)')

    linesegments.append('Press "0" for')
    linesegments.append('Help.')

    display_lines(linesegments, 2)
    clear_screen(0.5)

#-----------------------------------------------------------------
# UTILITIES
def cap(s, leng):
    '''Returns s up to a max length of leng'''
    return s if len(s)<=leng else s[0:leng]

# Arm signal to end program.
def handler(signum, frame):
    ''' A sigint interrupt will get caught here, and will in effect be the same as
        getting a ^C at the keyboard.'''
        # Doesn't appear to be working...
    raise KeyboardInterrupt

#-----------------------------------------------------------------
# Arm sigint to cause proceed to graceful end.
signal.signal(signal.SIGINT, handler)

# Initialize pax display & keypad
#print("Call init_pax")
init_pax()

#Show IP address
get_IP2()
 
# Initialize News feed
rssfeedlist = []    # global: built in init_rssfeed, (occasionally) updated in next_rssfeed
init_rssfeed()
rss_site = ""
rss_site, _, _ = get_rss(rss_site)  # get rss_site - ignore other stuff

# Principal loop

try:
    while True:
        rss_site, rss_feed = next_rssfeed(rss_site)

        index = 0
#       print(rss_site+" entries:", len(rss_feed["entries"]))

        # If we are offline, then rss_feed is empty. Then get news from pickle file.
        # Otherwise, save a copy for the pickle file.
        if len(rss_feed["entries"]) == 0:
            news_is_live = False
            _, news_time, rss_feed["entries"] = get_rss(rss_site) # don't
                                                    # overwrite rss_site
        else:
            news_is_live = True
            news_time = datetime.datetime.now()
            save_rss(rss_site, news_time, rss_feed["entries"])

        disp_topic(rss_site, news_time, news_is_live)

        while index < len(rss_feed["entries"]):
            entry = rss_feed["entries"][index]
            news_line = entry["title"] #Capture news item

            linesegments = prep(news_line)

            kbd_input, keyvalue = display_lines(linesegments, 2)
            #kbd_input in ["none", "single key", "Long", "Double"]

            if kbd_input == "none":
                clear_screen(0.5)
                index += 1
            else:
                clear_screen(0)
                if   keyvalue == "0":             # Show Help message
                    help_msg()
                    index += 1
                elif keyvalue == "1":             # redisplay current topic, redisplay news item
                    disp_topic(rss_site, news_time, news_is_live)
                elif keyvalue == "2":             # go back a news item
                    index = max(0, index-1)
                elif keyvalue == "3":             # we want the details...
                    show_details(entry["summary"])
                    index += 1
                elif keyvalue == "4":             # get next topic
                    break
                elif keyvalue == "5":             # get next news item
                    index += 1
                elif keyvalue == "*":             # call the config routines
                    config_mypi()
                else:                         # keys: 6,7,8,9,#
                    index += 1

except KeyboardInterrupt:
    print("\rKeyboardInterrupt")
    GPIO.cleanup()   # Clear any current status

# Clear Screen
clear_screen(0)

# Turn Off Back light
turnoff_backlight()

