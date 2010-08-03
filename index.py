import flickrapi
import web
import time
import elementtree.ElementTree as ET
Fuser = "54827292@N00" #me
Fuser = "25721820@N00" #joz

db = "gal.db"

Fkey = "04133797314d6ff600f07314fe061643"
Fsecret = "b9f548992d4c62b0"

f = flickrapi.FlickrAPI(Fkey, Fsecret)

db = web.database(dbn='sqlite',db='gal.db')
render = web.template.render('templates/')
progress = 0

def dropsets():
    db.query("DELETE FROM imgs")
    db.query("DELETE FROM sets")
    db.query("DELETE FROM keys")

class UpdateStatus:
    def __init__(self):
        self.progressbar = 0

class ViewUsedSets:
    def GET(self):
        return render.sets(db.select("user")[0],list(db.select("sets",where="visible=1")),len(list(db.select('imgs'))),False)
    #def POST(self):
        #?????????????????????????????????????? GET/POST SEPARATION NEEDS FIXIN!

class ViewAllSets:
    def GET(self):
        return render.sets(db.select("user")[0],list(db.select("sets")),len(list(db.select('imgs'))),True)

class Admin:
    def POST(self):
        i = web.input(update=[])
        if i.update == "updatesetlist":
            sets = f.photosets_GetList(api_key = Fkey, user_id = Fuser)[0]
            dbsets = [str(x["id"]) for x in db.select("sets",what="id")]
            for newset in [item for item in sets if item.attrib["id"] not in dbsets]:
                db.insert(
                    "sets",
                    id=newset.attrib["id"],
                    pcount=newset.attrib["photos"],
                    pri=newset.attrib["primary"],
                    thumb="http://farm%s.static.flickr.com/%s/%s_%s_s.jpg" % (newset.attrib["farm"],newset.attrib["server"],newset.attrib["primary"],newset.attrib["secret"]),  
                    title=newset[0].text,
                    desc=newset[1].text
                )
                print 'Added set %s' % (newset[0].text)
            for deadset in [item for item in dbsets if item not in [y.attrib["id"] for y in sets]]:
                db.delete("sets",where="id="+deadset)
                print 'Deleted set %s' % (deadset)
        if i.update == "showunused":
            db.insert("conf",where="name=visible",val=1)
        print i["update"]
        return render.sets(db.select("conf"),list(db.select("sets")),len(list(db.select('imgs'))),True)
    def GET(self):
        print "GET!!!!"
        return render.sets(list(db.select("conf")),list(db.select("sets")),len(list(db.select('imgs'))),True)


class DropSets:
    def GET(self):
        db.query("DELETE FROM imgs")
        db.query("DELETE FROM sets")
        db.query("DELETE FROM keys")
        return "dropped sets!"

class UpdateUser:
    def POST(self):
        i = web.input()
        if db.select("conf",where="name=username")[0].val != i.user.lower():
            dropsets()         
            user = f.people_GetInfo(api_key = Fkey,user_id = f.people_FindByUsername(api_key = Fkey,username = i.user)[0].attrib["nsid"])[0]
            u = dict([(i.tag,i.text) for i in user.getchildren()])
            db.query("delete FROM user")
            db.insert("conf",name="nsid",val=user.attrib["nsid"])
            db.insert("conf",name="username",val=user.attrib["username"].lower())
            db.insert("conf",name="photosurl",val=user.attrib["photosurl"])
            db.insert("conf",name="profileurl",val=user.attrib["profileurl"])

