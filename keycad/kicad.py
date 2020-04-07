import os
import pcbnew
import subprocess

Point = pcbnew.wxPoint

MM_TO_KC = 1000000


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


def draw_outline(pcb_filename,
                 left_mm,
                 top_mm,
                 width_mm,
                 height_mm,
                 usb_cutout_position=-1,
                 usb_cutout_width=-1,
                 modify_existing=True,
                 margin_mm=0,
                 corner_radius_mm=3):
    l = int(left_mm * MM_TO_KC)
    t = int(top_mm * MM_TO_KC)
    r = int(left_mm + width_mm) * MM_TO_KC
    b = int(top_mm + height_mm) * MM_TO_KC

    margin_kc = margin_mm * MM_TO_KC
    corner_rad_kc = corner_radius_mm * MM_TO_KC
    points = [
        (l - margin_kc, t - margin_kc),
        (r + margin_kc, t - margin_kc),
        (r + margin_kc, b + margin_kc),
        (l - margin_kc, b + margin_kc),
    ]

    if modify_existing:
        pcb = pcbnew.LoadBoard(pcb_filename)
    else:
        pcb = pcbnew.BOARD()

    if usb_cutout_position >= 0:
        usb_cutout_left = (usb_cutout_position -
                           usb_cutout_width / 2) * MM_TO_KC
        usb_cutout_right = (usb_cutout_position +
                            usb_cutout_width / 2) * MM_TO_KC
        draw_segment(pcb, points[0][0] + corner_rad_kc, points[0][1],
                     usb_cutout_left, points[0][1])
        draw_segment(pcb, usb_cutout_right, points[1][1],
                     points[1][0] - corner_rad_kc, points[1][1])
    else:
        draw_segment(pcb, points[0][0] + corner_rad_kc, points[0][1],
                     points[1][0] - corner_rad_kc, points[1][1])
    draw_segment(pcb, points[1][0], points[1][1] + corner_rad_kc, points[2][0],
                 points[2][1] - corner_rad_kc)
    draw_segment(pcb, points[2][0] - corner_rad_kc, points[2][1],
                 points[3][0] + corner_rad_kc, points[3][1])
    draw_segment(pcb, points[3][0], points[3][1] - corner_rad_kc, points[0][0],
                 points[0][1] + corner_rad_kc)

    draw_arc(pcb, points[0][0] + corner_rad_kc, points[0][1] + corner_rad_kc,
             points[0][0], points[0][1] + corner_rad_kc, 90)
    draw_arc(pcb, points[1][0] - corner_rad_kc, points[1][1] + corner_rad_kc,
             points[1][0] - corner_rad_kc, points[1][1], 90)
    draw_arc(pcb, points[2][0] - corner_rad_kc, points[2][1] - corner_rad_kc,
             points[2][0], points[2][1] - corner_rad_kc, 90)
    draw_arc(pcb, points[3][0] + corner_rad_kc, points[3][1] - corner_rad_kc,
             points[3][0] + corner_rad_kc, points[3][1], 90)

    pcbnew.SaveBoard(pcb_filename, pcb)

def draw_keepout(pcb_filename,
                 left_mm,
                 top_mm,
                 width_mm,
                 height_mm):
    l = int(left_mm * MM_TO_KC)
    t = int(top_mm * MM_TO_KC)
    r = int(left_mm + width_mm) * MM_TO_KC
    b = int(top_mm + height_mm) * MM_TO_KC

    pcb = pcbnew.LoadBoard(pcb_filename)
    layer = pcbnew.F_Cu
    # See below for where the 2 comes from
    area = pcb.InsertArea(-1, 0xffff, layer, 0, 0, 2)
    area.SetIsKeepout(True)
    area.SetDoNotAllowTracks(True)
    area.SetDoNotAllowVias(True)
    area.SetDoNotAllowCopperPour(True)
    outline = area.Outline()
    outline.NewOutline()
    outline.Append(l, t)
    outline.Append(r, t)
    outline.Append(r, b)
    outline.Append(l, b)

    pcbnew.SaveBoard(pcb_filename, pcb)

def pour_fills(pcb_filename):
    pcb = pcbnew.LoadBoard(pcb_filename)
    pcb.ComputeBoundingBox(False)
    bb = pcb.GetBoundingBox()
    l, t, r, b = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()

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
        # The number 2 is found in this code snippet:
        #
        # enum class ZONE_HATCH_STYLE
        # {
        #    NO_HATCH,
        #    DIAGONAL_FULL,
        #    DIAGONAL_EDGE
        # };
        # in the KiCad C++ source pcbnew/zone_settings.h.
        #
        # It seems that the version of the Python bindings
        # on current versions of KiCad don't have this enum.
        DIAGONAL_EDGE = 2
        newarea = pcb.InsertArea(net.GetNet(), 0, layer, l, t,
                                    DIAGONAL_EDGE)
        newoutline = newarea.Outline()
        newoutline.Append(l, b)
        newoutline.Append(r, b)
        newoutline.Append(r, t)
        newarea.Hatch()

        filler = pcbnew.ZONE_FILLER(pcb)
        zones = pcb.Zones()
        filler.Fill(zones)

    pcbnew.SaveBoard(pcb_filename, pcb)
