from src.PyVMF import *
import numpy as np
from sympy import Point, Segment
from bezier import bezier, bezier_normal, line, plane
from errors import NoTopTexture, TopTextureUsedForNonDisp, SideTextureUsedForNonDisp

class preSideDisp:
    def __init__(self, side, solid):
        self.side = side
        self.solid = solid
        if side.get_displacement == None:
            raise SideTextureUsedForNonDisp()
        self.max, self.min = self.min_max_creator()
        self.start, self.end = self.start_end_creator()

        self.matrix = side.get_displacement().matrix

    def identify( self ):
        for i in range(self.matrix.size):
            for j in range(self.matrix.size):
                p = self.matrix.get(i, j)
                if (i,j) == (0,0):
                    p.set(Vertex(0,0,1), 1*128)

    def min_max_creator(self):
        vertexList = self.side.get_vertices()
        z_list = [vertex.z for vertex in vertexList]
        return max(z_list), min(z_list)

    def start_end_creator(self):
        vertexList = self.side.get_vertices()
        startposition = self.side.get_displacement().startposition

        x_y_list = [(vertex.x,vertex.y) for vertex in vertexList]
        new_x_y_list = []
        for elem in x_y_list:
            if elem not in new_x_y_list:
                new_x_y_list.append(elem)
        if startposition.x == new_x_y_list[0][0] and startposition.y == new_x_y_list[0][1]:
            start = new_x_y_list[0]
            end = new_x_y_list[1]
            return start, end
        else:
            start = new_x_y_list[1]
            end = new_x_y_list[0]
            return start, end

class Stack:
    def __init__(self, psd_list, top):
        self.top = top
        self.psd_list = self.psd_list_initializer(psd_list)
        self.start, self.end = psd_list[0].start, psd_list[0].end

    def psd_list_initializer( self, psd_list ):
        ''' Before we initialize the psd_list, we want to fix up the startingpoints, so that they are easier to work with '''

        def change_sp_checker( psd ):
            pl = self.top.pointlist
            for index in range(len(pl)):
                if (pl[index].x, pl[index].y) == psd.start:
                    if (pl[(index - 1)%4].x, pl[(index-1)%4].y) == psd.end:
                        return True
            return False

        for psd in psd_list:
            if change_sp_checker( psd ):
                psd.side.get_displacement().startposition = Vertex(*psd.end, psd.min)
                psd.start, psd.end = psd.end, psd.start
        return psd_list

    def map_to_bezier( self, index, points ):
        for psd in self.psd_list:
            power = psd.matrix.size-1
            if power == 8:
                ( start_val, end_val ) = ( 4,9 ) if index == 0 else ( 0, 5 )
                bez_factor = -4 if index == 0 else 4
            elif power == 4:
                ( start_val, end_val ) = ( 2, 5 ) if index == 0 else ( 0, 3 )
                bez_factor = -2 if index == 0 else 2
            for i in range(psd.matrix.size):
                if i in range(start_val, end_val):
                    for j in range(psd.matrix.size):
                        p = psd.matrix.get(i, j)
                        p_coord = np.array(
                            [
                            psd.start[0]*(1-i/power) + psd.end[0]*(i/power),
                            psd.start[1]*(1-i/power) + psd.end[1]*(i/power),
                            psd.min*(1-j/power) + psd.max*(j/power),
                            ]
                        )
                        bez_coord = np.array(
                            [
                            *bezier((i + bez_factor)/power, points),
                            psd.min*(1-j/power) + psd.max*(j/power)
                            ])
                        new_coord = bez_coord - p_coord
                        # new_coord = new_coord + bez_normal_coord(k, j, factor)
                        point_updater(p, new_coord)

