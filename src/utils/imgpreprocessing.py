import cv2

BW_TRESHOLD = 135

def convertImage(img, imgdef, args):
    """convert input image into BW using defined treshold"""

    # convert into gray scala
    if len(img.shape) > 2:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # apply treshold
    treshold = int(imgdef['treshold']) if 'treshold' in imgdef else BW_TRESHOLD
    if args.debug:
        print('treshold', treshold)

    thresh = cv2.threshold(gray, treshold, 255, cv2.THRESH_BINARY_INV)[1]
    # edges = cv2.Canny(gray,100,200)
    # blur = cv2.blur(edges,(4,4))
    # cv2.imshow(cv2.namedWindow("addIcons"), gray)
    # cv2.waitKey()
    return thresh

