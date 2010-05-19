import web
import sys
# Make sure webr_update.py is called at least once to create the 
# dump of Flickr photoset data

FUser = "47608356@N06"
FlickrDBFile = "flickrdb.pickle.dump"
SiteRoot = '/'
MediaRoot = '/templates/'
GalleryName = 'James Elliott Images'

web.webapi.internalerror = web.debugerror
cache = False