class Top:
    def __init__(self, side, pointlist, z_value):

        def pointlist_to_orient(pointlist, sp):
            def pointlist_to_segments(pointlist):
                pre_segment_list = []
                for index1 in range(len(pointlist)):
                    for index2 in range(len(pointlist)):
                        if index2 > index1:
                            point1 = pointlist[index1]
                            point2 = pointlist[index2]
                            pre_segment_list.append(Segment(point1, point2))
                return pre_segment_list

            def diag_returner(pre_segment_list):
                checked_segments = []
                for index1 in range(len(pre_segment_list)):
                    segment = pre_segment_list[index1]
                    for index2 in range(len(checked_segments)):
                        segment2 = checked_segments[index2]
                        intersec = segment.intersection(segment2)
                        if intersec != []:
                            if intersec[0] != segment.p1 and intersec[0] != segment.p2:
                                return segment, segment2
                    checked_segments.append(segment)

            def diag_to_orient(diags, sp):
                def get_angle(v1, sp_ar, v2):
                    v1 = v1 - sp_ar
                    v2 = v2 - sp_ar
                    v1 = v1.astype(float)
                    v2 = v2.astype(float)
                    angle = np.arctan2(np.cross(v1, v2), np.dot(v1, v2))
                    return angle

                [main_diag, other_diag]  = diags if (diags[0].p1 == sp or diags[0].p2 == sp) else [diags[1], diags[0]]
                main_diag = Segment(sp, main_diag.p1) if main_diag.p1 != sp else main_diag
                sp_ar = np.array(sp)
                v1 = np.array(main_diag.p2)
                v2 = np.array(other_diag.p1)
                if get_angle(v1, sp_ar, v2) < 0:
                    return [main_diag.p1, other_diag.p1, main_diag.p2, other_diag.p2]
                else:
                    return [main_diag.p1, other_diag.p2, main_diag.p2, other_diag.p1]

            segments = pointlist_to_segments( pointlist )
            diags = diag_returner(segments)
            orient = diag_to_orient(diags, sp)

            return orient

        self.z = z_value
        self.side = side
        if side.get_displacement() == None:
            raise TopTextureUsedForNonDisp()
        self.matrix = side.get_displacement().matrix
        self.startposition = side.get_displacement().startposition

        sympy_pointlist = [Point(point.x, point.y) for point in pointlist]
        sympy_startposition = Point(self.startposition.x, self.startposition.y )

        self.orient = pointlist_to_orient(sympy_pointlist, sympy_startposition)
        self.pointlist = [Vertex(point.x, point.y, self.z) for point in self.orient]

    def orient_changer(self, start):
        def sp_index_in_orient():
            for o_index in range(len(self.orient)):
                if self.orient[ o_index ].x == start[0] and self.orient[ o_index ].y == start[1]:
                    return o_index
        sp_index = sp_index_in_orient()
        if sp_index != 1:
            new_orient = []
            for o_index in range(len(self.orient)):
                new_orient.append(self.orient[(o_index+sp_index-1)%4])
            self.orient = new_orient
            self.side.get_displacement().startposition = Vertex(*self.orient[0], self.z)
            self.startposition = Vertex(*self.orient[0], self.z)

    def set_to_zero(self):
        for i in range(self.matrix.size):
            for j in range(self.matrix.size):
                p = self.matrix.get(i, j)
                coord = np.array( [*plane(i/8, j/8, self.orient), self.z])
                point_updater( p, coord )

    def identify( self, start ):
        # self.orient_changer( start )
        for i in range(self.matrix.size):
            for j in range(self.matrix.size):
                p = self.matrix.get(i, j)
                if (i,j) == (0,0):
                    p.set(Vertex(0,0,1), 1*128)
                elif (i,j) == (8,0):
                    p.set(Vertex(0,0,1), 2*128)
                elif (i,j) == (8,8):
                    p.set(Vertex(0,0,1), 3*128)
                elif (i,j) == (0,8):
                    p.set(Vertex(0,0,1), 4*128)


    def map_to_bezier( self, index, points, start):
        self.orient_changer(start)

        power = self.matrix.size-1
        if power == 8:
            ( start_val, end_val ) = ( 4,9 ) if index == 0 else ( 0, 5 )
            bez_factor = -4 if index == 0 else 4
        elif power == 4:
            ( start_val, end_val ) = ( 2, 5 ) if index == 0 else ( 0, 3 )
            bez_factor = -2 if index == 0 else 2

        for j in range(self.matrix.size):
            if j in range(start_val, end_val):
                for i in range(self.matrix.size):
                    p = self.matrix.get(i, j)
                    p_coord = np.array( [*plane(i/power, j/power, self.orient), self.z])
                    align_coord = np.array( [*plane(0, j/power, self.orient), self.z])
                    bez_coord =(1-i/power)*align_coord + (i/power) * np.array(
                        [
                        *bezier((j + bez_factor)/power, points),
                        self.z
                        ])
                    new_coord = bez_coord - p_coord
                    # new_coord = new_coord + bez_normal_coord(k, j, factor)
                    point_updater(p, new_coord)

