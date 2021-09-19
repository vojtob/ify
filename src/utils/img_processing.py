from pathlib import PureWindowsPath, Path
import os
import subprocess
import json

import numpy as np
import cv2
from numpy.lib.shape_base import apply_along_axis
from cairosvg import svg2png

import utils.rect_recognition as rr

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

def geticonxy(args, filename, iconname, dicon, rectangle, xAlign, yAlign, marginSize=5):
    # dx = icon.shape[1]
    # dy = icon.shape[0]

    # calculate x position of icon
    if(xAlign == 'left'):
        x = rectangle[0][0] + marginSize
    elif(xAlign == 'right'):
        # x = rectangle[1][0] - dx - marginSize
        x = rectangle[1][0] - dicon - marginSize
    elif (xAlign == 'center'):
        # x = (rectangle[1][0]+rectangle[0][0]-dx) // 2
        x = (rectangle[1][0]+rectangle[0][0]-dicon) // 2
    else:
        # relative
        try:
            # x = int( (1-xAlign)*rectangle[0][0] + xAlign*rectangle[1][0] - dx/2 )
            x = int( (1-xAlign)*rectangle[0][0] + xAlign*rectangle[1][0] - dicon/2 )
        except:
            args.problems.append('icon {0} in image {1} has bad x align !!!!!!!'.format(iconname, filename))
            print('       icon x align bad format !!!!!!!')
            return None
    
    # calculate y position of icon
    if(yAlign == 'top'):
        y = rectangle[0][1] + marginSize
    elif(yAlign == 'bottom'):
        # y = rectangle[1][1] - dy - marginSize
        y = rectangle[1][1] - dicon - marginSize
    elif (yAlign == 'center'):
        # y = (rectangle[1][1]+rectangle[0][1]-dy) // 2
        y = (rectangle[1][1]+rectangle[0][1]-dicon) // 2
    else:
        # relative
        try:
            pass
            # y = int( (1-yAlign)*rectangle[0][1] + yAlign*rectangle[1][1] - dy/2 )
            y = int( (1-yAlign)*rectangle[0][1] + yAlign*rectangle[1][1] - dicon/2 )
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
    imgpath = args.exporteddir / imgdef['fileName']
    if not (imgpath).exists():
        args.problems.append('Add ' + what + ' to image: file {0} does not exists !!!'.format(imgdef['fileName']))
        return
    if args.debug:
        print('whole image path:', imgpath)
    img = cv2.imread(str(imgpath), cv2.IMREAD_UNCHANGED)
    rectangles = imgrectangles(img, imgdef, args)

    if what == 'icons':
        # icons2image(args, imgdef, img, rectangles)
        icons2image(args, imgdef, str(imgpath), rectangles)
    elif what == 'areas':
        areas2image(args, imgdef, img, rectangles)
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

def icons2imageXX(args, imgdef, img, rectangles):
    # add icons to image
    for icondef in imgdef['icons']:
        if args.debug:
            print('  add icon', icondef['iconName'])
        if icondef['iconName'].endswith('.svg'):
            # SVG
            # ipath = Path('C:/Projects_src/resources/dxc-icons/DXC_Miscellaneous_Icons')/icondef['iconName']
            ipath = args.iconssourcedir / icondef['iconName']
            isize = icondef['size']
            print(str(ipath), isize)
            icon = svg2png(url = str(ipath), output_width=isize, output_height=icondef['size'])
            icon = np.fromstring(icon, np.uint8)
            icon = cv2.imdecode(icon, cv2.IMREAD_UNCHANGED)
        else:
            # PNG
            iconfilepath = args.iconssourcedir / icondef['iconName']
            if not iconfilepath.exists():
                iconfilepath = args.iconssourcedir / 'generated' / icondef['iconName']
                if not iconfilepath.exists():
                    iconfilepath = args.projectdir / 'temp' / 'generated_icons' / icondef['iconName']
                    if not iconfilepath.exists():
                        args.problems.append('Add icon2image: could not find icon {0} for image {1}'.format(icondef['iconName'], imgdef['fileName']))
                        return
            icon = cv2.imread(str(iconfilepath), cv2.IMREAD_UNCHANGED)
        # resize icon
        # if args.debug:
        #     print(icon.shape)
        s = max(icon.shape[0], icon.shape[1])
        dy = int((icondef['size']*icon.shape[0])/s)
        dx = int((icondef['size']*icon.shape[1])/s)
        icon = cv2.resize(icon, (dx,dy), interpolation = cv2.INTER_NEAREST)
        if args.debug:
            bwpath = (args.bwdir / icondef['iconName']).with_suffix('')
            bwpath.parent.mkdir(parents=True, exist_ok=True)           
            cv2.imwrite(str(bwpath)+'.png', icon)

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

        img = overlayImageOverImage(img, icon, iconxy, args)


    imgiconpath = args.iconsdir / imgdef['fileName']
    imgiconpath.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(imgiconpath), img)


