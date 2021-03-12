#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""RSS notifier to Mattermost
This module notify RSS feed to Mattermost

Example:
    $ python rss2mm.py \
        --url http://path-to-mattermost/hooks/internal-webhook-id \
        --username FeedBot

Attributes:
    url: URL of internal webook of Mattermost
    username: name for a post of Mattermost
    db: database file for managing post. actually it is just a CSV
    feed: list of URL of RSS feed. just a CSV

Todo:
    Nothing.
"""

import os
import sys
import argparse
from logging import getLogger, StreamHandler, FileHandler, Formatter, DEBUG
import time
import csv
import json
import hashlib

import requests
import feedparser
import pandas as pd

class db:
    """ database class to manage posted feed

    Attributes:
        filepath(str): filepath to save database
        
    """
    def __init__(self, filepath:str):
        self.filepath = filepath
        if os.path.exists(filepath):
            self.db = pd.read_csv(filepath, encoding='utf-8', header=0)
        else:
            self.db = pd.DataFrame()

    def get_new_entries(self, entries:pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
        if self.db.empty:
            return entries
        else:
            return entries[~entries['hash'].isin(self.db['hash'])]

    def save_new_entries(self, entries:pd.core.frame.DataFrame):
        if os.path.exists(self.filepath):
            entries.loc[:,['hash', 'title', 'link']].to_csv(
                self.filepath, encoding='utf-8', mode='a', header=False)
        else:
            entries.loc[:,['hash', 'title', 'link']].to_csv(
                self.filepath, encoding='utf-8')

def post_to_mattermost(url:str, message:list[str], username:str):
    header = {'content-Type':'application/json'}
    for m in message:
        time.sleep(1)
        payload = {
            'text': m,
            'username': username,
        }
        resp = requests.post(url, headers=header, data=json.dumps(payload))

def insert_hash(df:pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
    hash_list = list()
    for row in df.iterrows():
        hash_list.append(
            hashlib.sha256(
                str(row).encode()
                ).hexdigest())
    df.insert(0, 'hash', hash_list)
    return df

if __name__ == "__main__":
    logger = getLogger(__name__)
    handler = StreamHandler(sys.stdout)
    handler.setFormatter(Formatter('%(levelname)s: %(asctime)s %(message)s'))
    handler.setLevel(DEBUG)
    logger.setLevel(DEBUG)
    logger.addHandler(handler)

    p = argparse.ArgumentParser()
    p.add_argument('--url', help='url for mattermost incomming webhook', required=True)
    p.add_argument('--username', help='username for mattermost incomming webhook', default='Bot')
    p.add_argument('--db', help='database filepath', default='entries.csv')
    p.add_argument('--feed', help='feed filepath', default='feeds.csv')
    p.add_argument('--feed-encoding', help='encoding of feed file', default='utf-8')


    args = p.parse_args()
    feed = args.feed

    db = db(args.db)
    
    logger.debug('reading %s' % feed)
    with open(feed, 'r', encoding=args.feed_encoding) as f:
        reader = csv.reader(f)
        for line in reader:
            try:
                name = line[0]
                feed = line[1].strip()
                logger.debug('getting feeds from %s' % feed)
                entries = pd.DataFrame(feedparser.parse(feed).entries)
                
                logger.debug('calculating hash')
                entries = insert_hash(entries)

                logger.debug('extracting new feeds')
                entries = db.get_new_entries(entries)

                logger.debug('%d new feeds found' % len(entries.index))
                if not entries.empty:
                    feed_list = list()
                    for key, row in entries.iterrows():
                        feed_list.append('%s: [%s](%s)' % (name, row['title'], row['link']))
                    if len(feed_list) != 0:
                        logger.debug('sending new feeds to mattermost')
                        post_to_mattermost(args.url, feed_list, args.username)
                        logger.debug('saving new feeds')
                        db.save_new_entries(entries)
            except requests.exceptions.MissingSchema as e:
                logger.warn(e)

