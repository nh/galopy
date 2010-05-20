#!/usr/bin/python
#
# webr_update.py: This script fetches data on photo sets and contained photos from flickr.com
#                 and dumps it into a pickled file. This pickled database is used by webr.py 
#                 Does not need authentication from Flickr since we fetch only public data.
#                 
#                 Run this periodically to keep your local db in sync with your Flickr account.
#      
# author:   Deepak Sarda
#           firstname@antrix.net
#
# requires: flickrapi (http://beej.us/flickr/flickrapi/)
#

__author__      = 'Deepak Sarda'
__version__     = '0.3'
__copyright__   = '(c) 2006 Deepak Sarda'
__license__     = 'GPL'
__url__         = 'http://www.antrix.net/stuff/webr/'

import os, cPickle
import flickrapi

# Remember to change FUser to your Flickr userid!
from config import FUser, FlickrDBFile

# The rest can be left as is.
FKey = "04133797314d6ff600f07314fe061643"
FSecret = "b9f548992d4c62b0"

fapi = flickrapi.FlickrAPI(FKey, FSecret)

# All responses from flickrapi are python unicode strings.
# So ideally we should be explicitly encoding them back
# to 'utf-8' before printing. (Flickr saves as utf-8)

class User:
    """This class is used to store user specific info like name, userid, etc."""
    def __init__(self):
        rsp = fapi.people_getInfo(api_key = FKey, user_id = FUser)
        for x in rsp[0]:
            print x
        #if rsp[0] != True:
        #    Print an error
        #    fapi.testFailure(rsp, exit=False)
        #    raise RuntimeError
        
        rsp = rsp[0]
        
        try:
            self.id = FUser
            self.username = rsp.find('username').text
            self.photos_url = rsp.find('photosurl').text
            self.profile_url = rsp.find('profileurl').text
            self.realname = rsp.find('realname').text
            self.location = rsp.find('location').text
        except:
            print "Missing info"
 
    def __str__(self): return self.username
        
class Photo:
    """All Photo specific stuff goes in here."""
    def __init__(self, photo_id, update = True):
        self.img_urls = {}
        self.id = str(photo_id)
        if update: self.update()
        
    def __str__(self): return u"%s: %s" % (self.id, self.title)
        
    def update(self):
        rsp = fapi.photos_getInfo(api_key = FKey, photo_id = self.id)
        if rsp.attrib['stat'] == "fail":
            # Print an error
            fapi.testFailure(rsp, exit=False)
            raise RuntimeError
        
        p = rsp[0]
        self.update_with_chunk(p)
        
    def update_with_chunk(self, p):
        """This method is needed since some flickr api calls return 
        this info as part of other calls. So we just reuse that info
        instead of making another remote api call."""
        print p.find('dates')
        self.title = p.find('title').text
        self.desc = p.find('description').text
        self.taken = p.find('dates').attrib["taken"]
        self.comment_count = p.find('comments').text
        self.flickr_url = p.find('urls')[0].text
        
    def update_img_urls(self):
        """"""
        rsp = fapi.photos_getSizes(api_key=FKey, photo_id=self.id)
        if rsp.attrib['stat'] == "fail":
            # Print an error
            fapi.testFailure(rsp, exit=False)
            raise RuntimeError

        for s in rsp[0].findall('size'):
            self.img_urls[s.attrib['label']] = s.attrib['source']
            

class PhotoSet:
    def __init__(self, set_id, update = True):
        self.id = str(set_id)
        self.photos = []
        if update: self.update()
    
    def __str__(self):
        return u"Photoset # %s - %s. (%s photos)" % (self.id, self.title, self.pcount)
    
    def is_consistent(self):
        if not len(self.photos) == int(self.pcount):
            print "len(photos list) (%s) != stored photo count (%s)" % (len(self.photos), self.pcount)
            raise RuntimeError
        
        if self.primary not in self.photos:
            print "Primary photo not in photos list"
            return False
        
        return True
    
    def update(self):
        rsp = fapi.photosets_getInfo(api_key=FKey, photoset_id = self.id)
        if rsp.attrib['stat'] == "fail":
            # Print an error
            fapi.testFailure(rsp, exit=False)
            raise RuntimeError
        
        p = rsp.photoset[0]
        self.update_with_chunk(p)
        
    def update_with_chunk(self, p):
        """This method is needed since some flickr api calls return 
        this info as part of other calls. So we just reuse that info
        instead of making another remote api call."""
        self.id = p.attrib["id"]
        self.pcount = p.attrib["photos"]
        self.primary = p.attrib["primary"] 
        self.desc = p.find('description').text
        self.title = p.find('title').text
                
    def update_photo_list(self):
        rsp = fapi.photosets_getPhotos(api_key=FKey, user_id=FUser, photoset_id=self.id)
        if rsp.attrib['stat'] == "fail":
            # Print an error
            fapi.testFailure(rsp, exit=False)
            raise RuntimeError
        print dir(rsp[0])
        self.photos = [ p.attrib["id"] for p in rsp[0] ]
                        
def get_sets():
    """A utility function that gets the list of a user's photo sets 
    and their info from Flickr"""
    rsp = fapi.photosets_getList(api_key = FKey, user_id = FUser)
    if rsp.attrib['stat'] == "fail":
        # Print an error
        fapi.testFailure(rsp, exit=False)
        raise RuntimeError
    
    for x in rsp[0]:
        print x.attrib['id']
    sets_l = [] # Store just set ids to capture ordering at Flickr
    sets_d = {} # Store PhotoSet objects with setid as key
    
    for s in rsp[0]:
        set = s.attrib['id']
        sets_l.append(set)
        ps = PhotoSet(set_id = set, update = False)
        ps.update_with_chunk(s)
        ps.update_photo_list()
        sets_d[set] = ps
        
    return sets_l, sets_d

if __name__ == '__main__':
    
    user = User()
    print "User:", user
    
    set_ids, sets_d = get_sets()
    
    for s in sets_d.itervalues():
        # Not all terminals understand UTF-8
        # If yours does, feel free to delete the 
        # encode bit - just s.__str__() will suffice
        print s.__str__()
    
    photos_d = {} #cPickle.load(open(FlickrDBFile))[3]
    
    for s in sets_d.itervalues():
        s.is_consistent()
        
        for photo in s.photos:
            # A photo may belong to multiple sets!
            # Don't fetch multiple times!
            if photo not in photos_d:
                photos_d[photo] = Photo(photo)
                photos_d[photo].update_img_urls()
                # Not all terminals understand UTF-8
                # If yours does, feel free to delete the 
                # encode bit - just s.__str__() will suffice
                print photos_d[photo].__str__()
            else:
                print "Skipping", photo

        s.primary_imgurl = photos_d[s.primary].img_urls
                
    # POSIX rename is atomic
    # Good enough for me :-)                
    f = open(FlickrDBFile+'.tmp','w')
    cPickle.dump( (user, set_ids, sets_d, photos_d), f)
    f.close()
    os.rename(FlickrDBFile+'.tmp', FlickrDBFile)
