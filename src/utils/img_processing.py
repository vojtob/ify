from pathlib import PureWindowsPath, Path
import os
import subprocess
import json

import numpy as np
import cv2
from numpy.lib.shape_base import apply_along_axis
# from cairosvg import svg2svg
import xml.etree.ElementTree as ET

import utils.rect_recognition as rr

BW_TRESHOLD = 135

def convertImage(img, imgdef, args):
    "convert input image into BW"
    if len(img.shape) > 2:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    treshold = int(imgdef['treshold']) if 'treshold' in imgdef else BW_TRESHOLD
    if args.debug:
        print('treshold', treshold)

    thresh = cv2.threshold(gray, treshold, 255, cv2.THRESH_BINARY_INV)[1]
    # edges = cv2.Canny(gray,100,200)
    # blur = cv2.blur(edges,(4,4))
    # cv2.imshow(cv2.namedWindow("addIcons"), gray)
    # cv2.waitKey()
    return thresh

def rectangles2image(img, rectangles):
    imgRec = np.copy(img)
    recCounter = 1
    font = cv2.FONT_HERSHEY_SIMPLEX
    for r in rectangles:
        cv2.rectangle(imgRec, r[0], r[1], (0,0,255), thickness=2)
        cv2.putText(imgRec,str(recCounter),(r[0][0],r[0][1]+30), font, 1, (0,0,255),1,cv2.LINE_AA)
        recCounter += 1

    # for y, segments in lineSegmentsHorizontal.items():
    #     for s in segments:
    #         cv2.line(img, (s[0],y),(s[1],y), (0,255,0), thickness=2)
    # for x, segments in lineSegmentsVertical.items():
    #     for s in segments:
    #         cv2.line(img, (x,s[0]),(x,s[1]), (255,0,0), thickness=2)

    return imgRec

def imgrectangles(img, imgdef, args):
    # convert to BW
    imgBW = convertImage(img, imgdef, args)
    # save BW image
    if args.debug:
        bwpath = args.bwdir / imgdef['fileName']
        bwpath.parent.mkdir(parents=True, exist_ok=True)           
        cv2.imwrite(str(bwpath), imgBW)
    
    # identify rectangles
    rectangles = rr.getRectangles(args, imgBW, imgdef)
    if args.verbose:
        imgrec = rectangles2image(img, rectangles)
        recpath = args.recdir / imgdef['fileName']
        recpath.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(recpath), imgrec)

    return rectangles

def overlayImageOverImage(bigImg, smallImage, smallImageOrigin, args):
    if args.debug:
        # print('overlay bigSize: {0[0]}x{0[1]}  iconSize: {1[0]}x{1[1]}  placement: {2[0]}x{2[1]}'.format(bigImg.shape, smallImage.shape, smallImageOrigin))
        print('overlay bigSize: {0}  iconSize: {1}  placement: {2}'.format(bigImg.shape, smallImage.shape, smallImageOrigin))
    x1 = smallImageOrigin[0]
    x2 = x1 + smallImage.shape[1]
    y1 = smallImageOrigin[1]
    y2 = y1 + smallImage.shape[0]

    if smallImage.shape[2] < 4:
        # no transparency in image
        x = np.full((smallImage.shape[0], smallImage.shape[1], 1), 255, smallImage.dtype)
        # print('x shape', x.shape)
        smallImage = np.concatenate((smallImage, x),2)
        # img = np.hstack((img, x))
        # print('add transparency shape', img.shape)
        # print('mask shape', mask.shape)      

    alpha_smallImage = smallImage[:, :, 3] / 255.0
    if args.debug:
        print(alpha_smallImage)
    # alpha_smallImage = [1.0 if x>0.5 else 0.0 for x in alpha_smallImage]
    # alpha_smallImage = [[1.0 if x>0.5 else 0.0 for x in row] for row in alpha_smallImage]
    # alpha_smallImage = np.rint(alpha_smallImage)
    if args.debug:
        print(alpha_smallImage)
    alpha_bigImage = 1.0 - alpha_smallImage

    # print('bigimg shape', bigImg.shape, smallImage.shape, alpha_bigImage.shape, alpha_smallImage.shape)
    if len(bigImg.shape) > 2:
        for c in range(0, 3):
            bigImg[y1:y2, x1:x2, c] = (alpha_smallImage * smallImage[:, :, c] + alpha_bigImage * bigImg[y1:y2, x1:x2, c])
    else:
        bigImg[y1:y2, x1:x2] = (alpha_smallImage[:,:] * smallImage[:, :,0] + alpha_bigImage * bigImg[y1:y2, x1:x2])

    return bigImg

