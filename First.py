#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0105,C0325
'''
Created on Monday Mar 11 2019
@Original author: Sean.Titmarsh https://github.com/seantitmarsh/Roosterteeth.com
@Discord integration by: ThatOneRoadie https://github.com/ThatOneRoadie/Roosterteeth.com.Discord
'''

import sys
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')
#Some moron decided to use https://emojipedia.org/large-blue-circle/. This protects from that.
#import praw
import sqlite3
import datetime
import pytz
import json
import urllib2
import discord_webhook
from discord_webhook import DiscordWebhook, DiscordEmbed

#Select which sites/properties you want to pull and publish via webhook.
SITE = ['achievement-hunter', 'rooster-teeth','funhaus','']
#Discord Webhook
webhookurl = 'https://discordapp.com/api/webhooks/PUTTHERESTOFYOURWEBHOOKHERE'
#database file location
dbloc = '/home/bots/Webhooks/First.db'
#Database Table Filler
submissionId = '0'
reddit = '0'


def get_today():
    '''
    Get the date 90 days ago, used for url in get_surveys()
    Arguments
    None required
    Function Variables
    today -- Today's date
    offset -- Number of days to subtract from today's date (Default is 90)
    Returns
    date - String repersentation of date the date 90 days ago.
           Type: string (Format YYYY-MM-DD)
    '''
    central = pytz.timezone('US/Central')
    now = datetime.datetime.now(central) # timezone-aware datetime.utcnow()
    print(str(now) + '\r')
    today = datetime.datetime(now.year, now.month, now.day)
    return str(today)[:-9]


def get_time(length):
    '''
    Please don't look at this. -Sean
    '''
    hour = length/3600
    hour_sub = hour * 60
    minute = length/60
    second = length%60
    if hour >= 1:
        if minute <10:
            if second < 10:
                time = str(hour) + ':0' + str(minute - hour_sub) + ':0' + str(second)
            else:
                time = str(hour) + ':0' + str(minute - hour_sub) + ':' + str(second)
        else:
            if second < 10:
                time = str(hour) + ':' + str(minute - hour_sub) + ':0' + str(second)
            else:
                time = str(hour) + ':' + str(minute - hour_sub) + ':' + str(second)
    else:
        if second < 10:
            time = str(minute) + ':0' + str(second)
        else:
            time = str(minute) + ':' + str(second)
    print('Video Lengh: ' + time + '\r')
    return time

'''
ROOSTERTEETH.COM API FUNCTIONS
'''
def get_episodes():
    req = urllib2.Request('https://svod-be.roosterteeth.com/api/v1/episodes', headers={'User-Agent' : 'RT-Video-Discord-Video-Scraper'})
    page = urllib2.urlopen(req).read()
    info = json.loads(page)
    return info['data']

def check_if_early(episode):
    first = episode['attributes']['sponsor_golive_at']
    public = episode['attributes']['public_golive_at']
    if first == public:
        return False
    else:
        return True

'''
EPISODE FUNCTIONS
Note, to work, pass reddit to each function. Otherwise, the praw instance won't be logged in.
'''

def check_videoId(videoId):
    '''
    '''
    conn = sqlite3.connect(dbloc)
    c = conn.cursor()
    c.execute('SELECT * FROM Videos WHERE videoId = (?)', (videoId,))
    line = c.fetchone()
    if line == [] or line is None:
        match = 'New'
    else:
        match = 'Old'
    conn.close()
    return match

def save_videoId(title, submissionId, videoId, episode, today, reddit):
    '''
    '''
    conn = sqlite3.connect(dbloc)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO Videos VALUES(?, ?, ?, ?, ?)', (title, submissionId, videoId, today, str(episode)))
    except:
        try:
            c.execute('INSERT INTO Videos VALUES(?, ?, ?, ?, ?)', (str(title), submissionId, videoId, today, 'Exception, see messages'))
        except:
            c.execute('INSERT INTO Videos VALUES(?, ?, ?, ?, ?)', ('Exception, see messages', submissionId, videoId, today, 'Exception, see messages'))
    conn.commit()
    conn.close()


