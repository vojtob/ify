import cv2
import numpy as np
# import docool.images.image_utils as image_utils

aligngap = 3

def addPointToSegments(lineSegments, keyCoordinate, lenCoordinate, reallySmallGap, minSegmentLength):
    """ add a point to segments """

    # try to add point into existing segments
    if(lineSegments.get(keyCoordinate)):
        # there is a segment with key coordinate equal to keyCoordinate
        segments = lineSegments[keyCoordinate]
        # the last segment
        s = segments.pop()
        # check how close is the point to the last segment
        if( (lenCoordinate-s[1]) <= reallySmallGap ):
            # the point is realy close to the last segment, we prolong this segment (poped element replaced with longer)
            segments.append((s[0],lenCoordinate))
        else:
            # the point is too far from previous segment

            # check, if the previous segment is long enough
            if( (s[1]-s[0]) > minSegmentLength ):
                # last segment is long enough, we should return it back to list (removed by pop)
                segments.append(s)

            # the point must be added into a new segment, only one point long
            lineSegments[keyCoordinate].append((lenCoordinate,lenCoordinate))
    else:
        # the very first segment for this key coordinate, create list of segments and a new segment       
        segments = []
        segments.append((lenCoordinate,lenCoordinate))
        lineSegments[keyCoordinate] = segments

def removeShortSegments(lineSegments, minSegmentLength):
    emptyList = []
    for keyCoordinate, segments in lineSegments.items():
        if (len(segments) == 0):
            print('!!!!!!!!!!!!', keyCoordinate)
        s = segments[-1]
        if( (s[1]-s[0]) < minSegmentLength ):
            segments.pop()
        if(len(segments) < 1):
            emptyList.append(keyCoordinate)
    for keyCoordinate in emptyList:
        lineSegments.pop(keyCoordinate)

def merge_similar_segments(line_segments, similar_length, really_small_gap):
    """if there are two almoust similar segments, remove shorter"""

    emptyList = []
    for y in sorted(line_segments.keys()):
        if(len(line_segments[y]) < 1):
            emptyList.append(y)

        for g in range(1, really_small_gap+1):
            if not line_segments.get(y+g):
                continue

            segments = line_segments[y]
            next_segments = line_segments[y+g]

            for i_s, s in enumerate(list(segments)):
                remove_elements = set()
                for i_n, n in enumerate(list(next_segments)):
                    if(((s[1]+similar_length) < n[0]) or ((n[1]+similar_length) < s[0])):
                        continue # segment do not overlap
                    # merge
                    segments.pop(i_s)
                    segments.insert(i_s, (min(s[0],n[0]),max(s[1],n[1])))
                    remove_elements.add(i_n)
                for i in sorted(remove_elements, reverse=True):
                    next_segments.pop(i)

    for y in emptyList:
        line_segments.pop(y)

def findLineSegments(img, reallySmallGap, minSegmentLength):
    """find line segments with minimal length"""

    # line segments are indexed by x or y coordinate and
    # for a particular x contain list of line segment
    # x : (y1,y2), (y3,y4)  - it means segments (x,y1, x,y2) and (x,y3, x,y4)
    lineSegmentsHorizontal = {}
    lineSegmentsVertical = {}

    # in this run we identify all line segments (even with length 1)
    # short segments could be only the last in list
    # opencv coordinate system is (row,col), therefore swith x-y
    maxY, maxX = img.shape[:2]
    for x in range(maxX):
        for y in range(maxY):
            # opencv coordinate system is (row,col), therefore swith x-y
            if(img[y,x]):
                # here is a point that should be added to segments
                addPointToSegments(lineSegmentsHorizontal, y, x, reallySmallGap, minSegmentLength)
                addPointToSegments(lineSegmentsVertical, x, y, reallySmallGap, minSegmentLength)
    # for y in range(maxY):
    #     for x in range(maxX):
    #         # opencv coordinate system is (row,col), therefore swith x-y
    #         if(img[y,x]):
    #             # here is a point that should be added to segments
    #             addPointToSegments(lineSegmentsHorizontal, y, x, reallySmallGap, minSegmentLength)

    # check segments for length
    removeShortSegments(lineSegmentsHorizontal, minSegmentLength)
    removeShortSegments(lineSegmentsVertical, minSegmentLength)
    merge_similar_segments(lineSegmentsHorizontal, reallySmallGap, reallySmallGap)
    merge_similar_segments(lineSegmentsVertical, reallySmallGap, reallySmallGap)

    return lineSegmentsHorizontal, lineSegmentsVertical

def findVerticalEdge(startX, startY, cornerGap, lineSegmentsVertical):
    xKeys = lineSegmentsVertical.keys()
    for x in sorted(xKeys):
        if(x < (startX-cornerGap)):
            # too small x
            continue
        if(x > (startX+cornerGap)):
            # too big
            return None
        # this x is in interval
        verticalEgdeCandidates = lineSegmentsVertical[x]
        for edge in verticalEgdeCandidates:
            if(edge[0] < (startY-cornerGap)):
                # too high
                continue
            if(edge[0] > (startY+cornerGap)):
                # too low
                # return None
                break
            return (x, edge)