def geticonxy(args, filename, iconfilepath, iconname, dicon, rectangle, xAlign, yAlign, marginSize=5):
    if str(iconfilepath).endswith('.svg'):
        if args.debug:
            print("read icon to aquire size:", iconfilepath)
        tree = ET.parse(iconfilepath)
        root = tree.getroot()
        vb = list(map(float, root.attrib['viewBox'].split()))
        if args.debug:
            print(vb)
        dx = vb[2]-vb[0]
        dy = vb[3]-vb[1]
        q = dicon / max(dx,dy)
        if args.debug:
            print("icon size:", dx, dy, q)
        dx = int(q*dx)
        dy = int(q*dy)
        if args.debug:
            print("icon size:", dx, dy)
    else:
        dx = dicon
        dy = dicon
    
    margin = marginSize
    if args.poster:
        margin = int(marginSize * args.poster)

    # calculate x position of icon
    if(xAlign == 'left'):
        x = rectangle[0][0] + margin
    elif(xAlign == 'right'):
        x = rectangle[1][0] - dx - margin
        # x = rectangle[1][0] - dicon - marginSize
    elif (xAlign == 'center'):
        x = (rectangle[1][0]+rectangle[0][0]-dx) // 2
        # x = (rectangle[1][0]+rectangle[0][0]-dicon) // 2
    else:
        # relative
        try:
            x = int( (1-xAlign)*rectangle[0][0] + xAlign*rectangle[1][0] - dx/2 )
            # x = int( (1-xAlign)*rectangle[0][0] + xAlign*rectangle[1][0] - dicon/2 )
        except:
            args.problems.append('icon {0} in image {1} has bad x align !!!!!!!'.format(iconname, filename))
            print('       icon x align bad format !!!!!!!')
            return None
    
    # calculate y position of icon
    if(yAlign == 'top'):
        y = rectangle[0][1] + margin
    elif(yAlign == 'bottom'):
        y = rectangle[1][1] - dy - margin
        # y = rectangle[1][1] - dicon - marginSize
    elif (yAlign == 'center'):
        y = (rectangle[1][1]+rectangle[0][1]-dy) // 2
        # y = (rectangle[1][1]+rectangle[0][1]-dicon) // 2
    else:
        # relative
        try:
            pass
            y = int( (1-yAlign)*rectangle[0][1] + yAlign*rectangle[1][1] - dy/2 )
            # y = int( (1-yAlign)*rectangle[0][1] + yAlign*rectangle[1][1] - dicon/2 )
        except:
            args.problems.append('icon {0} in image {1} has bad y align !!!!!!!'.format(iconname, filename))
            print('       icon y align bad format !!!!!!!!')
            return None

    if args.debug:
        print('icon', iconname, "(x,y): (", x, ', ', y, ')')
    return (x,y)

def __processdef(args, what, imgdef):
    if args.verbose or args.debug:
        print('Start adding ' + what + ' to image {0}'.format(imgdef['fileName']))

    # read image
    imgpath = args.pngdir / imgdef['fileName']
    if not (imgpath).exists():
        args.problems.append('Add ' + what + ' to image: file {0} does not exists !!!'.format(imgdef['fileName']))
        return
    if args.debug:
        print('whole image path:', imgpath)
    img = cv2.imread(str(imgpath), cv2.IMREAD_UNCHANGED)
    if what != 'test':
        rectangles = imgrectangles(img, imgdef, args)

    if what == 'icons':
        # icons2image(args, imgdef, img, rectangles)
        icons2image(args, imgdef, str(imgpath), rectangles, img)
    elif what == 'areas':
        areas2image(args, imgdef, img, rectangles)
    elif what == 'test':
        test(args, imgdef, img)
    else:
        args.problems.append('do not know what to add ' + what)