def get_color(video_site):
    return {
        'rooster-teeth':10624289,
        'achievement-hunter':9036558,
        'funhaus':16737792,
    }.get(video_site,16777215)

def run_bot():
    today = get_today()
    episodes = get_episodes()     # Obtain latest episode feed
    count = 0
    base_link = 'https://www.roosterteeth.com'
    while count <= 19:
        new_episode = episodes[count]
        count += 1    # Increment episode counter here, if something breaks it willl skip to the next episode
        #print(new_episode)
        print('\r')
        print('Now running episode ' + str(count - 1) + '\r')
        e_title = str(new_episode['attributes']['title'])
        episode_title = e_title.replace("’", "'").replace('…', '...')
        print('Video Title: "' + episode_title + '"\r')
        video_site = str(new_episode['attributes']['channel_slug'])
        print('Site: ' + video_site + '\r')
        if video_site not in SITE:
            continue
        episode_id = str(new_episode['id'])
        print('Checking if video: "' + episode_title + '" and id: "' + episode_id + '" is new.\r')
        new = check_videoId(episode_id)
        if new == 'New':
            full_title =  str(new_episode['attributes']['show_title']) + ': ' + episode_title
            showname = str(new_episode['attributes']['show_title'])
            desc = str(new_episode['attributes']['caption'])
            live_time = str(new_episode['attributes']['sponsor_golive_at'])
            episode_link = base_link + str(new_episode['canonical_links']['self'])
            first_only = str(new_episode['attributes']['is_sponsors_only'])
            first_early = str(check_if_early(new_episode))
            firsticon=''
            firstcontent=''
            print('VIDEO INFORMATION:-------------------------------------------------\r')
            print('Full Title: ' + full_title + '\r')
            print('Episode ID: ' + episode_id + '\r')
            print('Episode Link: ' + episode_link + '\r')
            print('FIRST Exclusive?: ' + first_only + '\r')
            print('FIRST Early?: ' + first_early + '\r')
            ep_thumbnail = str(new_episode['included']['images'][0]['attributes']['thumb'])
            show_thumbnail = str(new_episode['included']['images'][2]['attributes']['thumb'])
            if first_only == 'True':
                print('\rVideo is a First Exclusive Series, building hook\r')
                firsticon='https://i.imgur.com/7EhUum3.png'
                firstcontent='First-Exclusive'
            elif first_early == 'True':
                print('\rVideo is a First Early Series, building hook\r')
                firsticon='https://i.imgur.com/a4oXyWe.png'
                firstcontent='First Early Access'
            #create embed object for webhook
            colorset=16777215
            colorset=get_color(video_site)
            webhook = DiscordWebhook(url=webhookurl,avatar_url='https://assets.roosterteeth.com/img/apple-touch-icon.png',content='A new '+showname+' episode is live!')
            embed = DiscordEmbed(description=desc, color=colorset)
            # set author
            embed.set_author(name=full_title, url=episode_link, icon_url=firsticon)
            # set image
            embed.set_image(url=ep_thumbnail)
            # set thumbnail
            embed.set_thumbnail(url=show_thumbnail)
            # set footer
            embed.set_footer(text=showname)
            # set timestamp (default is now)
            print(live_time)
            embed.set_timestamp(live_time)
            # add embed object to webhook
            webhook.add_embed(embed)
            print('Executing Webhook')
            webhook.execute()
            save_videoId(full_title, submissionId, episode_id, new_episode, today, reddit)
        else:
            print('Old Video\r')
            new = False
        print('Finished video ' + str(count - 1) + '\r')


if __name__ == '__main__':

    try:
        run_bot()
    except SystemExit:
        print('Exit called.')
