import os
import pcbnew
import subprocess

KC_TO_MM = 1000000


def generate_kicad_pcb(netlist_filename, kinjector_filename, pcb_filename):
    subprocess.call([
        'kinet2pcb', '--nobackup', '--overwrite', '-i', netlist_filename, '-w'
    ])
    subprocess.call([
        'kinjector', '--nobackup', '--overwrite', '--from', kinjector_filename,
        '--to', pcb_filename
    ])


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


def draw_outline(pcb_filename):
    # TODO(miket): the PCB BB should be determined by keyboard grid * key width.
    # For example, 68-key layout is 17 x 4.75 or 323.85 x 90.4875. Then any
    # non-key components should fit in any empty spaces, or else explicitly
    # take up a new area dedicated to them.
    pcb = pcbnew.LoadBoard(pcb_filename)
    pcb.ComputeBoundingBox(False)
    bb = pcb.GetBoundingBox()
    l, t, r, b = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
    print("component bounding box is (%d %d) (%d %d)" % (l, t, r, b))
    print("h/w mm (%0.2f %0.2f)" % ((r - l) / KC_TO_MM, (b - t) / KC_TO_MM))

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

    layertable = {}

    numlayers = pcbnew.PCB_LAYER_ID_COUNT
    for i in range(numlayers):
        layertable[pcb.GetLayerName(i)] = i

    nets = pcb.GetNetsByName()

    powernets = []

    for name in ["GND"]:
        if (nets.has_key(name)):
            powernets.append((name, "F.Cu"))
            powernets.append((name, "B.Cu"))
            break

    for netname, layername in (powernets):
        net = nets.find(netname).value()[1]
        layer = layertable[layername]
        newarea = pcb.InsertArea(
            net.GetNet(), 0, layer, l, t, pcbnew.ZONE_EXPORT_VALUES
        )  # picked random name because ZONE_HATCH_STYLE_DIAGONAL_EDGE was missing

        newoutline = newarea.Outline()
        newoutline.Append(l, b)
        newoutline.Append(r, b)
        newoutline.Append(r, t)
        newarea.Hatch()

    filler = pcbnew.ZONE_FILLER(pcb)
    zones = pcb.Zones()
    filler.Fill(zones)

    pcbnew.SaveBoard(pcb_filename, pcb)
