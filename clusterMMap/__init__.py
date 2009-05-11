# $Id: __init__.py,v 1.5 2009/04/24 05:59:56 asc Exp $

from cluster import KMeansClustering
from shapely.geometry import *
import types
import math

class clusterMMap :

        def __init__ (self) :
                pass
        
        #
        # public
        #
        
        def clusters(self, points, k=None) :

                if not k :
                        k = int(math.sqrt(len(points)))

                # print "CLUSTERS %s points, %s k" % (len(points), k)
                
                (hulls, hpoints, orphans) = self.mk_clusterhull(points, k)

                polys = self.hulls2polys(hulls)
                
                (sorted, abandoned) = self.visit_family_services(polys, points, orphans)

                return (sorted, abandoned)


        ###############################################################

        def paginate (self, clusters, points, items, lookup) :

                bucket = []
                
                count = len(clusters)
                
                for i in range(0, count) :
                        poly = clusters[i]
                        center = poly.centroid
                        bounds = poly.bounds

                        bucket.append({
                                'poly':poly,
                                'markers':[],
                                })
                
                pages = {}
        
                for p in points  :
                        pt = Point(p)

                        for i in range(0, count) :
                                if not pages.has_key(i) :
                                        pages[i] = []
                                
                                poly = clusters[i]

                                if poly.contains(pt) :
                                        pages[i].append(p)
                                        break

                                elif poly.touches(pt) :
                                        pages[i].append(p)
                                        break
                                else :
                                        pass

                # sudo make me a list of markers

                for p in pages.keys() :

                        for pt in pages[p] :
                
                                key = "%s,%s" % (pt)

                                if not lookup.has_key(key) :
                                        continue
                                
                                id = lookup[key]

                                item = items[id]

                                bucket[p]['markers'].append(item)

                return bucket
                
        ###############################################################

        #
        # "private"
        #
        
        def mk_clusterhull (self, points, k) :

                hpolys = []
                hpoints = []
                orphans = []
                
                clusters = self.mk_clusters(points, k, [])

                for c in clusters :
                        
                        count = len(c)
                        hull = []

                        if count == 1:
                                # print "failed cluster (of one)"
                                orphans.extend(c)
                                continue
                        
                        try:
                                ch = self.convexHull(c)
                        except Exception, e:
                                print "failed hull %s, %s" % (c, e)
                                orphans.extend(c)
                                continue
                        
                        if len(ch) == 2:
                                # print "failed hull (too small)"
                                orphans.extend(c)
                                continue
                        
                        for pt in ch :
                                hpoints.append(pt)
                                hull.append(pt)

                        hpolys.append(hull)

                return (hpolys, hpoints, orphans)

        ###############################################################

        def mk_clusters (self, points, k, clusters) :

                cl = KMeansClustering(points, None)
                res = cl.getclusters(k)

                for c in res :
                        count = len(c)

                        if count <= 2 :
                                clusters.append(c)
                        elif count <= 9 :
                                
                                if type(c) == types.ListType :
                                        tmp = self.mk_clusters(c, 2, [])
                                        
                                        if len(tmp) > 1 :
                                                p1 = Point(tmp[0])
                                                p2 = Point(tmp[1])
                                                d = p1.centroid.distance(p2.centroid)
                                                
                                                if d >= 0.025 :
                                                        for c in tmp :
                                                                clusters.append(c)
                                                        continue
                                clusters.append(c)
                        else :
                                clusters = self.mk_clusters(c, 2, clusters)
                
                return clusters

        ###############################################################
        
        def visit_family_services(self, sorted, points, orphans) :

                resorted = []
                abandoned = []
                
                seen = {}
                
                c = len(sorted)

                for i in range(0, c) :

                        for j in range(0, c) :

                                if i != j and not seen.has_key(i) :
                                        
                                        p1 = sorted[i]
                                        p2 = sorted[j]

                                        box1 = self.poly2box(p1)
                                        box2 = self.poly2box(p2)

                                        if not box1 or not box2 :
                                                continue
                                        
                                        if box1.contains(p2) :
                                                # print "BOX1 %s CONTAINS POLY2 %s" % (i, j)
                                                seen[i] = j
                                        elif box2.contains(p1) :
                                                # print "BOX2 %s CONTAINS POLY1 %s" % (j, i)
                                                seen[i] = j                                                
                                        elif box1.intersects(p2) :
                                                # print "BOX1 %s INTERSECTS POLY2 %s" % (i, j)
                                                seen[i] = j
                                        elif box2.intersects(p1) :
                                                # print "BOX2 %s INTERSECTS POLY1 %s" % (j, i)
                                                seen[i] = j
                                        else :
                                                pass

                #

                skip = []
                
                for i in range(0, c) :

                        if i in skip :
                                pass
                        
                        elif seen.has_key(i) :
                                j = seen[i]
                                skip.append(j)
                                
                                p1 = list(sorted[i].exterior.coords)
                                p2 = list(sorted[j].exterior.coords)
                                p1.extend(p2)
                                
                                bucket = []

                                try :
                                        for pt in self.convexHull(p1) :
                                                bucket.append(pt)

                                        p = Polygon(bucket)
                                        resorted.append(p)
                                                
                                except Exception, e:
                                        print e
                                        resorted.append(sorted[i])
                                                                        
                        else :
                                resorted.append(sorted[i])

                #

                c = len(resorted)
                
                for o in orphans :

                        pt = Point(o)
                        contained = 0
                        
                        for i in range(0, c) :

                                poly = resorted[i]
                                box = self.poly2box(poly)
                                
                                if not box :
                                        continue
                                
                                if box.contains(pt):
                                        tmp = list(poly.exterior.coords)
                                        tmp.extend((o,))

                                        bucket = []

                                        for pt in self.convexHull(tmp) :
                                                bucket.append(pt)
                                                
                                        resorted[i] = Polygon(bucket)
                                        contained = 1

                                        break

                        if not contained :
                               abandoned.append(o)
                               
                return (resorted, abandoned)

        ###############################################################
        
        def hulls2polys (self, hulls) :

                polys = []
                
                for h in hulls :
                        
                        bucket = []
        
                        for pt in h :
                                bucket.append(pt)

                        p = Polygon(bucket)
                        polys.append(p)
                        
                return polys

        ###############################################################
        
        def poly2box (self, poly) :

                try :
                        b = poly.bounds
                        box = Polygon([(b[0],b[1]), (b[0],b[3]), (b[2],b[3]), (b[2], b[1])])
                except Exception, e:
                        print "poly2box failed for %s" % e
                        return
                
                return box

        ###############################################################

        #
        # convex hull stuff
        #
        # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66527
        # Dinu C. Gherman
        #
        
        def _myDet (self, p, q, r):
                """Calc. determinant of a special matrix with three 2D points.

                The sign, "-" or "+", determines the side, right or left,
                respectivly, on which the point r lies, when measured against
                a directed vector from p to q.
                """

                # We use Sarrus' Rule to calculate the determinant.
                # (could also use the Numeric package...)
                sum1 = q[0]*r[1] + p[0]*q[1] + r[0]*p[1]
                sum2 = q[0]*p[1] + r[0]*q[1] + p[0]*r[1]

                return sum1 - sum2


        def _isRightTurn (self, (p, q, r)):
                "Do the vectors pq:qr form a right turn, or not?"

                # assert p != q and q != r and p != r
            
                if self._myDet(p, q, r) < 0:
                        return 1
                else:
                        return 0

        def _isPointInPolygon (self, r, P):
                "Is point r inside a given polygon P?"

                # We assume the polygon is a list of points, listed clockwise!
                for i in xrange(len(P[:-1])):
                        p, q = P[i], P[i+1]
                        if not self._isRightTurn((p, q, r)):
                                return 0 # Out!        

                return 1 # It's within!


        def _makeRandomData (self, numPoints=10, sqrLength=100, addCornerPoints=0):
                "Generate a list of random points within a square."
    
                # Fill a square with random points.
                min, max = 0, sqrLength
                P = []
                for i in xrange(numPoints):
                        rand = random.randint
                        x = rand(min+1, max-1)
                        y = rand(min+1, max-1)
                        P.append((x, y))

                # Add some "outmost" corner points.
                if self.addCornerPoints != 0:
                        P = P + [(min, min), (max, max), (min, max), (max, min)]

                return P

        def convexHull (self, P):
                "Calculate the convex hull of a set of points."

                # Get a local list copy of the points and sort them lexically.
                points = map(None, P)
                points.sort()

                # Build upper half of the hull.
                upper = [points[0], points[1]]
                for p in points[2:]:
                        upper.append(p)
                        while len(upper) > 2 and not self._isRightTurn(upper[-3:]):
                                del upper[-2]

                # Build lower half of the hull.
                points.reverse()
                lower = [points[0], points[1]]
                for p in points[2:]:
                        lower.append(p)
                        while len(lower) > 2 and not self._isRightTurn(lower[-3:]):
                                del lower[-2]
                                
                # Remove duplicates.
                del lower[0]
                del lower[-1]

                # Concatenate both halfs and return.
                return tuple(upper + lower)
        
