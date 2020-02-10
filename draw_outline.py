#!/usr/bin/env python3

import pcbnew

KC_TO_MM = 1000000

FILENAME = "keycad.kicad_pcb"
pcb = pcbnew.LoadBoard(FILENAME)
pcb.ComputeBoundingBox(False)
print(pcb)
l, t, r, b = pcb.GetBoundingBox().GetLeft(), pcb.GetBoundingBox().GetTop(), pcb.GetBoundingBox().GetRight(), pcb.GetBoundingBox().GetBottom()
print(l, t, r, b)


def draw_segment(board, x1, y1, x2, y2):
    layer=pcbnew.Edge_Cuts
    thickness=0.15*pcbnew.IU_PER_MM
    ds=pcbnew.DRAWSEGMENT(board)
    ds.SetLayer(layer)
    ds.SetWidth(max(1,int(thickness)))
    board.Add(ds)
    ds.SetStart(pcbnew.wxPoint(x1, y1))
    ds.SetEnd(pcbnew.wxPoint(x2, y2))

def draw_arc(board, cx, cy, sx, sy, a):
    layer=pcbnew.Edge_Cuts
    thickness=0.15*pcbnew.IU_PER_MM
    ds=pcbnew.DRAWSEGMENT(board)
    ds.SetLayer(layer)
    ds.SetWidth(max(1,int(thickness)))
    board.Add(ds)
    ds.SetShape(pcbnew.S_ARC)
    ds.SetCenter(pcbnew.wxPoint(cx, cy))
    ds.SetArcStart(pcbnew.wxPoint(sx, sy))
    ds.SetAngle(a * 10)

# https://docs.kicad-pcb.org/doxygen-python/FootprintWizardBase_8py_source.html
class Drawing:
    def __init__(self, board):
        self.__board = board

    def TransformPoint(self, x, y, mat=None):
            """!
            Return a point (x, y) transformed by the given matrix, or if
            that is not given, the drawing context transform
    
            @param x: the x co-ordinate of the point to transform
            @param y: the y co-ordinate of the point to transform
            @param mat: the transform matrix to use or None to use the current DC's
            @return: the transformed point as a wxPoint
            """
    
            if not mat:
                mat = [1, 0, 0, 0, 1, 0]
    
            return pcbnew.wxPoint(x * mat[0] + y * mat[1] + mat[2],
                                x * mat[3] + y * mat[4] + mat[5])

    def Line(self, x1, y1, x2, y2):
        layer=pcbnew.Edge_Cuts
        thickness=0.15*pcbnew.IU_PER_MM
        ds=pcbnew.DRAWSEGMENT(self.__board)
        self.__board.Add(ds)
        ds.SetStart(pcbnew.wxPoint(x1, y1))
        ds.SetEnd(pcbnew.wxPoint(x2, y2))
        ds.SetLayer(layer)
        ds.SetWidth(max(1,int(thickness)))

    def Arc(self, cx, cy, sx, sy, a):
        """!
        Draw an arc based on centre, start and angle

        The transform matrix is applied

        Note that this won't work properly if the result is not a
        circular arc (e.g. a horizontal scale)

        @param cx: the x co-ordinate of the arc centre
        @param cy: the y co-ordinate of the arc centre
        @param sx: the x co-ordinate of the arc start point
        @param sy: the y co-ordinate of the arc start point
        @param a: the arc's central angle (in deci-degrees)
        """
        layer=pcbnew.Edge_Cuts
        circle = pcbnew.DRAWSEGMENT(self.__board)
        circle.SetShape(pcbnew.S_CIRCLE)
        circle.SetCenter(pcbnew.wxPoint(cx, cy))
        start_coord = pcbnew.wxPoint(sx, sy)
        circle.SetArcStart(start_coord)
        circle.SetLayer(layer)
        self._obj = circle
    
    def HLine(self, x, y, l):
        """!
        Draw a horizontal line from (x,y), rightwards

        @param x: line start x co-ordinate
        @param y: line start y co-ordinate
        @param l: line length
        """
        self.Line(x, y, x + l, y)

    def VLine(self, x, y, l):
        """!
        Draw a vertical line from (x1,y1), downwards

        @param x: line start x co-ordinate
        @param y: line start y co-ordinate
        @param l: line length
        """
        self.Line(x, y, x, y + l)

    def RoundedBox(self, x, y, w, h, rad):
        """!
        Draw a box with rounded corners (i.e. a 90-degree circular arc)

        :param x: the x co-ordinate of the box's centre
        :param y: the y co-ordinate of the box's centre
        :param w: the width of the box
        :param h: the height of the box
        :param rad: the radius of the corner rounds
        """

        x_inner = w - rad * 2
        y_inner = h - rad * 2

        x_left = x - w / 2
        y_top = y - h / 2

        # Draw straight sections
        self.HLine(x_left + rad, y_top, x_inner)
        self.HLine(x_left + rad, -y_top, x_inner)

        self.VLine(x_left, y_top + rad, y_inner)
        self.VLine(-x_left, y_top + rad, y_inner)

        # corner arcs
        ninety_deg = 90 * 10  # deci-degs
        cx = x - w / 2 + rad
        cy = y - h / 2 + rad

        # top left
        self.Arc(+cx, +cy, +x_left, +cy, +ninety_deg)
        self.Arc(-cx, +cy, -x_left, +cy, -ninety_deg)
        self.Arc(+cx, -cy, +x_left, -cy, -ninety_deg)
        self.Arc(-cx, -cy, -x_left, -cy, +ninety_deg)

drawing = Drawing(pcb)
MARGIN = 5 * KC_TO_MM
CORNER_RADIUS = 3 * KC_TO_MM
POINTS = [
    (l - MARGIN, t - MARGIN),
    (r + MARGIN, t - MARGIN),
    (r + MARGIN, b + MARGIN),
    (l - MARGIN, b + MARGIN),
]
draw_segment(pcb, POINTS[0][0] + CORNER_RADIUS, POINTS[0][1], POINTS[1][0] - CORNER_RADIUS, POINTS[1][1])
draw_segment(pcb, POINTS[1][0], POINTS[1][1] + CORNER_RADIUS, POINTS[2][0], POINTS[2][1] - CORNER_RADIUS)
draw_segment(pcb, POINTS[2][0] - CORNER_RADIUS, POINTS[2][1], POINTS[3][0] + CORNER_RADIUS, POINTS[3][1])
draw_segment(pcb, POINTS[3][0], POINTS[3][1] - CORNER_RADIUS, POINTS[0][0], POINTS[0][1] + CORNER_RADIUS)

draw_arc(pcb, POINTS[0][0] + CORNER_RADIUS, POINTS[0][1] + CORNER_RADIUS, POINTS[0][0], POINTS[0][1] + CORNER_RADIUS, 90)
draw_arc(pcb, POINTS[1][0] - CORNER_RADIUS, POINTS[1][1] + CORNER_RADIUS, POINTS[1][0] - CORNER_RADIUS, POINTS[1][1], 90)
draw_arc(pcb, POINTS[2][0] - CORNER_RADIUS, POINTS[2][1] - CORNER_RADIUS, POINTS[2][0], POINTS[2][1] - CORNER_RADIUS, 90)
draw_arc(pcb, POINTS[3][0] + CORNER_RADIUS, POINTS[3][1] - CORNER_RADIUS, POINTS[3][0] + CORNER_RADIUS, POINTS[3][1], 90)

pcbnew.SaveBoard(FILENAME, pcb)