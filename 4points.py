from sympy import Point3D, Line3D, Plane
from src.PyVMF import *
import os.path

path = "C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\my maps\python\displacement_editor_vmfs"
completeOpenName = os.path.join(path, "disp_prototype.vmf")
v = load_vmf(completeOpenName)

def planes_to_lines(planelist):
    all_lines = []
    for index1 in range(len(planelist)):
        intersec_lines = []
        for index2 in range(len(planelist)):
            if index2 != index1:
                plane = planelist[ index1 ]
                plane2 = planelist[ index2 ]
                intersec_line = plane.intersection( plane2 )
                if intersec_line != []:
                    intersec_lines.append(intersec_line[0])
        all_lines.append(intersec_lines)
    return all_lines

def lines_to_points(intersec_lines):
    intersec_points = set([])
    for index1 in range(len(intersec_lines)):
        for index2 in range(len(intersec_lines)):
            if index2 != index1:
                il = intersec_lines[ index1 ]
                il2 = intersec_lines[ index2 ]
                intersec_point = il.intersection(il2)
                if intersec_point != []:
                    intersec_points.add(intersec_point[0])
    return intersec_points

for solid in v.get_solids():
    planelist = []
    for side in solid.get_sides():
        pointlist = [Point3D(vert.x, vert.y, vert.z) for vert in side.get_vertices()]
        plane = Plane(*pointlist)
        planelist.append(plane)
    linelist = []
    for lines in planes_to_lines(planelist):
        linelist.append(list(lines_to_points(lines)))
