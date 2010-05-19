import web
import sys, os
abspath = os.path.dirname(__file__)

# Make sure webr_update.py is called at least once to create the 
# dump of Flickr photoset data

FUser = "47608356@N06"
FlickrDBFile = sys.path[0] + "/flickrdb.pickle.dump"
SiteRoot = '/'
MediaRoot = '/templates/'
GalleryName = 'James Elliott Images'

web.webapi.internalerror = web.debugerror
cache = False
