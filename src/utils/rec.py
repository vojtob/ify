import numpy as np
import cv2
from pathlib import Path
import sys
import argparse

BW_TRESHOLD = 135
ALIGNGAP = 7

LOG_LEVEL_ALL = 0
LOG_LEVEL_DEBUG = 1
LOG_LEVEL_INFO = 2
LOG_LEVEL_WARNING = 3
LOG_LEVEL_ERROR = 4

def log(log_level, *args):
    if log_level < LOG_LEVEL:
        return  
    print(*args, sep=', ', file=sys.stderr, flush=True)


def logImage(img, imgpath: Path, suffix: str):
    if LOG_LEVEL <= LOG_LEVEL_DEBUG:
        ip = imgpath.with_stem(imgpath.stem + suffix)
        ip.parent.mkdir(parents=True, exist_ok=True)           
        log(LOG_LEVEL_DEBUG, f"Saving image to {ip}")
        cv2.imwrite(str(ip), img)

def __read_image(imgpath: Path) -> np.ndarray:
    # Read the image using OpenCV
    img = cv2.imread(str(imgpath), cv2.IMREAD_UNCHANGED)
    return img

def __getBW(img, orig_img_path: Path):
    if len(img.shape) == 2: # grayscale image
        gray = img
    elif img.shape[2] == 4: # color image with alpha channel
        gray = cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2GRAY)
    else: # color image without alpha channel
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # save BW image
    logImage(gray, orig_img_path, "_BW")

    return gray

def __getCountours(img, orig_img_path):
    # blur = cv2.blur(img,(4,4))
    # logImage(blur, orig_img_path, "_BLUR")

    treshold =  BW_TRESHOLD
    log(LOG_LEVEL_ALL, f"{treshold=}")
    # _, thresh = cv2.threshold(imgBW, treshold, 255, cv2.THRESH_BINARY_INV)
    img = cv2.adaptiveThreshold(
       img, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )
    logImage(img, orig_img_path, "_TRESH")

    # img = cv2.Canny(img, 50, 150)
    # logImage(img, orig_img_path, "_EDGES")

    # contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    
    # filtruj contours to keep only big enough rectangles
    # contours = [c for c in contours if cv2.isContourConvex(c)]
    # contours = [c for c in contours if cv2.contourArea(c) > 1000]

    big_countours = []
    csize = 100
    # i = 0
    # r = 0
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if (w+h) > (3*csize):  # Filter for large rectangles
            big_countours.append(c)
            # rectangle = ( (x, y), (x + w, y + h) )
            # rectangles.append(rectangle)
            # log(LOG_LEVEL_ALL, f"{r:>3} {i:>5} Rectangle : {rectangle}  hierarchy: {hierarchy[0][i]}")
            # r += 1
        # i += 1

    return big_countours

def __get_rectangles(contours):
    rectangles = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        rectangle = ( (x, y), (x + w, y + h) )
        rectangles.append(rectangle)

    return rectangles

def __purge_rectangles(rectangles):
    purged = []
    for r in rectangles:
        isduplicate = False
        for rp in purged:
            if (abs(r[0][0] - rp[0][0]) < ALIGNGAP) and (abs(r[0][1] - rp[0][1]) < ALIGNGAP) and (abs(r[1][0] - rp[1][0]) < ALIGNGAP) and (abs(r[1][1] - rp[1][1]) < ALIGNGAP):
                isduplicate = True
                break
        if not isduplicate:
            purged.append(r)
    log(LOG_LEVEL_DEBUG, f"original {len(rectangles)} purged to {len(purged)} rectangles")

    return purged