def icons2image(args, imgdef, imgPath, rectangles):
    # add icons to image
    icmd = 'magick -density 1000 ' + imgPath + ' -background none'
    
    for icondef in imgdef['icons']:
        if args.debug:
            print('  add icon', icondef['iconName'])
        # find icon file
        iconfilepath = args.iconssourcedir / icondef['iconName']
        if not iconfilepath.exists():
            iconfilepath = args.iconssourcedir / 'generated' / icondef['iconName']
            if not iconfilepath.exists():
                iconfilepath = args.projectdir / 'temp' / 'generated_icons' / icondef['iconName']
                if not iconfilepath.exists():
                    args.problems.append('Add icon2image: could not find icon {0} for image {1}'.format(icondef['iconName'], imgdef['fileName']))
                    return

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
            iconxy = geticonxy(args, imgdef['fileName'], icondef['iconName'], 
                iconsize, rectangles[recID-1], icondef['x'], icondef['y'])
        else:
            if args.debug:
                print('add icon by position', iconxy)
            iconxy = (icondef['x'], icondef['y'])

        icon_cmd = '( {iconpath} -filter Hanning -resize {iconsize}x{iconsize} ) -gravity NorthWest -geometry +{x}+{y} -composite'.format(
            iconpath=iconfilepath, iconsize=iconsize, x=iconxy[0], y=iconxy[1])
        icmd = icmd + ' ' + icon_cmd

    imgiconpath = args.iconsdir / imgdef['fileName']
    imgiconpath.parent.mkdir(parents=True, exist_ok=True)
    icmd = icmd + ' ' + str(imgiconpath)
    if args.debug:
        print(icmd)
    subprocess.run(icmd, shell=False)

def areas2image(args, imgdef, img, rectangles):
    # try to read image with icons
    imgpath = args.iconsdir / imgdef['fileName']
    if imgpath.exists():
        img = cv2.imread(str(imgpath), cv2.IMREAD_UNCHANGED)

    border = imgdef['border']  if 'border' in imgdef else 8
    # identify bounding polygons for areas
    polygon = []
    for p in imgdef['points']:
        r = rectangles[p[0]-1]
        top = p[1][0] == 'T'
        left = p[1][1] == 'L'
        x = (r[0][0]-border) if left else (r[1][0]+border)
        y = (r[0][1]-border) if top  else (r[1][1]+border)
        if polygon:
            prev = polygon[-1]
            if abs(prev[0]-x) < (2*border):
                x = prev[0]
            if abs(prev[1]-y) < (2*border):
                y = prev[1]
        polygon.append((x,y))
    polygon.append(polygon[0])

    if args.debug:
        print(polygon)

    linecolor = (imgdef['linecolor'][2], imgdef['linecolor'][1], imgdef['linecolor'][0]) if 'linecolor' in imgdef else (145,44,111)
    linewidth = imgdef['linewidth'] if ('linewidth' in imgdef) else 2
    opacity   = imgdef['opacity'] if 'opacity' in imgdef else 80
    if args.debug:
        print('linecolor: {0}, linewidth: {1}, opacity: {2}'.format(linecolor, linewidth, opacity))

    # add transparency to image
    mask = np.full((img.shape[0], img.shape[1]), opacity, np.uint8)
    # for polygon in polygon:
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
