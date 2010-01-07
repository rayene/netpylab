import time
from math import log, cos, sin, radians, degrees, atan2, tan, pi, sqrt
from xml.dom import minidom
import bisect

pow2_25 = 2**25

class Point(object):
    def __init__(self, lat=None,lon=None, x = None, y = None, time = 0.0, speed = 0.0, direction = 0.0):
        """docstring for __init__"""
        self.time = time
        self.speed = speed
        self.direction = direction
        if lat is not None and lon is not None:
            self.lat, self.lon = lat, lon
            self.xo, self.yo = self.osm2map()
            self.x ,self.y = self.geo2map()
        elif x and y:
            self.x, self.y  = x, y

    def osm2map(self):
        x = (self.lon + 180.0) / 360.0
        y = (1 - log(tan(radians(self.lat)) + 1/cos(radians(self.lat))) / pi) / 2
        return(x, y)

    def geo2map(self):
            return (2*self.xo-1)*pow2_25, -(2*self.yo-1)*pow2_25

    def get_distance(self, other):
        radius = 6371000 
        deltaLat = other.lat-self.lat
        deltaLong = other.lon-self.lon
        a = (sin(radians(deltaLat)/2))**2
        b = cos(radians(other.lat))*cos(radians(self.lat))*(sin(radians(deltaLong)/2))**2
        c = 2*atan2(sqrt(a+b), sqrt(1-a-b))
        distance = radius * c
        return distance        

    def get_direction(self, other):
        deltaLong = other.lon - self.lon
        a = sin(radians(deltaLong))*cos(radians(self.lat))
        b = cos(radians(other.lat))*sin(radians(self.lat))
        c = sin(radians(other.lat))*cos(radians(self.lat))*cos(radians(deltaLong))
        direction = degrees(atan2(a, b-c))
        return direction #maybe a sign problem ????

    def get_speed(self, other):
        delta_t = other.time - self.time
        if delta_t ==0:
            return 0
        else:
            return (self.get_distance(other)*3600.0)/(delta_t*1000.0)

        
class Path(list):
    """docstring for Path Abstract Class"""
    def __init__(self):
        list.__init__(self)
        self.start_time = None
        self.times = []

    def append(self, point):
        if self.start_time is None:
            self.start_time = point.time
        else:
            point.time = (point.time - self.start_time)
            prev = self[-1]
            prev.dist = point.get_distance(prev)
            prev.speed = prev.get_speed(point)
            #TODO: distance is calculated twice
            prev.direction = prev.get_direction(point)
        list.append(self, point)
        self.times.append(point.time)

    def position(self, time):
        if len(self)==1:
            return self[0]
        i = bisect.bisect(self.times, time)
        if i == 0:
            return self[0]
        elif i == len(self.times):
            return self[-1]
        orig, dst = self[i-1], self[i]
        percentage = (time-orig.time)/(dst.time-orig.time)
        lat = orig.lat + (dst.lat - orig.lat) * percentage
        lon = orig.lon + (dst.lon - orig.lon) * percentage
        return Point(lat, lon, speed = orig.speed, time =time)

class PointPath(Path):
    def __init__(self, lat, lon):
        Path.__init__(self)
        self.append(Point(lat, lon))

class StraigthPath(Path):
    """docstring for StraigthPath"""
    def __init__(self, lat1, lon1, lat2, lon2, speed):
        Path.__init__(self)
        self.append(Point(lat1, lon1, speed = speed))
        self.append(Point(lat2, lon2))

class CircularPath(Path):
    """docstring for CircularPath"""
    def __init__(self, center, radius):
        Path.__init__(self)
        self.center = center
        self.radius = radius #meters

    def position(self):
        """docstring for position"""
        lon = 0.0
        lat = 0.0
        return (lon,lat)
        

class GpxPath(Path):
    """docstring for GpxPath"""
    def __init__(self, gpx_file, track_id = 0):
        Path.__init__(self)
        doc = minidom.parse(gpx_file)
        doc.normalize()
        gpx = doc.documentElement
        tracks = gpx.getElementsByTagName('trk')
        if type(track_id) == int :
            self.parse_track(tracks[track_id])
        else:
            ok = False
            for trk in tracks :
                l = trk.getElementsByTagName('name')
                if len(l)>0 and l[0].firstChild.data == track_id:
                    ok = True
                    self.parse_track(trk)
            if not ok:
                raise(RuntimeError('track %s not found in file %s' % (track_id, gpx_file)))
        
    def parse_track(self, trk):
        for trkseg in trk.getElementsByTagName('trkseg'):
            for trkpt in trkseg.getElementsByTagName('trkpt'):
                lat = float(trkpt.getAttribute('lat'))
                lon = float(trkpt.getAttribute('lon'))
                time_rfc3339 = trkpt.getElementsByTagName('time')[0].firstChild.data
                try:
                    t = time.mktime(time.strptime(time_rfc3339, "%Y-%m-%dT%H:%M:%SZ"))
                except:
                    t = time.mktime(time.strptime(time_rfc3339, "%Y-%m-%dT%H:%M:%S"))
                self.append(Point(lat, lon, time = t))
