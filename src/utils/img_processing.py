from pathlib import PureWindowsPath, Path
import os
import subprocess
import json

import numpy as np
import cv2

import utils.rect_recognition as rr
import utils.rect_areas as ra

BW_TRESHOLD = 135

def convertImage(img, imgdef, args):
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

def overlayImageOverImage(bigImg, smallImage, smallImageOrigin):
    # print('overlay bigSize: {0[0]}x{0[1]}  iconSize: {1[0]}x{1[1]}  placement: {2[0]}x{2[1]}'.format(bigImg.shape, smallImage.shape, smallImageOrigin))
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
    alpha_bigImage = 1.0 - alpha_smallImage

    # print('bigimg shape', bigImg.shape, smallImage.shape, alpha_bigImage.shape, alpha_smallImage.shape)
    if len(bigImg.shape) > 2:
        for c in range(0, 3):
            bigImg[y1:y2, x1:x2, c] = (alpha_smallImage * smallImage[:, :, c] + alpha_bigImage * bigImg[y1:y2, x1:x2, c])
    else:
        bigImg[y1:y2, x1:x2] = (alpha_smallImage[:,:] * smallImage[:, :,0] + alpha_bigImage * bigImg[y1:y2, x1:x2])

    return bigImg

def geticonxy(args, filename, iconname, icon, rectangle, xAlign, yAlign, marginSize=5):
    dx = icon.shape[1]
    dy = icon.shape[0]

    # calculate x position of icon
    if(xAlign == 'left'):
        x = rectangle[0][0] + marginSize
    elif(xAlign == 'right'):
        x = rectangle[1][0] - dx - marginSize
    elif (xAlign == 'center'):
        x = (rectangle[1][0]+rectangle[0][0]-dx) // 2
    else:
        # relative
        try:
            x = int( (1-xAlign)*rectangle[0][0] + xAlign*rectangle[1][0] - dx/2 )
        except:
            args.problems.append('icon {0} in image {1} has bad x align !!!!!!!'.format(iconname, filename))
            print('       icon x align bad format !!!!!!!')
            return None
    
    # calculate y position of icon
    if(yAlign == 'top'):
        y = rectangle[0][1] + marginSize
    elif(yAlign == 'bottom'):
        y = rectangle[1][1] - dy - marginSize
    elif (yAlign == 'center'):
        y = (rectangle[1][1]+rectangle[0][1]-dy) // 2
    else:
        # relative
        try:
            pass
            y = int( (1-yAlign)*rectangle[0][1] + yAlign*rectangle[1][1] - dy/2 )
        except:
            args.problems.append('icon {0} in image {1} has bad y align !!!!!!!'.format(iconname, filename))
            print('       icon y align bad format !!!!!!!!')
            return None

    return (x,y)

def __processdef(args, what, imgdef):
    if args.verbose:
        print('Start adding ' + what + ' to image {0}'.format(imgdef['fileName']))

    # read image
    imgpath = args.exporteddir / imgdef['fileName']
    if not (imgpath).exists():
        args.problems.append('Add ' + what + ' to image: file {0} does not exists !!!'.format(imgdef['fileName']))
        return
    if args.debug:
        print('whole image path:', imgpath)
    img = cv2.imread(str(imgpath), cv2.IMREAD_UNCHANGED)
    rectangles = imgrectangles(img, imgdef, args)

    if what == 'icons':
        icons2image(args, imgdef, img, rectangles)
    elif what == 'areas':
        areas2image(args, imgdef, img, rectangles)
    else:
        args.problems.append('do not know what to add ' + what)

def __add_decorations(args, what):
    if args.verbose:
        print('add ', what)
    # read definitions 
    p =   args.projectdir / 'src_doc' / 'img' / (what+'.json')
    if not p.exists():
        if args.verbose:
            print('no ' + what + ' definition at ' + str(p) +', skipp it')
        return
    with open(p) as imagesFile:
        imagedefs = json.load(imagesFile)
    for imgdef in imagedefs:
        if (args.file is not None) and (not PureWindowsPath(imgdef['fileName']).with_suffix('').match(args.file)):
            # we want to process a specific file, but not this
            continue
        __processdef(args, what, imgdef)

