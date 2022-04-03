from src.PyVMF import *
import numpy as np
from errors import NoTopTexture, TopTextureUsedForNonDisp, SideTextureUsedForNonDisp
from displacementClasses import preSideDisp, Stack, Top, Corner
from bezier import line

def top_vertices_returner( solid, z_value ):
    total_vertices = []
    for side in solid.get_sides():
        for vertex in side.get_vertices():
            total_vertices.append(vertex)
    new_total_vertices = []
    for vertex in total_vertices:
        if vertex not in new_total_vertices:
            new_total_vertices.append(vertex)
    top_vertices = [ vertex for vertex in new_total_vertices if vertex.z == z_value ]
    return top_vertices

def create_stack_neighbour_list( stack_list ):
    neighbour_list = []
    checking_list = [stack_list[0]]
    for index in range(1,len(stack_list)):
        stack1 = stack_list[index]
        for stack2 in checking_list:
            if stack1.start == stack2.end:
                neighbour_list.append([stack2, stack1])
            elif stack2.start == stack1.end:
                neighbour_list.append([stack1, stack2])
        checking_list.append(stack1)
    return neighbour_list

def create_stack_list( vmf, t_tex, v_tex):
    psd_list = []
    for solid in vmf.get_solids():
        for side in solid.get_displacement_sides():
            # print(side.material)
            # print(v_tex)
            if side.material == v_tex.upper():
                psd = preSideDisp(side, solid)
                psd_list.append(psd)
    psd_x_y_trackering_list = []
    psd_x_y_sortering_list = []
    for psd in psd_list:
        psd_x_y_tracker = (psd.start, psd.end)
        psd_x_y_tracker_inverse = (psd.end, psd.start)
        if (psd_x_y_tracker not in psd_x_y_trackering_list) and (psd_x_y_tracker_inverse not in psd_x_y_trackering_list):
            psd_x_y_trackering_list.append(psd_x_y_tracker)
            psd_x_y_sortering_list.append([psd])
        else:
            index = psd_x_y_trackering_list.index(psd_x_y_tracker)
            psd_x_y_sortering_list[index].append(psd)
    stack_list = []
    for pre_stack in psd_x_y_sortering_list:
        pre_stack.sort(reverse=True, key=(lambda psd: psd.max))
        top_psd = pre_stack[0] # after sorting this will be the top side disp
        solid = top_psd.solid
        if solid.get_texture_sides( t_tex ) == []:
            raise NoTopTexture()
        top_side = solid.get_texture_sides( t_tex )[0]
        z_value = top_side.get_vertices()[0].z
        td = Top( top_side, top_vertices_returner( solid, z_value ), z_value )
        stack = Stack( pre_stack, td )
        stack_list.append(stack)
    return stack_list

def create_corner(vmf, neighbour_triple, t_tex):
    for solid in vmf.get_solids():
        for side in solid.get_displacement_sides():
            if side.material == t_tex.upper():
                z_value = side.get_vertices()[0].z
                vertexList = top_vertices_returner( solid, z_value )
                x_y_vertexList = [(vertex.x, vertex.y) for vertex in vertexList]
                if neighbour_triple[1] in x_y_vertexList:
                    if (neighbour_triple[0] not in x_y_vertexList) and (neighbour_triple[2] not in x_y_vertexList):
                        corner = Corner(side, vertexList, z_value, neighbour_triple[1] )
                        return corner

def main_func(filepath, t_tex, v_tex, smooth_factor=1 ):
    vmf = load_vmf(filepath)
    stack_list = create_stack_list( vmf, t_tex, v_tex )
    neighbour_list = create_stack_neighbour_list( stack_list )

    for stack1, stack2 in neighbour_list:
        # constructing the points for the bezier curve
        smoothness = (5 + smooth_factor)/8 # smooth_factor takes values 0,1,2,3
        start = line( 1/2, stack1.start, stack1.end )
        mp1 =   line( smoothness, stack1.start, stack1.end )
        mp2 =   line( 1 - smoothness, stack2.start, stack2.end )
        end =   line( 1/2, stack2.start, stack2.end )
        points = [ start, mp1, mp2, end ]
        stack1.map_to_bezier( 0, points )
        stack2.map_to_bezier( 1, points )
        stack1.top.map_to_bezier( 0, points, stack1.start)
        stack2.top.map_to_bezier( 1, points, stack2.start)

        corner = create_corner(vmf, [stack1.start, stack1.end, stack2.end], t_tex)
        if corner:
            corner.map_to_bezier( points )

    vmf.export(filepath)
