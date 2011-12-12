#!/usr/bin/env python

"""
debaser.py
v0.52 - 12122011 [ frozen 3:21 PM EST 12/11/2011 ]
  * Added support for uppercase file extensions on urls (ex: .JPG, .GIF)
  * Added support for .jpeg file extension
  * Added license information to heading comment (see below).
  * Removed counter from main loop; used enumerate() to obtain index and len() to obtain totals in error summary

v0.51 - 12112011 [ frozen 5:14 PM EST 12/11/2011 ]
  * fixed bug with non-imgur urls that are downloadable
  * added permalink output in verbose mode to add additional log information
  * fixed cross-compatibility bug by using os.path.join & posixpath (untested)
  * fixed bug with limit being passed as string...now it actually works!

v0.50 - 12112011 [ frozen 3:16 PM EST 12/11/2011 ]

An image scouring tool for reddit.

Copyright (c) 2011 Andy Kulie.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import reddit
import os
import urllib
from urlparse import urlparse # for parsing out *.jpg from url (python 2)
from optparse import OptionParser # for parsing command line options
from posixpath import basename # for url splitting on non-imgur urls

# add system argument for verbose mode
verbose_mode = False
current_version = "%prog 0.52-12122011"
current_dir = os.getcwd()

## start parse arguments
usage = "usage: %prog [options] arg"
parser = OptionParser(usage, version=current_version)
parser.add_option("-s", "--subreddit", dest="subreddit", default="pics", help="name of subreddit | defaults to %default")
parser.add_option("-f", "--filter", dest="filter", default="hot", help="filter: hot, top, controversial, new | defaults to %default")
parser.add_option("-l", "--limit", dest="limit", default=5, help="limit of submissions to gather | defaults to %default")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose")
parser.add_option("-q", "--quiet", action="store_false", dest="verbose")
(options, args) = parser.parse_args() 
if options.verbose:
    verbose_mode = True
## end parse arguments

"""
submissions(subr_name, subr_filter, subr_limit)
  Returns a generator for the submissions in a given
  subreddit.

  subr_name - name of subreddit [STRING]
  subr_filter - top, hot, controversial, new [STRING]
  subr_limit - limit of submissions to return [INTEGER]

  returns submissions [GENERATOR]
"""
def submissions(subr_name='pics', subr_filter='hot', subr_limit=5):
    if (subr_filter == 'hot'):
        return r.get_subreddit(subr_name).get_hot(limit=subr_limit)
    elif (subr_filter == 'top'):
        return r.get_subreddit(subr_name).get_top(limit=subr_limit)
    elif (subr_filter == 'new'):
        return r.get_subreddit(subr_name).get_new(limit=subr_limit)
    elif (subr_filter == 'controversial'):
        return r.get_subreddit(subr_name).get_controversial(limit=subr_limit)

"""
build_imgur_dl(url)
  Return a direct link url for imgur based on an indirect
  url tuple from urlparse

  url - a parsed url tuple from urlparse [TUPLE]

  returns direct link url [STRING]
"""
def build_imgur_dl(url):
    return 'http://' + 'i.' + url.netloc + url.path + '.jpg'
    # to be added: exceptions for if it's a png or gif

# initialize reddit object
r = reddit.Reddit(user_agent='sample_app')

# get submissions as a list of objects
subr_name = options.subreddit
subr_filter = options.filter
subr_limit = int(options.limit) # make this an int instead of a string, duh!
if verbose_mode: print "Scouring subreddit " + subr_name + " for " + subr_filter + " submissions (limit " + str(subr_limit) + ")\nPlease wait..."

sublist = submissions(subr_name, subr_filter, subr_limit) #replace default with user input
sublist = list(sublist)

# main parse & download loop
success = len(sublist)
summary = []
for index, i in enumerate(sublist):
    if verbose_mode: 
        print str(index) + ": " + i.title + " :: " + i.url
        print "permalink = " + i.permalink
    # parse out the url to get its parts as a 6-tuple
    parsed_url = urlparse(i.url)
    if (parsed_url.netloc == 'i.imgur.com'):
        if verbose_mode: print "Direct imgur link.  Downloading..."
        savedto = urllib.urlretrieve(i.url, current_dir + parsed_url.path)
        if verbose_mode: print savedto
    elif (parsed_url.netloc == 'imgur.com'):
        if (parsed_url.path[0:3] == '/a/'):
            if verbose_mode: print "Imgur album path not yet supported."
            summary.append(i.url + " is an Imgur album path.\nThese are not yet supported by debaser.")
            success -= 1
            # add support using imgur album downloader & make subdirectory for it
        else:
            if verbose_mode: print "Indirect imgur link.  Downloading..."
            savedto = urllib.urlretrieve(build_imgur_dl(parsed_url), current_dir + parsed_url.path + '.jpg') #build imgur direct link & download it
            if verbose_mode: print savedto
    else:
        plen = len(parsed_url.path)
        if (parsed_url.path[plen-4:plen].lower() == '.jpg' or parsed_url.path[plen-4:plen].lower() == '.gif' or parsed_url.path[plen-4:plen].lower() == '.png' or  parsed_url.path[plen-4:plen].lower() == '.jpeg'): # added .lower() to all results to allow for uppercase file extensions
            if verbose_mode: print "Unknown source.  Downloading..."
            savedto = urllib.urlretrieve(i.url, os.path.join(current_dir, basename(parsed_url.path)))
            print savedto
        else:
            if verbose_mode: print "Unknown HTML encountered.  Download abort."
            summary.append(i.url + " is an unsupported URL.\nNo image files found.")
            success -= 1

if verbose_mode: 
    print "\n" + str(success) + " of " + str(len(sublist)) + " files downloaded."
    if len(summary) > 0:
        print "\nSummary of errors:"
        for i in summary:
            print i

    # to be added - urllib.urlretrieve exception IOError if something goes wrong.  Possibly break into a subroutine to simplify and make it pretty.
