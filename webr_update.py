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

import sys, os, cPickle
import flickrapi

# Remember to change FUser to your Flickr userid!
from config import FUser, FlickrDBFile

# The rest can be left as is.
FKey = "9baf1fe6daf86b0602b1ca31f7a83688"
FSecret = "2964866d87b3b8c5"

fapi = flickrapi.FlickrAPI(FKey, FSecret)

# All responses from flickrapi are python unicode strings.
# So ideally we should be explicitly encoding them back
# to 'utf-8' before printing. (Flickr saves as utf-8)

class User:
    """This class is used to store user specific info like name, userid, etc."""
    def __init__(self):
        rsp = fapi.people_getInfo(api_key = FKey, user_id = FUser)
        if rsp['stat'] == "fail":
            # Print an error
            fapi.testFailure(rsp, exit=False)
            raise RuntimeError
        
        rsp = rsp.person[0]
        
        self._id = FUser
        self._username = rsp.username[0].elementText
        self._realname = rsp.realname[0].elementText
        self._photos_url = rsp.photosurl[0].elementText
        self._profile_url = rsp.profileurl[0].elementText
        self._location = rsp.location[0].elementText
        
    def __str__(self): return self._realname
        
class Photo:
    """All Photo specific stuff goes in here."""
    def __init__(self, photo_id, update = True):
        self._img_urls = {}
        self._id = str(photo_id)
        if update: self.update()
        
    def __str__(self): return u"%s: %s" % (self._id, self._title)
        
    def update(self):
        rsp = fapi.photos_getInfo(api_key = FKey, photo_id = self._id)
        if rsp['stat'] == "fail":
            # Print an error
            fapi.testFailure(rsp, exit=False)
            raise RuntimeError
        
        p = rsp.photo[0]
        self.update_with_chunk(p)
        
    def update_with_chunk(self, p):
        """This method is needed since some flickr api calls return 
        this info as part of other calls. So we just reuse that info
        instead of making another remote api call."""
        self._title = p.title[0].elementText
        self._desc = p.description[0].elementText
        self._taken = p.dates[0]["taken"]
        self._comment_count = p.comments[0].elementText
        self._flickr_url = p.urls[0].url[0].elementText
        
    def update_img_urls(self):
        """"""
        rsp = fapi.photos_getSizes(api_key=FKey, photo_id=self._id)
        if rsp['stat'] == "fail":
            # Print an error
            fapi.testFailure(rsp, exit=False)
            raise RuntimeError

        for s in rsp.sizes[0].size:
            self._img_urls[s['label']] = s['source']
            

class PhotoSet:
    def __init__(self, set_id, update = True):
        self._id = str(set_id)
        self._photos = []
        if update: self.update()
    
    def __str__(self):
        return u"Photoset # %s - %s. (%s photos)" % (self._id, self._title, self._pcount)
    
    def is_consistent(self):
        if not len(self._photos) == int(self._pcount):
            print "len(photos list) (%s) != stored photo count (%s)" % (len(self._photos), self._pcount)
            raise RuntimeError
        
        if self._primary not in self._photos:
            print "Primary photo not in photos list"
            return False
        
        return True
    
    def update(self):
        rsp = fapi.photosets_getInfo(api_key=FKey, photoset_id = self._id)
        if rsp['stat'] == "fail":
            # Print an error
            fapi.testFailure(rsp, exit=False)
            raise RuntimeError
        
        p = rsp.photoset[0]
        self.update_with_chunk(p)
        
    def update_with_chunk(self, p):
        """This method is needed since some flickr api calls return 
        this info as part of other calls. So we just reuse that info
        instead of making another remote api call."""
        self._id = p["id"]
        self._pcount = p["photos"]
        self._primary = p["primary"]
        self._desc = p.description[0].elementText
        self._title = p.title[0].elementText
        
    def update_photo_list(self):
        rsp = fapi.photosets_getPhotos(api_key=FKey, user_id=FUser, photoset_id=self._id)
        if rsp['stat'] == "fail":
            # Print an error
            fapi.testFailure(rsp, exit=False)
            raise RuntimeError
        
        self._photos = [ p["id"] for p in rsp.photoset[0].photo ]
                        
def get_sets():
    """A utility function that gets the list of a user's photo sets 
    and their info from Flickr"""
    rsp = fapi.photosets_getList(api_key = FKey, user_id = FUser)
    if rsp['stat'] == "fail":
        # Print an error
        fapi.testFailure(rsp, exit=False)
        raise RuntimeError
    
    sets_l = [] # Store just set ids to capture ordering at Flickr
    sets_d = {} # Store PhotoSet objects with setid as key
    
    for s in rsp.photosets[0].photoset:
        sets_l.append(s["id"])
        ps = PhotoSet(set_id = s["id"], update = False)
        ps.update_with_chunk(s)
        ps.update_photo_list()
        sets_d[s["id"]] = ps
        
    return sets_l, sets_d

if __name__ == '__main__':
    
    user = User()
    print "User:", user
    
    set_ids, sets_d = get_sets()
    
    for s in sets_d.itervalues():
        # Not all terminals understand UTF-8
        # If yours does, feel free to delete the 
        # encode bit - just s.__str__() will suffice
        print s.__str__().encode('ascii', 'replace')
    
    photos_d = {}
    
    for s in sets_d.itervalues():
        s.is_consistent()
        
        for photo in s._photos:
            # A photo may belong to multiple sets!
            # Don't fetch multiple times!
            if photo not in photos_d:
                photos_d[photo] = Photo(photo)
                photos_d[photo].update_img_urls()
                # Not all terminals understand UTF-8
                # If yours does, feel free to delete the 
                # encode bit - just s.__str__() will suffice
                print photos_d[photo].__str__().encode('ascii','replace')
            else:
                print "Skipping", photo
                
    # POSIX rename is atomic
    # Good enough for me :-)                
    f = open(FlickrDBFile+'.tmp','w')
    cPickle.dump( (user, set_ids, sets_d, photos_d), f)
    f.close()
    os.rename(FlickrDBFile+'.tmp', FlickrDBFile)
