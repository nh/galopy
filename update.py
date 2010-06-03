import flickrapi
import web

Fuser = "54827292@N00" #me
Fuser = "25721820@N00" #joz

db = "gal.db"

Fkey = "04133797314d6ff600f07314fe061643"
Fsecret = "b9f548992d4c62b0"

f = flickrapi.FlickrAPI(Fkey, Fsecret)

db = web.database(dbn='sqlite',db='gal.db')
render = web.template.render('templates/')

class showSetlist:
    def GET(self):
        return render.sets(list(db.select("sets")))

class updateSetlist:
    def GET(self):
        sets = f.photosets_GetList(api_key = Fkey, user_id = Fuser)[0]
        dbsets = [str(x["id"]) for x in db.select("sets",what="id")]
        for newset in [item for item in sets if item.attrib["id"] not in dbsets]:
            db.insert("sets",id=newset.attrib["id"],pcount=newset.attrib["photos"],pri=newset.attrib["primary"],thumb=f.photos_getSizes(api_key = Fkey,photo_id = newset.attrib["primary"])[0][0].attrib["source"],title=newset[0].text,desc=newset[1].text)
            print 'Added set %s' % (newset[0].text)
        for deadset in [item for item in dbsets if item not in [y.attrib["id"] for y in sets]]:
            db.delete("sets",where="id="+deadset)
            print 'Deleted set %s' % (deadset)

        setlist = list(db.select("sets"))
        return render.sets(setlist)

def setUpdater(setid):
    imgs = f.photosets_GetPhotos(api_key = Fkey, photoset_id = setid,extras="last_update")[0]
    dbimgsids = [str(x.id) for x in db.query("SELECT imgs.id FROM imgs INNER JOIN keys ON imgs.id = keys.img_id AND keys.set_id = "+setid)]

    for newimg in [item for item in imgs if item.attrib["id"] not in dbimgsids]:
        sizes = f.photos_getSizes(api_key = Fkey,photo_id = newimg.attrib["id"])[0]
        square = sizes[0].attrib["source"]
        medium = sizes[2].attrib["source"]
        db.insert("keys",img_id=newimg.attrib["id"],set_id=setid)
        db.insert("imgs",id=newimg.attrib["id"],title=newimg.attrib["title"],last_update=newimg.attrib["lastupdate"],square=square,medium=medium)

    for changedimg in [x for x in imgs if int(x.attrib["lastupdate"]) > db.select("imgs",what="last_update",where="id="+x.attrib["id"])[0].last_update]:
        db.update("imgs",where="id="+changedimg.attrib["id"],title=changedimg.attrib["title"],last_update=changedimg.attrib["lastupdate"])
        print "update %s" % changedimg.attrib["title"]

    for deadimg in [item for item in dbimgsids if item not in [y.attrib["id"] for y in imgs]]:
        db.delete("keys",where="img_id="+deadimg)
        db.delete("imgs",where="id="+deadimg)
        print 'Deleted image %s' % (deadimg)

class showSet:
    def GET(self,id):
        set = db.select("sets",where="id = "+id)[0]
        imglist = list(db.query("SELECT * FROM imgs INNER JOIN keys ON imgs.id = keys.img_id AND keys.set_id = "+id))
        return render.setimgs(set,imglist)

class updateSet:
    def GET(self,id):
        setUpdater(id)
        set = db.select("sets",where="id = "+id)[0]
        imglist = list(db.query("SELECT * FROM imgs INNER JOIN keys ON imgs.id = keys.img_id AND keys.set_id = "+id))
        return render.setimgs(set,imglist)

"""
photos = f.people_GetPublicPhotos(api_key = Fkey, user_id = Fuser, per_page=500, extras="date_upload, date_taken, owner_name, icon_server, original_format, last_update, geo, tags, machine_tags, o_dims, views, media, path_alias, url_sq, url_t, url_s, url_m, url_o")
for p in photos[0]:
    for a in p.attrib:
        print a + " -- " + p.attrib[a]
    print "------------------------"
print photos[0].attrib['total']
"""

urls = (
    "/sets/update","updateSetlist",
    "/sets", "showSetlist",
    "/sets/update/(.*)","updateSet",
    "/sets/(.*)","showSet",
)

L1 = (0,1,2,3,4,5,6,7)
L2 = (0,1,2,3,44,5,6,7)

print [item for item in L1 if item not in L2]
print [item for item in L2 if item not in L1]

app = web.application(urls, globals())
if __name__ == "__main__": app.run()
