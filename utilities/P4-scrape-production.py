#!/usr/bin/env python
# coding: utf-8

import requests
import time
import random
from bs4 import BeautifulSoup as soup
import os
from datetime import datetime
import pickle

# Project 4 production scraping script
# Digest code from test workbook and set up production loops.
# 1. Navigate to YJ forum
# 2. Navigate to last page
# 3. Navigate to last thread
# 4. Begin thread loop
#   4a. Test: Is this end-of-forum?
#       4aa. Yes. Goodbye.
#       4ab. No. Carry on, then.
#   4b. Begin page loop
#       4ba. Rip all post data & save to dictionary list
#       4bb. Test: is there another thread page?
#           4bba. Yes. Return to 4b.
#           4bbb. No. Break.
#   4c. Test: Is it time to dump data? (Is post_counter over 100?)
#       4ca. Yes. Dump data and reset.
#       4cb. No. Keep digging.

# Step 1. Forum navigation
# Step 2. Navigate to last page
# Step 3. Navigate to last thread
def forum_start_scrape(forum_id):
    """Takes a jeepforum.com forum id and returns a link to its oldest thread."""
    root = 'https://www.jeepforum.com/forum/'
    forum_response = requests.get(root+forum_id)
    forum_code = forum_response.content
    forum_soup = soup(forum_code,features='lxml')
    last_page_link = forum_soup.find('td', class_='alt1 lastpage')
    last_page_url = last_page_link.find('a').get('href')
    thread_list_response = requests.get(last_page_url)
    thread_list_code = thread_list_response.content
    thread_list_soup = soup(thread_list_code,features='lxml')
    thread_list_links = thread_list_soup.find_all('a', class_='thread_title_link')
    thread_url = thread_list_links[-1].get('href')
    return thread_url

# Utility function to pull numbers off the end of strings
def pull_id(s):
    """Takes a jeepforum id string from a div, url, or etc., pops off and returns 
    the digits at right."""
    head = s.rstrip('0123456789')
    tail = s[len(head):]
    return int(tail)

# Annoying notice plastered across many sigs when you're not logged in as a user 
# with so many posts
WAHWAH = """To view links or images in signatures your post count must be 10 or 
greater. You currently have 0 posts."""

# Step 4. Thread loop begins with passing of a new thread url
def scrape_thread(thread_url, forum_id):
    """Takes a thread URL, rips all post data from the thread.
    Usually this is actually a fake URL ending in -next/, so we must be careful 
    to get the real URL at the beginning of the function from the requests object.
    Returns either None if the thread didn't exist
    (got the vBulletin No threads newer... message)
    or a list of dictionaries containing the post data and a URL
    for the next newer thread."""
    thread_response = requests.get(thread_url)
    print("Response ", thread_response.status_code, " for ", thread_url)
    thread_code = thread_response.content
    thread_soup = soup(thread_code,features='lxml')
    # Step 4a: Have we gotten the end-of-forum message?
    EOF = thread_soup.find('td', class_='tcat')
    # Some pages have no such tag, so we need to protect against the infernal
    # 'NoneType' object has no attribute 'get_text' error.
    if EOF != None:
        EOF = EOF.get_text()
    if EOF == 'vBulletin Message':
        # Step 4aa: done with forum
        return None, None
    # Step 4ab: carry on
    # Step 4b: begin page loop
    # first get the real thread URL and therefore thread id number and title
    thread_url = thread_response.request.url
    thread_title = thread_url.split('/')[-2]
    thread_id = pull_id(thread_title)
    thread_title = thread_title.rstrip('0123456789-')
    title_words = thread_title.split('-')
    thread_title = ' '.join(title_words)
    post_dicts = []
    more_page = True
    while more_page:
        # Step 4ba: rip all post data
        new_posts, more_page, page_url = page_rip(thread_soup, thread_id,
                                                thread_title, forum_id)
        post_dicts += new_posts
        # Step 4bb: is there another thread page?
        if more_page:
            thread_response = requests.get(page_url)
            print("Response ", thread_response.status_code, " for ", page_url)
            thread_code = thread_response.content
            thread_soup = soup(thread_code,features='lxml')
    new_thread_url = thread_url.rstrip('/')+'-next/'    
    return post_dicts, new_thread_url

# Step 4ba: rip all post data
def page_rip(page_soup, thread_id_num, thread_title, forum_id):
    """Takes a BeautifulSouped thread page and rips all post data to dictionaries.
    Returns a list of the post dictionaries and True if there is a Next Page in the
    thread along with a url for the next thread page; False and None otherwise."""
    global WAHWAH
    posts = page_soup.find_all('div', itemprop='text')
    # this will also pull 10 usernames from the recent posts box at the bottom, 
    # but we won't pull those index numbers in the loop so it doesn't matter
    usernames = page_soup.find_all('div', itemprop='contributor')
    post_dicts = []
    for i, post in enumerate(posts):
        post_dicts.append({})
        # encoding is per html ISO-8859-1
        post_dicts[i]['post'] = ' '.join(post.get_text().split())
        post_dicts[i]['username'] = ' '.join(usernames[i].get_text().split())
        # since not everyone has a signature, navigate up into the enclosing 
        # <div class="main-column-text">
        # and then pull the enclosed <div class="vs_sig">'s text and elmininate 
        # any nag messages
        sig = post.parent.find('div',class_='vs_sig')
        try:
            post_dicts[i]['sig'] = ' '.join(sig.get_text().replace(WAHWAH,
                                        '').split())
        except:
            # there is no signature, no problem
            post_dicts[i]['sig'] = None
        post_dicts[i]['postid'] = pull_id(post['id'])
        # kind of incredible that this is the way they mark post titles
        title = post.parent.find('strong', itemprop='alternativeHeadline')
        try:
            post_dicts[i]['title'] = title.get_text()
        except:
            # there is no post title, no problem
            post_dicts[i]['title'] = None
        post_dicts[i]['threadid'] = thread_id_num
        post_dicts[i]['thtitle'] = thread_title
        date_str = post.parent.parent.parent.parent.find('span',
                                        itemprop='dateCreated').get_text()
        # example date: 03-19-2020, 08:10 AM
        post_date = datetime.strptime(date_str, '%m-%d-%Y, %I:%M %p')
        post_dicts[i]['postdate'] = post_date
        post_dicts[i]['forum'] = forum_id
    next_page_link = page_soup.find('a',rel='next')
    if next_page_link == None:
        return post_dicts, False, next_page_link
    else:
        return post_dicts, True, next_page_link.get('href')

# Step 4ca. Dump data.
def dump_posts(post_list, forum_id, file_seq):
    """Pickles a list of posts once it has grown past 100 entries.
    By solemn convention pickles are always stored in the cellar."""
    with open('jf_'+forum_id+str(file_seq)+'.pkl','wb') as cellar:
        pickle.dump(post_list, cellar)


# Step 1. Kick off with forum f12, the Wrangler YJ (1987-1995) forum
forum_code = 'f12'
print("Scraping forum ", forum_code)
post_dicts = []
file_seq = 0
thread_url = forum_start_scrape(forum_code)
while thread_url != None:
    new_posts, thread_url = scrape_thread(thread_url, forum_code)
    post_dicts += new_posts
    if len(post_dicts) > 100:
        dump_posts(post_dicts, forum_code, file_seq)
        file_seq += 1
        post_dicts = []
print("Forum scraped.")