def add_decorations(args, what):
    if args.verbose:
        if args.file:
            print('add ', what, 'for a file', args.file)
        else:
            print('add ', what)
    # read definitions 
    p =   args.projectdir / 'src_doc' / 'img' / (what+'.json')
    if not p.exists():
        if args.verbose:
            print('no ' + what + ' definition at ' + str(p) +', skipp it')
        return
    with open(p) as imagesFile:
        imagedefs = json.load(imagesFile)
    if(args.file):
        processedFile = False
        pf = Path(args.file)
        if args.debug:
            print("match file path", pf)
    else:
        processedFile = True
    for imgdef in imagedefs:
        # if (args.file is not None) and (not PureWindowsPath(imgdef['fileName']).with_suffix('').match(args.file)):
        if args.file:
            # print('only specific file', args.file)
            # print(Path(imgdef['fileName']).with_suffix(''))
            if Path(imgdef['fileName']).with_suffix('') != pf:
                # we want to process a specific file, but not this
                # print('skip file ', imgdef['fileName'], args.file)
                continue
            processedFile = True
        # if args.verbose or args.debug:
        #     print('process ' + what + args.file)
        __processdef(args, what, imgdef)
    if not processedFile:
        print('file {0} not found for {1}'.format(args.file, what))
        args.problems.append('file {0} not found for {1}'.format(args.file, what))

def icons2image(args, imgdef, imgPath, rectangles, img):
    # add icons to image
    icmd = 'magick -density 1000 ' + imgPath + ' -background none'
    
    for icondef in imgdef['icons']:
        if args.debug:
            print('  add icon', icondef['iconName'])
        # find icon file
        iconfilepath = args.iconssourcedir / icondef['iconName']
        if not iconfilepath.exists():
            args.problems.append('Add icon2image: could not find icon {0} for image {1}'.format(icondef['iconName'], imgdef['fileName']))
            return
            # iconfilepath = args.iconssourcedir / 'generated' / icondef['iconName']
            # if not iconfilepath.exists():
            #     iconfilepath = args.projectdir / 'temp' / 'generated_icons' / icondef['iconName']
            #     if not iconfilepath.exists():
            #         args.problems.append('Add icon2image: could not find icon {0} for image {1}'.format(icondef['iconName'], imgdef['fileName']))
            #         return

        iconsize = icondef['size']
        if args.poster:
            iconsize = int(iconsize * args.poster)

        # calculate icon position
        if 'rec' in icondef:
            if args.debug:
                print('add icon by rect')
            recID = icondef['rec']
            if( recID > len(rectangles)):
                args.problems.append('Add icon2image: icon {0} for image {1} refers to non existing rectangle {2}'.format(icondef['iconName'], imgdef['fileName'], recID))
                return
            iconxy = geticonxy(args, imgdef['fileName'], iconfilepath, icondef['iconName'], 
                iconsize, rectangles[recID-1], icondef['x'], icondef['y'])
        else:
            if args.debug:
                print('add icon into whole image')
            iconxy = geticonxy(args, imgdef['fileName'], iconfilepath, icondef['iconName'], 
                iconsize, [[0,0],[img.shape[1], img.shape[0]]], icondef['x'], icondef['y'])
            if args.debug:
                print('add icon by position', iconxy)

            # iconxy = (icondef['asbx'], icondef['absy'])

        icon_cmd = '( "{iconpath}" -resize {iconsize}x{iconsize} ) -gravity NorthWest -geometry +{x}+{y} -composite'.format(
            iconpath=iconfilepath, iconsize=iconsize, x=iconxy[0], y=iconxy[1])
        icmd = icmd + ' ' + icon_cmd

    imgiconpath = args.iconsdir / imgdef['fileName']
    imgiconpath.parent.mkdir(parents=True, exist_ok=True)
    icmd = icmd + ' ' + str(imgiconpath)
    if args.debug:
        print(icmd)
    subprocess.run(icmd, shell=False)