def findBottomEdge(startX, endX, startY, cornerGap, lineSegmentsHorizontal):
    yKeys = lineSegmentsHorizontal.keys()
    for y in sorted(yKeys):
        if(y < (startY-cornerGap)):
            # too small
            continue
        if(y > (startY+cornerGap)):
            # too big
            return None
        # this y is in interval, find by left and right ends
        horizontalEgdeCandidates = lineSegmentsHorizontal[y]
        for edge in horizontalEgdeCandidates:
            if(edge[0] < (startX-cornerGap)):
                # too high
                continue
            if(edge[0] > (startX+cornerGap)):
                # too low
                # return None
                break
            # left corner OK, check right corner
            if(edge[1] < (endX-cornerGap)):
                # too small
                # return None
                break
            if(edge[1] > (endX+cornerGap)):
                # too big
                # return None
                break
            return (y, edge)

def findRectangles(lineSegmentsHorizontal, lineSegmentsVertical, cornerGap):
    rectangles = []

    # iterate over horizontal segments a consider them as horizontal top line of rectangle
    for y in sorted(lineSegmentsHorizontal.keys()):
        topSegments = lineSegmentsHorizontal[y]
    # for y, topSegments in lineSegmentsHorizontal.items():
        # start with TOP edge
        for topEdge in topSegments:
            leftEdge = findVerticalEdge(topEdge[0], y, cornerGap, lineSegmentsVertical)
            if(not leftEdge):
                # left edge not found
                continue
            rightEdge = findVerticalEdge(topEdge[1], y, cornerGap, lineSegmentsVertical)
            if(not rightEdge):
                # right edge not found
                continue
            # try to find bottom edge
            bottomEdge = findBottomEdge(topEdge[0], topEdge[1], (leftEdge[1][1]+rightEdge[1][1])//2, cornerGap, lineSegmentsHorizontal)
            if(not bottomEdge):
                continue
            # we found a rectangle
            tl = ( min(leftEdge[0], topEdge[0], bottomEdge[1][0] ), min(y, leftEdge[1][0], rightEdge[1][0]) )
            br = ( max(rightEdge[0], topEdge[1], bottomEdge[1][1] ), max(bottomEdge[0], leftEdge[1][1], rightEdge[1][1]) )
            rectangles.append( (tl, br)  ) 

    return rectangles

def __alignrectpurge(sides):
    """try to align sides, stotozni dve hrany ak sa lisia o menej ako aligngap"""
    if len(sides) == 0:
        return sides
    sides = sorted(sides)
    # print('sorted sides ', sides)
    isaligned = False
    while not isaligned:
        isaligned = True
        aligned = [sides[0]]
        for i in range(1, len(sides)):
            # print('check ', sides[i])
            if (sides[i-1]+aligngap) < sides[i]:
                aligned.append(sides[i])
                # print('added')
            else:
                isaligned = False
                # print('purged')
        sides = aligned
        # print('purged sides ', sides)
    return sides

def getRectangles(args, imgBW, imgdef):
    really_small_gap   = int(imgdef['gap'])     if 'gap'     in imgdef else 3
    min_segment_length = int(imgdef['segment']) if 'segment' in imgdef else 30
    corner_gap         = int(imgdef['corner'])  if 'corner'  in imgdef else 12
    if args.poster:
        really_small_gap   = int(really_small_gap * args.poster)
        min_segment_length = int(min_segment_length * args.poster)
        corner_gap         = int(corner_gap * args.poster)

    if args.debug:
        print('identify rectangles with gap {0}, segment {1}, corner {2}'.format(really_small_gap, min_segment_length, corner_gap))

    # identify rectangles
    lineSegmentsHorizontal, lineSegmentsVertical = findLineSegments(imgBW, really_small_gap, min_segment_length)
    # if args.debug:
    #    # log segments
    #    print('HORIZONTAL segments')
    #    for y in sorted(lineSegmentsHorizontal.keys()):
    #        print(y)
    #        for x in lineSegmentsHorizontal[y]:
    #            print(x)
        # print(lineSegmentsHorizontal)
    #    print('VERTICAL segments')
    #    for x in sorted(lineSegmentsVertical.keys()):
    #        print(x)
    #        for y in lineSegmentsVertical[x]:
    #            print(y)

    rectangles = findRectangles(lineSegmentsHorizontal, lineSegmentsVertical, corner_gap)
    # align rectangles
    leftsides = set()
    topsides = set()
    for r in rectangles:
        leftsides.add(r[0][0])
        topsides.add(r[0][1])
    leftsides = __alignrectpurge(leftsides)
    # print(leftsides)
    topsides = __alignrectpurge(topsides)
    # print(topsides)

    alignedrects = []
    for r in rectangles:
        arx = r[0][0]
        ary = r[0][1]
        if r[0][0] not in leftsides:
            # left side should be aligned
            for x in leftsides:
                if abs(x - r[0][0]) < aligngap:
                    arx = x
                    break
        if r[0][1] not in topsides:
            # left side should be aligned
            for y in topsides:
                if abs(y - r[0][1]) < aligngap:
                    ary = y
                    break
        alignedrects.append(((arx, ary), r[1]))
    
    # sort aligned rects 
    alignedrects.sort(key = lambda x: x[0][1]*100000+x[0][0])
    if args.debug:
        for i,r in enumerate(alignedrects):
            print(i+1, r)
            print(i+1, rectangles[i])
    
    return alignedrects
