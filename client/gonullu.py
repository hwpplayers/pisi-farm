import urllib2
import os
import json
import requests, sys, glob, time


class Docker:
    def __init__(self):
        self.started = self.start()
        self.image = ""
        self.id = None
        self.volumes = {}

    def setImageName(self, newName):
        self.image = newName

    def check(self):
        cmd = "docker ps >/dev/null"
        status = os.system(cmd)
        return status

    def volume(self, local, indocker):
        self.volumes[indocker] = local

    def start(self):
        if self.check() != 0:
            print "Starting docker"
            cmd1 = "sudo cgroupfs-mount"
            cmd2 = "docker -d &"
            print "Mounting cgroupfs"
            os.system(cmd1)
            print "Starting docker daemon"
            os.system(cmd2)
        else:
            print "Docker already started"

class Farm:
    def __init__(self, farm_url):
        self.url = farm_url
        self.params = self.parametre()

    def get(self, cmd):
        return urllib2.urlopen("%s/%s" % (self.url, cmd)).read()

    def kuyruktanPaketAl(self):
        cmd = "requestPkg"
        return self.get(cmd)

    def parametre(self):
        bilgi = self.get("parameter")
        return json.loads(bilgi)

    def dosya_gonder(self, fname):
        cmd = "upload"
        f = {'file' : open(fname, 'rb') }
        r = requests.post("%s/%s" % (self.url, cmd) , files = f)
        hash = os.popen("sha1sum %s" % fname, "r").readlines()[0].split()[0].strip()
        if hash == r.text.strip():
            return True
        else:
            return False

    def dosyalari_gonder(self, liste):
        # FIXME:  derleme islemi sonucunda olusan log ve pisi
        # dosyalari burada gonderilecek
        for f in liste:
            print "dosya gonderiliyor, ", f
            if self.dosya_gonder(f) == True:
                print f, " gonderildi"
        print liste

class Gonullu:
    def __init__(self, farm, dock):
        self.farm = farm
        self.paket = None
        self.dockerImageName = self.farm.params['docker-image']
        self.docker = dock
        self.volumes = {'/var/cache/pisi/packages': '/var/cache/pisi/packages',
                        '/var/cache/pisi/archives': '/var/cache/pisi/archives',
                        '/derle':'/tmp/derle'}

        self.derle()
        self.gonder()

    def paketAl(self):
        self.paket = self.farm.kuyruktanPaketAl()
        self.volumes['/root'] = '/tmp/%s' % ( self.paket)

    def volumes_str(self):
        temp = ""
        for ind, local in self.volumes.items():
            temp += " -v %s:%s " % (local, ind)
        return temp

    def calisma_kontrol(self):
        cmd = "ls /tmp/%s/%s.bitti" % (self.paket, self.paket)
        status = os.system(cmd)
        return status

    def derle(self):
        pkg = self.paketAl()
        cmd = "docker run -id %s %s /derle/derle.sh %s" % (self.volumes_str(), self.dockerImageName, self.paket)
        status = os.system(cmd)
        calisiyor = True
        while calisiyor == True:
            time.sleep(60)
            calisma =  self.calisma_kontrol()
            if calisma == 0:
                calisiyor = False
                print "calisma bitmis"
                return 
            print "hala calisiyor"

    def gonder(self):
        liste = glob.glob("/tmp/%s/*.[lpe]*" % self.paket)
        print liste
        self.farm.dosyalari_gonder(liste)

d = Docker()
f = Farm("http://manap.se:5000")
g = Gonullu(f,d)

"""
docker run -itd 
-v /home/packages:/var/cache/pisi/packages 
-v /home/archives:/var/cache/pisi/archives 
-v /home/ertugrul/Works/manap_se/build:/root 
-v /home/ertugrul/Works/PisiLinux:/git 
ertugerata/pisi-chroot-farm bash 
"""