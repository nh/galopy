import flickrapi, web, time, re, os
import elementtree.ElementTree as ET

db = "gal.db"
Fkey = "04133797314d6ff600f07314fe061643"
Fsecret = "b9f548992d4c62b0"
Static = "./static/"
Theme = "default"

f = flickrapi.FlickrAPI(Fkey, Fsecret)
db = web.database(dbn='sqlite',db='gal.db')
render = web.template.render('themes/'+Theme+'/')
progress = 0
ChangedSet = 0
Fuser = db.select("conf",where="name='nsid'")[0].val

def dropsets():
    for set in db.select("sets"):
        if os.path.exists(Static+set.slug):
            os.remove(Static+set.slug+"/index.html")
            os.rmdir(Static+set.slug)
    db.query("DELETE FROM imgs")
    db.query("DELETE FROM sets")
    db.query("DELETE FROM keys")

def updateimgs(sets):
    global progress
    open(Static+"index.html","w").write("aaaaaaaaaaaa")
    for set in sets:
        if set.visible == 2:
            db.update("sets",where="id="+str(set.id),visible=0)
            db.delete("keys",where="set_id="+str(set.id))
            os.remove(Static+set.slug+"/index.html")
            os.rmdir(Static+set.slug)
            continue
        dirty = False
        setimgs = dict([(x.attrib["id"],x) for x in f.photosets_GetPhotos(api_key = Fkey, photoset_id = set.id,extras="last_update,url_sq,url_m")[0]])
        DBsetimgs = dict([(str(x.img_id),x.lastupdate) for x in db.query("SELECT * FROM imgs INNER JOIN keys ON imgs.id = keys.img_id AND keys.set_id = "+str(set.id))])
        for imgid, setimg in setimgs.iteritems():
            if imgid not in DBsetimgs:
                dirty = True
                db.query("INSERT OR IGNORE INTO imgs (id,title,lastupdate,url_sq,url_m) VALUES ($id,$title,$lastupdate,$url_sq,$url_m)", vars=setimg.attrib)
                db.insert("keys",img_id=setimg.attrib["id"],set_id=set.id)
            elif int(setimg.attrib["lastupdate"]) > DBsetimgs[setimg.attrib["id"]]:
                dirty = True
                db.query("REPLACE INTO imgs (id,title,lastupdate,url_sq,url_m) VALUES ($id,$title,$lastupdate,$url_sq,$url_m)", vars=setimg.attrib)
        for dead in [i for i in DBsetimgs.keys() if i not in setimgs]:
            dirty = True
            db.delete("keys",where="img_id="+dead)
        if dirty == True:
            os.makedirs(Static+set.slug)
            open(Static+set.slug+"/index.html","w").write(str(render.setimgs(set,db.query("SELECT * FROM imgs INNER JOIN keys ON imgs.id = keys.img_id AND keys.set_id = "+str(set.id)))))
    #db.query("DELETE FROM imgs WHERE (SELECT COUNT(*) FROM keys WHERE img_id=imgs.id)=0")
    db.delete('imgs', where="id NOT IN (SELECT img_id FROM keys)")
    db.query("UPDATE sets SET dbcount = (SELECT COUNT(*) FROM keys WHERE set_id=sets.id)")
    progress = 0

def updatesetlist():
    sets = f.photosets_GetList(api_key = Fkey, user_id = Fuser)[0]
    dbsets = [str(x["id"]) for x in db.select("sets",what="id")]
    for newset in [item for item in sets if item.attrib["id"] not in dbsets]:
        db.insert(
            "sets",
            id=newset.attrib["id"],
            pcount=newset.attrib["photos"],
            dbcount = 0,
            pri=newset.attrib["primary"],
            thumb="http://farm%s.static.flickr.com/%s/%s_%s_s.jpg" % (newset.attrib["farm"],newset.attrib["server"],newset.attrib["primary"],newset.attrib["secret"]),  
            title=newset[0].text,
            formattedtitle=re.sub("([^ ][./_]|[^\- ./]{13})([^ ])",r"\1<wbr>\2",web.websafe(newset[0].text)),
            slug=re.sub('\s+', '-', re.sub('[^\w\s-]', '', newset[0].text).strip().lower()),
            desc=newset[1].text
        )
        print 'Added set %s' % (newset[0].text)
    for deadset in [item for item in dbsets if item not in [y.attrib["id"] for y in sets]]:
        db.delete("sets",where="id="+deadset)
        print 'Deleted set %s' % (deadset)

class Admin:
    def GET(self):
        global ChangedSet
        global Static
        sets = list(db.select("sets"))
        for s in sets:
            if s.id == ChangedSet:
                s.changed = True
            else:
                s.changed = False
            s.updatecount = format(s.pcount - s.dbcount,'+').replace("+0","")
        ChangedSet = 0
        return web.template.frender('admin.html')(dict([(conf.name,conf.val) for conf in db.select("conf")],imgs=db.query("SELECT COUNT(DISTINCT img_id) AS c FROM keys")[0].c),sets)

class Update:
    def POST(self):
        global Fuser
        global ChangedSet
        i = web.input()
        if "update" in i:
            if re.match("Update Set List",i["update"]):
                updatesetlist()
            elif re.match("Update All Images",i["update"]):
                updateimgs(db.select("sets",where="visible != 0"))
            elif i["update"] == "Show Unused Sets":
                db.update("conf",where="name='visible'",val=1)
            elif i["update"] == "Hide Unused Sets":
                db.update("conf",where="name='visible'",val=0)
            elif i["update"] == "Kill All":
                dropsets()         
            else:
                updateimgs(db.select("sets",where="id="+i["update"]))
        elif "show" in i:
            db.update("sets",where="id=" + i["show"],visible=1)
            ChangedSet = int(i["show"])
        elif "hide" in i:
            db.update("sets",where="id=" + i["hide"],visible=2)
            ChangedSet = int(i["hide"])
        elif "user" in i:
            if 'username' not in db.select("conf") or db.select("conf",where="name='username'")[0].val != i.user.lower():
                dropsets()         
                user = f.people_GetInfo(api_key = Fkey,user_id = f.people_FindByUsername(api_key = Fkey,username = i["username"])[0].attrib["nsid"])[0]
                u = dict([(i.tag,i.text) for i in user.getchildren()])
                db.query("delete FROM conf")
                db.insert("conf",name="visible",val=1)
                db.insert("conf",name="nsid",val=user.attrib["nsid"])
                db.insert("conf",name="username",val=user.find("username").text)
                db.insert("conf",name="buddyicon",val="http://farm%s.static.flickr.com/%s/buddyicons/%s.jpg" % (user.attrib["iconfarm"],user.attrib["iconserver"],user.attrib["nsid"]))  
                db.insert("conf",name="photosurl",val=user.find("photosurl").text)
                db.insert("conf",name="profileurl",val=user.find("profileurl").text)
                Fuser = db.select("conf",where="name='nsid'")[0].val
        raise web.seeother('/')

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

urls = (
    "/update","Update",
    "/a.js","adminjs",
    "/a.css","admincss",
    "/","Admin",
)

app = web.application(urls, globals())
#application = web.application(urls, globals()).wsgifunc()
if __name__ == "__main__":
    app.run()
