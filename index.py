#
# webr.py: A virtual photo gallery software. It lets you showcase your flickr photosets 
#          in a photo gallery on your domain, styled to your tastes.
#      
# author:   Deepak Sarda
#           firstname@antrix.net
# requires: web.py (http://webpy.org)
#           Cheetah template (http://www.cheetahtemplate.org/)
#           flup (for web.py)
# Changelog: http://antrix.net/stuff/webr/Changelog

__author__      = 'Deepak Sarda'
__version__     = '0.3'
__copyright__   = '(c) 2006 Deepak Sarda'
__license__     = 'GPL'
__url__         = 'http://www.antrix.net/stuff/webr/'

import sys, os
abspath = os.path.dirname(__file__)
sys.path.append(abspath)
os.chdir(abspath)

import cPickle
import web

import config

from webr_update import User, Photo, PhotoSet

render = web.template.render('templates/')

class Data:
    pass
# G is the global data struct used everywhere in webr.py!
G = Data()
G.user, G.sets_l, G.sets_d, G.photos_d = cPickle.load(open(config.FlickrDBFile))
G.root = config.SiteRoot
G.media = config.MediaRoot
G.name = config.GalleryName

#### Helper functions ####
import mimetypes
def mime_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def getSets(p_id):
    """Return a list of set ids in which photo with id: p_id, exists"""
    p_id = str(p_id) # To be sure!
    sets = [s for s in G.sets_l if p_id in G.sets_d[s].photos]
    return sets 
#end getSets

def getSiblings(p_id, s_id):
    """Return next and previous photo ids for p_id in set 's_id'
    Careful! Doesn't check if p_id exists in s_id.
    """
    # This function will fail if set contains just one photo ;-)
    s = G.sets_d[str(s_id)]
    i = s.photos.index(str(p_id))
    
    if i == 0:
        return None, s.photos[1]
    elif i == len(s.photos) - 1:
        return s.photos[-2], None
    else:
        return s.photos[i-1], s.photos[i+1]
#end getSiblings

#### CONTROLLERS ####

class IndexC:
    def GET(self):
        # We want the sets in the same order they are sorted on Flickr
        sets = [ G.sets_d[s] for s in G.sets_l ]
        return render.index(sets,G)
#end IndexC

class SetC:
    def GET(self, set_id):
        if str(set_id) not in G.sets_d:
            return web.notfound()
        
        photoset = G.sets_d[str(set_id)]
        primary = G.photos_d[photoset.primary]
        photos = [G.photos_d[p] for p in photoset.photos]
        return render.set(photoset,primary,photos,G)
#end SetC
    
class PhotoC:
    def GET(self, p_id, set_id = ''):
        # Wish web.py's urlmapper did this for me!
        p_id = str(p_id)
        set_id = str(set_id)
        
        if p_id not in G.photos_d:
            return web.notfound()
        
        if not set_id:
            this_set = None
        elif set_id not in G.sets_d:
            return web.redirect('/%s/' % p_id)
        else: 
            this_set = G.sets_d[set_id]
            
        if this_set:
            prev, next = getSiblings(p_id, this_set.id)
            if prev: prev = G.photos_d[prev]
            if next: next = G.photos_d[next]
        else:
            prev, next = None, None

        photo = G.photos_d[p_id]
        if not photo.title:
            photo.title = 'Untitled'
        
        other_sets = getSets(p_id)
        other_sets = [ G.sets_d[s] for s in other_sets if s != set_id]
        
        return render.photo(photo,this_set,other_sets,prev,next,G)
#end PhotoC

class StaticServerC:
    def GET(self, static_dir):
        try:
            static_file_name = web.ctx.path.split('/')[-1]
            web.header('Content-type', mime_type(static_file_name))
            static_file = open('.' + web.ctx.path, 'rb').read()
            web.ctx.output = static_file
        except IOError:
            web.notfound()

#### END CONTROLLERS #### 
        
urls = (
    '/(templates)/.*', 'StaticServerC',
    '/set/(\d+)/?', 'SetC',
    '/(\d+)/in/set-(\d+)/?', 'PhotoC',
    '/(\d+)/?', 'PhotoC',
    '/?', 'IndexC',
)

app = web.application(urls, globals(), autoreload=False)
application = app.wsgifunc()
