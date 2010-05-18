import web
# Make sure webr_update.py is called at least once to create the 
# dump of Flickr photoset data

FUser = "94046501@N00"
FlickrDBFile = "flickrdb.pickle.dump"
SiteRoot = '/'
MediaRoot = '/templates/'
GalleryName = 'My Flickr Photosets'

web.webapi.internalerror = web.debugerror
middleware = [web.reloader]
cache = False
