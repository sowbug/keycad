#!/usr/bin/env python3

import pcbnew

KC_TO_MM = 1000000

FILENAME = "keycad.kicad_pcb"
pcb = pcbnew.LoadBoard(FILENAME)
pcb.ComputeBoundingBox(False)
l, t, r, b = pcb.GetBoundingBox().GetLeft(), pcb.GetBoundingBox().GetTop(
), pcb.GetBoundingBox().GetRight(), pcb.GetBoundingBox().GetBottom()


def draw_segment(board, x1, y1, x2, y2):
    layer = pcbnew.Edge_Cuts
    thickness = 0.15 * pcbnew.IU_PER_MM
    ds = pcbnew.DRAWSEGMENT(board)
    ds.SetLayer(layer)
    ds.SetWidth(max(1, int(thickness)))
    board.Add(ds)
    ds.SetStart(pcbnew.wxPoint(x1, y1))
    ds.SetEnd(pcbnew.wxPoint(x2, y2))


def draw_arc(board, cx, cy, sx, sy, a):
    layer = pcbnew.Edge_Cuts
    thickness = 0.15 * pcbnew.IU_PER_MM
    ds = pcbnew.DRAWSEGMENT(board)
    ds.SetLayer(layer)
    ds.SetWidth(max(1, int(thickness)))
    board.Add(ds)
    ds.SetShape(pcbnew.S_ARC)
    ds.SetCenter(pcbnew.wxPoint(cx, cy))
    ds.SetArcStart(pcbnew.wxPoint(sx, sy))
    ds.SetAngle(a * 10)


MARGIN = 0 * KC_TO_MM
CORNER_RADIUS = 3 * KC_TO_MM
POINTS = [
    (l - MARGIN, t - MARGIN),
    (r + MARGIN, t - MARGIN),
    (r + MARGIN, b + MARGIN),
    (l - MARGIN, b + MARGIN),
]
draw_segment(pcb, POINTS[0][0] + CORNER_RADIUS, POINTS[0][1],
             POINTS[1][0] - CORNER_RADIUS, POINTS[1][1])
draw_segment(pcb, POINTS[1][0], POINTS[1][1] + CORNER_RADIUS, POINTS[2][0],
             POINTS[2][1] - CORNER_RADIUS)
draw_segment(pcb, POINTS[2][0] - CORNER_RADIUS, POINTS[2][1],
             POINTS[3][0] + CORNER_RADIUS, POINTS[3][1])
draw_segment(pcb, POINTS[3][0], POINTS[3][1] - CORNER_RADIUS, POINTS[0][0],
             POINTS[0][1] + CORNER_RADIUS)

draw_arc(pcb, POINTS[0][0] + CORNER_RADIUS, POINTS[0][1] + CORNER_RADIUS,
         POINTS[0][0], POINTS[0][1] + CORNER_RADIUS, 90)
draw_arc(pcb, POINTS[1][0] - CORNER_RADIUS, POINTS[1][1] + CORNER_RADIUS,
         POINTS[1][0] - CORNER_RADIUS, POINTS[1][1], 90)
draw_arc(pcb, POINTS[2][0] - CORNER_RADIUS, POINTS[2][1] - CORNER_RADIUS,
         POINTS[2][0], POINTS[2][1] - CORNER_RADIUS, 90)
draw_arc(pcb, POINTS[3][0] + CORNER_RADIUS, POINTS[3][1] - CORNER_RADIUS,
         POINTS[3][0] + CORNER_RADIUS, POINTS[3][1], 90)

pcbnew.SaveBoard(FILENAME, pcb)