class Corner:
    def __init__(self, side, pointlist, z_value, start):
        def pointlist_to_orient(pointlist, sp):
            def pointlist_to_segments(pointlist):
                pre_segment_list = []
                for index1 in range(len(pointlist)):
                    for index2 in range(len(pointlist)):
                        if index2 > index1:
                            point1 = pointlist[index1]
                            point2 = pointlist[index2]
                            pre_segment_list.append(Segment(point1, point2))
                return pre_segment_list

            def diag_returner(pre_segment_list):
                checked_segments = []
                for index1 in range(len(pre_segment_list)):
                    segment = pre_segment_list[index1]
                    for index2 in range(len(checked_segments)):
                        segment2 = checked_segments[index2]
                        intersec = segment.intersection(segment2)
                        if intersec != []:
                            if intersec[0] != segment.p1 and intersec[0] != segment.p2:
                                return segment, segment2
                    checked_segments.append(segment)

            def diag_to_orient(diags, sp):
                def get_angle(v1, sp_ar, v2):
                    v1 = v1 - sp_ar
                    v2 = v2 - sp_ar
                    v1 = v1.astype(float)
                    v2 = v2.astype(float)
                    angle = np.arctan2(np.cross(v1, v2), np.dot(v1, v2))
                    return angle

                [main_diag, other_diag]  = diags if (diags[0].p1 == sp or diags[0].p2 == sp) else [diags[1], diags[0]]
                main_diag = Segment(sp, main_diag.p1) if main_diag.p1 != sp else main_diag
                sp_ar = np.array(sp)
                v1 = np.array(main_diag.p2)
                v2 = np.array(other_diag.p1)
                if get_angle(v1, sp_ar, v2) < 0:
                    return [main_diag.p1, other_diag.p1, main_diag.p2, other_diag.p2]
                else:
                    return [main_diag.p1, other_diag.p2, main_diag.p2, other_diag.p1]

            segments = pointlist_to_segments( pointlist )
            diags = diag_returner(segments)
            orient = diag_to_orient(diags, sp)

            return orient
        self.start = start
        self.z = z_value
        self.side = side
        if side.get_displacement() == None:
            raise TopTextureUsedForNonDisp()
        self.matrix = side.get_displacement().matrix
        self.startposition = side.get_displacement().startposition

        sympy_pointlist = [Point(point.x, point.y) for point in pointlist]
        sympy_startposition = Point(self.startposition.x, self.startposition.y )

        self.orient = pointlist_to_orient(sympy_pointlist, sympy_startposition)
        self.pointlist = [Vertex(point.x, point.y, self.z) for point in self.orient]

        self.orient_changer()

    def orient_changer(self):
        def sp_index_in_orient():
            for o_index in range(len(self.orient)):
                if self.orient[ o_index ].x == self.start[0] and self.orient[ o_index ].y == self.start[1]:
                    return o_index
        sp_index = sp_index_in_orient()
        if sp_index != 2:
            new_orient = []
            for o_index in range(len(self.orient)):
                new_orient.append(self.orient[(o_index+sp_index-2)%4])
            self.orient = new_orient
            self.side.get_displacement().startposition = Vertex(*self.orient[0], self.z)
            self.startposition = Vertex(*self.orient[0], self.z)

    def map_to_bezier( self, points):
        power = self.matrix.size - 1
        for i in range(self.matrix.size):
            for j in range(self.matrix.size):
                p = self.matrix.get(i, j)
                p_coord = np.array( [*plane(i/power, j/power, self.orient), self.z])
                bez_coord = tuple(bezier(1/2, points))
                new_orient = [self.orient[0], self.orient[1], bez_coord, self.orient[3]]

                new_coord = np.array( [*plane(i/power, j/power, new_orient), self.z])
                new_coord = new_coord - p_coord
                # new_coord = new_coord + bez_normal_coord(k, j, factor)
                point_updater(p, new_coord)

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

def bez_normal_coord(k, j, factor):
    bez_norm_coord = np.array(
        [
        bezier_normal(k/8, points)[0],
        bezier_normal(k/8, points)[1],
        0
        ])
    bez_norm_coord_norm = np.linalg.norm(bez_norm_coord)
    if int(bez_norm_coord_norm) != 0:
        bez_norm_coord_normalized= bez_norm_coord/bez_norm_coord_norm
    else:
         bez_norm_coord_normalized = np.array([0,0,0])
    new_bez_normal =  bez_norm_coord_normalized*factor*(j/8)
    return new_bez_normal

def point_updater( point, coord ):
    coord_norm = np.linalg.norm(coord.astype(float))
    if int(coord_norm) != 0:
        normalized_coord = coord/coord_norm
    else:
         normalized_coord = (0,0,0)
    point.set(Vertex(*normalized_coord), coord_norm)

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
