import flickrapi
import web

Fuser = "25721820@N00"
db = "gal.db"

Fkey = "04133797314d6ff600f07314fe061643"
Fsecret = "b9f548992d4c62b0"

f = flickrapi.FlickrAPI(Fkey, Fsecret)

db = web.database(dbn='sqlite',db='gal.db')

photos = f.people_GetPublicPhotos(api_key = Fkey, user_id = Fuser, per_page=500)

for p in photos[0]:
    print p.attrib['id']
print photos[0].attrib['total']

L1 = (0,1,2,3,4,5,6,7)
L2 = (0,1,2,3,44,5,6,7)

L2 = dict([(k,None) for k in L2])
print [item for item in L1 if item not in L2]
print [item for item in L2 if item not in L1]