def logRectangles(img, orig_img_path: Path, rectangles):
    reccolor = (0, 0, 255) # green

    image_copy = img[:, :, :3].copy()
    for i, rectangle in enumerate(rectangles):  
        cv2.rectangle(image_copy, rectangle[0], rectangle[1], reccolor, thickness=2)
        cv2.putText(image_copy, 
                    str(i+1),
                    (rectangle[0][0],rectangle[0][1]+30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, reccolor,1,cv2.LINE_AA)
    logImage(image_copy, orig_img_path, "_REC")

    for i, c in enumerate(rectangles):
        log(LOG_LEVEL_DEBUG, f"{i+1:>3}.Rectangle : {c}")

def __group_similar(values, epsilon=ALIGNGAP):
    snapped = []
    for val in sorted(values):
        for snap_val in snapped:
            if abs(val - snap_val) <= epsilon:
                val = snap_val  # zarovnaj na existujúcu hodnotu
                break
        else:
            snapped.append(val)  # nová skupina
    return snapped

def __snap_value(val, snapped_vals, epsilon=ALIGNGAP):
    for snap_val in snapped_vals:
        if abs(val - snap_val) <= epsilon:
            return snap_val
    return val

def __snap_rectangles(rectangles):
    # Pre každý bod v obdlžníku nájdeme najbližšiu hodnotu z "snapped" hodnot
    # a nahradíme ňou pôvodnú hodnotu.
    # Vytvoríme nové obdlžníky so "snapped" hodnotami.

    # Získame všetky hodnoty x1, x2, y1, y2 z obdlžníkov
    lefts   = [x1 for (x1, y1), (x2, y2) in rectangles]
    rights  = [x2 for (x1, y1), (x2, y2) in rectangles]
    tops    = [y1 for (x1, y1), (x2, y2) in rectangles]
    bottoms = [y2 for (x1, y1), (x2, y2) in rectangles]

    snap_lefts   = __group_similar(lefts)
    snap_rights  = __group_similar(rights)
    snap_tops    = __group_similar(tops)
    snap_bottoms = __group_similar(bottoms)

    snapped_rectangles = []
    for (x1, y1), (x2, y2) in rectangles:
        x1_new = __snap_value(x1, snap_lefts)
        x2_new = __snap_value(x2, snap_rights)
        y1_new = __snap_value(y1, snap_tops)
        y2_new = __snap_value(y2, snap_bottoms)
        snapped_rectangles.append(((x1_new, y1_new), (x2_new, y2_new)))
    
    return snapped_rectangles

def getRectangles(img, imgpath: Path, loglevel):
    global LOG_LEVEL
    LOG_LEVEL = loglevel

    # convert to BW
    imgBW = __getBW(img, imgpath)
    contours = __getCountours(imgBW, imgpath)
    rectangles = __get_rectangles(contours)

    rectangles = __purge_rectangles(rectangles)
    rectangles.sort(key = lambda x: x[0][1]*100000+x[0][0])
    rectangles = __snap_rectangles(rectangles)

    log(LOG_LEVEL_INFO, f"Identified {len(rectangles)} rectangles.")
    return rectangles

if __name__ == "__main__":
    # parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    # parser.add_argument("--verbose", action="store_true", help="Enable verbose mode.")
    # parser.add_argument("--loglevel", type=int, default=LOG_LEVEL, help="Set log level (0-4).")
    # args = parser.parse_args()
    LOG_LEVEL = LOG_LEVEL_DEBUG
    
    imgpath = Path("RK_koncept.png")
    # log(LOG_LEVEL_INFO, f"Current working directory: {Path.cwd()}")
    if not imgpath.exists():
        log(LOG_LEVEL_ERROR, f"Image path does not exist: {imgpath}")
        sys.exit(1)

    img = __read_image(imgpath)
    if img is None:
        log(LOG_LEVEL_ERROR, f"Failed to read image: {imgpath}")
        sys.exit(1)
    
    # Extract and log pixel values for the specified region
    # x_start, x_end = 410, 430
    # y_start, y_end = 410, 430
    # region = img[y_start:y_end, x_start:x_end]
    # log(LOG_LEVEL_INFO, f"Pixel values in region x:[{x_start}-{x_end}], y:[{y_start}-{y_end}]:\n{region}")
    getRectangles(img, imgpath, LOG_LEVEL_DEBUG)