def lines2image(args, lines, img, rectangles):
    for line in lines:
        linepoints = line['points']
        coordinates = []
        p = linepoints[0]
        r = rectangles[p[0]-1]
        xAlign = p[1]
        yAlign = p[2]
        lastx = int( (1-xAlign)*r[0][0] + xAlign*r[1][0] )
        lasty = int( (1-yAlign)*r[0][1] + yAlign*r[1][1] )
        coordinates.append((lastx,lasty))
        # img = cv2.circle(img, (lastx, lasty), 10, [0,0,255], 10)
        for p in linepoints[1:]:
            r = rectangles[p[0]-1]
            ratio = p[2]
            if p[1] == 'X':
                # menia sa obe suradnice
                lastx = int( (1-p[2])*r[0][0] + p[2]*r[1][0] )
                lasty = int( (1-p[3])*r[0][1] + p[3]*r[1][1] )
            elif p[1] in ['L', 'R']:
                # y sa nemeni iba x
                lastx = int( (1-ratio)*r[0][0] + ratio*r[1][0] )
            else:
                # x sa nemeni iba y
                lasty = int( (1-ratio)*r[0][1] + ratio*r[1][1] )
            coordinates.append((lastx, lasty))

        linewidth = line['linewidth'] if ('linewidth' in line) else 2
        if args.poster:
            linewidth = int(linewidth * args.poster)
        linecolor = (line['linecolor'][2], line['linecolor'][1], line['linecolor'][0]) if 'linecolor' in line else (145,44,111)
        if args.debug:
            print('linecolor: {0}, linewidth: {1}'.format(linecolor, linewidth))
        points = np.array([[p[0],p[1]] for p in coordinates], np.int32)
        points = points.reshape((-1,1,2))
        img = cv2.polylines(img, [points], False, linecolor, linewidth)

        # koncova sipka
        if 'arrowsize' in line:
            arrowsize = line['arrowsize']
            if args.poster:
                arrowsize = int(arrowsize * args.poster)
            if args.debug:
                print('Draw ending arrow with size: {0}'.format(arrowsize))
            p0 = coordinates[-1]
            if p[1] == 'L':
                p1 = (p0[0]+arrowsize, p0[1]-arrowsize)
                p2 = (p0[0]+arrowsize, p0[1]+arrowsize)
            elif p[1] == 'R':
                p1 = (p0[0]-arrowsize, p0[1]-arrowsize)
                p2 = (p0[0]-arrowsize, p0[1]+arrowsize)
            elif p[1] == 'U':
                p1 = (p0[0]-arrowsize, p0[1]+arrowsize)
                p2 = (p0[0]+arrowsize, p0[1]+arrowsize)
            elif p[1] == 'D':
                p1 = (p0[0]-arrowsize, p0[1]-arrowsize)
                p2 = (p0[0]+arrowsize, p0[1]-arrowsize)
            img = cv2.line(img, p0, p1, linecolor, linewidth)
            img = cv2.line(img, p0, p2, linecolor, linewidth)
        # zaciatocny kruzok
        if 'circlesize' in line:
            circlesize = line['circlesize']
            if args.poster:
                circlesize = int(circlesize * args.poster)
            if args.debug:
                print('Draw starting circle with size  {0}'.format(circlesize))
            p0 = coordinates[0]
            img = cv2.circle(img, p0, circlesize, linecolor, -1)
    return img

def polygonpoints(args, polygon, rectangles):
    border = polygon['border']  if 'border' in polygon else 8
    if args.poster:
        border = int(border * args.poster)
    # identify bounding polygons for areas
    points = []
    for p in polygon['points']:
        if len(p) == 2:
            # by corner of rectangle
            r = rectangles[p[0]-1]
            istop = p[1][0] == 'T'
            isleft = p[1][1] == 'L'
            x = (r[0][0]-border) if isleft else (r[1][0]+border)
            y = (r[0][1]-border) if istop  else (r[1][1]+border)
        else:
            # by coordinates defined by rectangles
            r = rectangles[p[0]-1]
            isleft = p[1] == 'L'
            x = (r[0][0]-border) if isleft else (r[1][0]+border)
            r = rectangles[p[2]-1]
            istop = p[3] == 'T'
            y = (r[0][1]-border) if istop  else (r[1][1]+border)
        if points:
            # prev = points[-1]
            for prev in points:
                if abs(prev[0]-x) < (3*border):
                    x = prev[0]
                if abs(prev[1]-y) < (3*border):
                    y = prev[1]
        points.append([x,y])

    points.append(points[0])
    return points

