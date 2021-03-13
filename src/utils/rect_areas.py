# if the distance between two points is smaller than this, continue in line
REALLY_SMALL_GAP = 3
# shorter lines are not line
MIN_SEGMENT_LENGTH = 30
# rounded rectangles
CORNER_GAP = 15
# 
AREA_GAP = 35
AREA_BORDER = 8

UP = 1
RIGHT = 2
DOWN = 3
LEFT = 4

def get_edge(r, edge):
    if(edge == UP):
        return (r[0][1], r[0][0], r[1][0])
    if(edge == RIGHT):
        return (r[1][0], r[0][1], r[1][1])
    if(edge == DOWN):
        return (r[1][1], r[0][0], r[1][0])
    if(edge == LEFT):
        return (r[0][0], r[0][1], r[1][1])

def get_collision_trace(edge, direction):
    return (getopposite(direction), edge)

def getopposite(direction):
    if direction == UP:
        return DOWN
    if direction == DOWN:
        return UP
    if direction == LEFT:
        return RIGHT
    if direction == RIGHT:
        return LEFT

def get_collision_edge(edge, edgename, edgedir, lastpoint):
    """edge that is prolonged by GAP to collide with nearby reactangle. 
    Moreover it is shifted away by GAP to not interfere with aligned rectangle and to collide with other rectangle"""

    if (edgename==UP) or (edgename == LEFT):
        collision_shift = edge[0] - AREA_GAP
    else:
        collision_shift = edge[0] + AREA_GAP

    if edgedir == LEFT:
        return (collision_shift, edge[1] - AREA_GAP, lastpoint[0])
    elif edgedir == RIGHT:
        return (collision_shift, lastpoint[0], edge[2] + AREA_GAP)
    elif edgedir == UP:
        return (collision_shift, edge[1] - AREA_GAP, lastpoint[1])
    else:
        return (collision_shift, lastpoint[1], edge[2] + AREA_GAP)

def get_collision_point(origedge, edgename, edgedir, collidingedge):
    if edgedir==DOWN:
        y = collidingedge[0] - AREA_BORDER
    elif edgedir==UP:
        y = collidingedge[0] + AREA_BORDER
    elif edgedir==LEFT:
        x = collidingedge[0] + AREA_BORDER
    elif edgedir==RIGHT:
        x = collidingedge[0] - AREA_BORDER

    if edgename == RIGHT:
        x = origedge[0] + AREA_BORDER
    elif edgename == LEFT:
        x = origedge[0] - AREA_BORDER
    elif edgename == UP:
        y = origedge[0] - AREA_BORDER
    elif edgename == DOWN:
        y = origedge[0] + AREA_BORDER

    return (x,y)

def turn_after_collision(rectangles, lastpoint, edge, edgename, edgedir):
    # create border_edge = prolong edge in direction and shift it slightly away from edge   
    border = get_collision_edge(edge, edgename, edgedir, lastpoint)

    cpoints = []

    for r in rectangles:
        # potentional collision edge
        ce = get_edge(r, getopposite(edgedir))
        # check collision
        if (border[1]<ce[0]) and (ce[0]<border[2]) and (ce[1]<border[0]) and (border[0]<ce[2]):
            # collision          
            cpoints.append((get_collision_point(edge, edgename, edgedir, ce), ce, get_collision_trace(edgename, edgedir)))

    if not cpoints:
        return None
    
    if edgedir==LEFT:
        # find the most right point
        p = cpoints[0]
        for c in cpoints:
            if c[0] > p[0]:
                p = c
        return p
    elif edgedir==RIGHT:
        # find the most right point
        p = cpoints[0]
        for c in cpoints:
            if c[0] < p[0]:
                p = c
        return p
    elif edgedir==UP:
        # find the most down point
        p = cpoints[0]
        for c in cpoints:
            if c[1] > p[1]:
                p = c
        return p
    else:
        # find the most up point
        p = cpoints[0]
        for c in cpoints:
            if c[1] < p[1]:
                p = c
        return p