def add_icons(args):
    __add_decorations(args, 'icons')

def add_areas(args):
    __add_decorations(args, 'areas')

def icons2image(args, imgdef, img, rectangles):
    # add icons to image
    for icondef in imgdef['icons']:
        if args.debug:
            print('  add icon', icondef['iconName'])
        iconfilepath = args.iconssourcedir / icondef['iconName']
        if not iconfilepath.exists():
            iconfilepath = args.iconssourcedir / 'generated' / icondef['iconName']
            if not iconfilepath.exists():
                args.problems.append('Add icon2image: could not find icon {0} for image {1}'.format(icondef['iconName'], imgdef['fileName']))
                return
        # resize icon
        icon = cv2.imread(str(iconfilepath), cv2.IMREAD_UNCHANGED)
        s = max(icon.shape[0], icon.shape[1])
        dy = int((icondef['size']*icon.shape[0])/s)
        dx = int((icondef['size']*icon.shape[1])/s)
        icon = cv2.resize(icon, (dx,dy))

        if 'rec' in icondef:
            if args.debug:
                print('add icon by rect')
            recID = icondef['rec']
            if( recID > len(rectangles)):
                args.problems.append('Add icon2image: icon {0} for image {1} refers to non existing rectangle {2}'.format(icondef['iconName'], imgdef['fileName'], recID))
                return
            iconxy = geticonxy(args, imgdef['fileName'], icondef['iconName'], 
            icon, rectangles[recID-1], icondef['x'], icondef['y'])
        else:
            iconxy = (icondef['x'], icondef['y'])
            if args.debug:
                print('add icon by position', iconxy)

        img = overlayImageOverImage(img, icon, iconxy)


    imgiconpath = args.iconsdir / imgdef['fileName']
    imgiconpath.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(imgiconpath), img)

def areas2image(args, imgdef, img, rectangles):
    # try to read image with icons
    imgpath = args.iconsdir / imgdef['fileName']
    if imgpath.exists():
        img = cv2.imread(str(imgpath), cv2.IMREAD_UNCHANGED)

    # identify bounding polygons for areas
    polygons = []
    if 'areas' in imgdef:
        if args.debug:
            print('aras by AREAS')
        if 'distance' in imgdef:
            if args.debug:
                print('set distance', int(imgdef['distance']))
            ra.set_area_gap(int(imgdef['distance']))
        for area in imgdef['areas']:
            area_rectangles = [rectangles[r-1] for r in area]            
            polygons.append(ra.find_traverse_points(area_rectangles))
    elif 'points' in imgdef:
        if args.debug:
            print('areas by POINTS')
        polygons.append(ra.shiftpoints(imgdef['points'], rectangles))


    linecolor = (imgdef['linecolor'][2], imgdef['linecolor'][1], imgdef['linecolor'][0]) if 'linecolor' in imgdef else (145,44,111)
    linewidth = imgdef['linewidth'] if ('linewidth' in imgdef) else 3
    opacity   = imgdef['opacity'] if 'opacity' in imgdef else 80
    if args.debug:
        print('linecolor: {0}, linewidth: {1}, opacity: {2}'.format(linecolor, linewidth, opacity))

    # add transparency to image
    mask = np.full((img.shape[0], img.shape[1]), opacity, np.uint8)
    for polygon in polygons:
        points = np.array([[p[0],p[1]] for p in polygon], np.int32)
        points = points.reshape((-1,1,2))
        # draw red polygon
        img = cv2.polylines(img, [points], True, linecolor, linewidth)
        # use mask to set transparency
        mask = cv2.fillPoly(mask, [points], 255)
    # print('orig shape', img.shape)
    if img.shape[2] < 4:
        # no transparency in image
        x = np.zeros((img.shape[0], img.shape[1], 1), img.dtype)
        # print('x shape', x.shape)
        img = np.concatenate((img, x),2)
        # img = np.hstack((img, x))
        # print('add transparency shape', img.shape)
        # print('mask shape', mask.shape)      
    img[:, :, 3] = mask
    # print('final shape', img.shape)

    imgpath = args.areasdir / imgdef['fileName'].replace('.png', '_{0}.png'.format(imgdef['focus-name']))
    imgpath.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(imgpath), img)