def rectpoints(args, rectarea, rectangles):
    border = rectarea['border']  if 'border' in rectarea else 8
    if args.poster:
        border = int(border * args.poster)
    points = []
    sr = rectarea['corners']
    r = rectangles[sr[0]-1]
    x1 = r[0][0]-border
    y1 = r[0][1]-border
    x2 = r[1][0]+border
    y2 = r[1][1]+border
    r = rectangles[sr[1]-1]
    x1 = min(x1, r[0][0]-border)
    y1 = min(y1, r[0][1]-border)
    x2 = max(x2, r[1][0]+border)
    y2 = max(y2, r[1][1]+border)
    points.append([x1,y1])
    points.append([x2,y1])
    points.append([x2,y2])
    points.append([x1,y2])
    return points

def polygon2image(args, points, area, img):
    linewidth = area['linewidth'] if ('linewidth' in area) else 2
    linecolor = (area['linecolor'][2], area['linecolor'][1], area['linecolor'][0]) if 'linecolor' in area else (145,44,111)
    opacity   = area['opacity'] if 'opacity' in area else 80
    if args.poster:
        linewidth = int(linewidth * args.poster)
    if args.debug:
        print('linecolor: {0}, linewidth: {1}, opacity: {2}'.format(linecolor, linewidth, opacity))

    points = np.array([[p[0],p[1]] for p in points], np.int32)
    points = points.reshape((-1,1,2))
    # draw polygon
    img = cv2.polylines(img, [points], True, linecolor, linewidth)
    if args.debug:
        print(points)

    # add mask opacity
    mask = np.full((img.shape[0], img.shape[1]), opacity, np.uint8)
    mask = cv2.fillPoly(mask, [points], 255)
    img[:, :, 3] = mask
    return img

def areas2image(args, imgdef, img, rectangles):
    # try to read image with icons
    imgpath = args.iconsdir / imgdef['fileName']
    if imgpath.exists():
        img = cv2.imread(str(imgpath), cv2.IMREAD_UNCHANGED)

    if args.verbose:
        print('process areas with extension', imgdef['ext'])

    # if args.debug:
    #     print(img.shape)
    #     print(img[:, :, 3])
    if img.shape[2] < 4:
        # no transparency in image
        x = np.full((img.shape[0], img.shape[1]), 255, np.uint8)
        img = np.concatenate((img, x),2)

    if 'lines' in imgdef:
        img = lines2image(args, imgdef['lines'], img, rectangles)
    img[:, :, 3] = np.full((img.shape[0], img.shape[1]), 255, np.uint8)
    # if 'polygon' in imgdef:
    #     points = polygonpoints(args, imgdef['polygon'], rectangles)
    #     img = polygon2image(args, points, imgdef['polygon'], img)
    # if 'rect-area' in imgdef:
    #     points = rectpoints(args, imgdef['rect-area'], rectangles)
    #     img = polygon2image(args, points, imgdef['rect-area'], img)
    for name, r in imgdef.items():
        if name == 'polygon':
            points = polygonpoints(args, r, rectangles)
            img = polygon2image(args, points, r, img)
        if name == 'rect-area':
            points = rectpoints(args, r, rectangles)
            img = polygon2image(args, points, r, img)

    imgpath = args.areasdir / imgdef['fileName'].replace('.png', '__{0}.png'.format(imgdef['ext']))
    imgpath.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(imgpath), img)

def test(args, imgdef, img):
    if len(img.shape) > 2:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # treshold = int(imgdef['treshold']) if 'treshold' in imgdef else BW_TRESHOLD
    # if args.debug:
    #     print('treshold', treshold)
    # thresh = cv2.threshold(gray, treshold, 255, cv2.THRESH_BINARY_INV)[1]

    # edges = cv2.Canny(thresh,100,200)
    edges = cv2.Canny(gray,0,1)

    tpath = args.destdir / '_test' / imgdef['fileName']
    tpath.parent.mkdir(parents=True, exist_ok=True)           
    cv2.imwrite(str(tpath), edges)

    return