def continue_on(rectangles, edge, edgename, edgedir):
    """ check if there is a rectangle aligned with this one"""

    if edgedir==LEFT:
        x = edge[1] - AREA_GAP
    elif edgedir==RIGHT:
        x = edge[2] + AREA_GAP
    elif edgedir==UP:
        y = edge[1] - AREA_GAP
    else:
        y = edge[2] + AREA_GAP

    if edgename==LEFT or edgename==RIGHT:
        x = edge[0]
        checkedge = (y, x-AREA_GAP, x+AREA_GAP)
    else:
        y = edge[0]
        checkedge = (x, y-AREA_GAP, y+AREA_GAP)

    for r in rectangles:
        # potentional collision edge
        ce = get_edge(r, edgename)
        # check collision
        if (checkedge[1]<ce[0]) and (ce[0]<checkedge[2]) and (ce[1]<checkedge[0]) and (checkedge[0]<ce[2]):
            # collision, we should go along
            return (ce, edgename, edgedir)
    
    return None

def turn_on_corner(rectangles, edge, edgename, edgedir):
    rect = None
    for r in rectangles:
        if get_edge(r, edgename) == edge:
            rect = r
            break
    
    if edgedir==LEFT:
        x = edge[1] - AREA_BORDER
    elif edgedir==RIGHT:
        x = edge[2] + AREA_BORDER
    elif edgedir==UP:
        y = edge[1] - AREA_BORDER
    else:
        y = edge[2] + AREA_BORDER

    if edgename==LEFT:
        x = edge[0] - AREA_BORDER
    elif edgename==RIGHT:
        x = edge[0] + AREA_BORDER
    elif edgename==UP:
        y = edge[0] - AREA_BORDER
    else:
        y = edge[0] + AREA_BORDER
    
    return ((x,y), get_edge(rect, edgedir), edgedir, getopposite(edgename))

def find_start_rect(rectangles):
    d = 100000000
    start_rect = None
    for r in rectangles:
        dr = r[0][0]**2 + r[0][1]**2
        if(dr < d):
            d = dr
            start_rect = r
    return start_rect

def go2nextpoint(rectangles, lastpoint, edge, edgename, edgedir):
    collision = turn_after_collision(rectangles, lastpoint, edge, edgename, edgedir)
    # try to find collision with another rectangle
    if collision is not None:
        return (collision[0], collision[1], collision[2][0], collision[2][1])
    
    # no collision, check if there is adjacent rectangle
    adjacent = continue_on(rectangles, edge, edgename, edgedir)
    if adjacent is not None:
        return (None, adjacent[0], adjacent[1], adjacent[2])

    # no adjacent rectangle, turn around corner
    return turn_on_corner(rectangles, edge, edgename, edgedir)

def is_traverse(point, startpoint):
    if point is None:
        return True
    return ((point[0]-startpoint[0])**2 + (point[1]-startpoint[1])**2) > (AREA_GAP**2)

def find_traverse_points(area_rectangles):
    # find left UP rectangle
    start_rect = find_start_rect(area_rectangles)
    startpoint = (start_rect[0][0]-AREA_BORDER, start_rect[0][1]-AREA_BORDER)
    points = [startpoint]

    traverse = ([], get_edge(start_rect, UP), UP, RIGHT)
    while is_traverse(traverse[0], startpoint):
        if len(traverse[0])>0:
            p0 = points[len(points)-1]
            p = traverse[0]
            if(abs(p[0]-p0[0]) < REALLY_SMALL_GAP):
                p = (p0[0], p[1])
            if(abs(p[1]-p0[1]) < REALLY_SMALL_GAP):
                p = (p[0], p0[1])
            points.append(p)
        traverse = go2nextpoint(area_rectangles, points[-1], traverse[1], traverse[2], traverse[3])
    
    return points

def set_area_gap(x):
    # global AREA_BORDER
    # AREA_BORDER = x
    global AREA_GAP
    AREA_GAP = x