class UpdateImgs:
    def __init__(self,setids):
        global progress
        imgs = []
        for setid in setids:
            imgs.extend(list(f.photosets_GetPhotos(api_key = Fkey, photoset_id = setid,extras="last_update,url_sq,url_m")[0]))
        print setids
        progress = 0
        setsquery = "".join(["keys.set_id = %s OR " % k for k in setids]).rstrip(" OR ")
        dbimgsids = [str(x.id) for x in db.query("SELECT imgs.id FROM imgs INNER JOIN keys ON imgs.id = keys.img_id AND (" + setsquery + ")")]
        print dbimgsids
        for newimg in [item for item in imgs if item.attrib["id"] not in dbimgsids]: # All new images that are not already in this set
            #db.query("INSERT OR IGNORE INTO keys VALUES ("+newimg.attrib["id"]+","+setid+")")
            db.query("INSERT OR IGNORE INTO imgs (id,title,lastupdate,url_sq,url_m) VALUES ($id,$title,$lastupdate,$url_sq,$url_m)", vars=newimg.attrib) # Don't add image to full imglist if it already exists in another set...
            db.insert("keys",img_id=newimg.attrib["id"],set_id=setid) # ...but still add to this set's imglist
            #time.sleep(3)
            progress += 1   

        for changedimg in [x for x in imgs if int(x.attrib["lastupdate"]) > db.select("imgs",what="lastupdate",where="id="+x.attrib["id"])[0].lastupdate]:
            db.update("imgs",where="id="+changedimg.attrib["id"],title=changedimg.attrib["title"],lastupdate=changedimg.attrib["lastupdate"])
            print "update %s" % changedimg.attrib["title"]

        for deadimg in [item for item in dbimgsids if item not in [y.attrib["id"] for y in imgs]]:
            db.delete("keys",where="img_id="+deadimg)
            db.delete("imgs",where="id="+deadimg)
            print 'Deleted image %s' % (deadimg)
        progress = 0

class UpdateAll:
    def GET(self):
        UpdateImgs([str(x.id) for x in db.select("sets",where="visible=1")])
        raise web.seeother('/sets')

class ShowSet:
    def GET(self,setid):
        db.update("sets",where="id="+setid,visible=1)
        raise web.seeother('/sets/all')

class HideSet:
    def GET(self,setid):
        db.delete('keys', where="set_id="+setid)
        db.delete('imgs', where="id NOT IN (SELECT img_id FROM keys)")
        db.update("sets", where="id="+setid,visible=0)
        raise web.seeother('/sets')

class ViewSet:
    def GET(self,id):
        set = db.select("sets",where="id = "+id)[0]
        imglist = list(db.query("SELECT * FROM imgs INNER JOIN keys ON imgs.id = keys.img_id AND keys.set_id = "+id))
        return render.setimgs(set,imglist)

class UpdateSet:
    def GET(self,id):
        UpdateImgs([id])
        #set = db.select("sets",where="id = "+id)[0]
        #imglist = list(db.query("SELECT * FROM imgs INNER JOIN keys ON imgs.id = keys.img_id AND keys.set_id = "+id))
        raise web.seeother('/sets/'+id)

class UpdateStatus:
    def GET(self):
        global progress
        if progress == 0:
            return "Done"
        else:
            return progress

class admincss:
    def GET(self):
        web.header('Content-Type', 'text/css')
        return open('a.css','r').read()

class adminjs:
    def GET(self):
        web.header('Content-Type', 'text/javascript')
        return open('jquery.js','r').read() + open('a.js','r').read()

"""
photos = f.people_GetPublicPhotos(api_key = Fkey, user_id = Fuser, per_page=500, extras="date_upload, date_taken, owner_name, icon_server, original_format, last_update, geo, tags, machine_tags, o_dims, views, media, path_alias, url_sq, url_t, url_s, url_m, url_o")
for p in photos[0]:
    for a in p.attrib:
        print a + " -- " + p.attrib[a]
    print "------------------------"
print photos[0].attrib['total']
"""

urls = (
    "/admin","Admin",
    "/a.js","adminjs",
    "/a.css","admincss",
)
"""/status","UpdateStatus",
"/dropsets","DropSets",
"/updatesetlist","UpdateSetlist",
"/updateall","UpdateAll",
"/sets/all", "ViewAllSets",
"/sets", "ViewUsedSets",
"/update/(.*)","UpdateSet",
"/show/(.*)","ShowSet",
"/hide/(.*)","HideSet",
"/view/(.*)","ViewSet",
".*","UpdateUser","""

app = web.application(urls, globals())
#application = web.application(urls, globals()).wsgifunc()
if __name__ == "__main__":
    app.run()
