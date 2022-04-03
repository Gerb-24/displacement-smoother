from src.PyVMF import *
import numpy as np
from sympy import Point, Segment
from bezier import bezier, bezier_normal, line, plane

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
        if sp_index_in_orient() == None:
            return
        sp_index = sp_index_in_orient()
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
        # self.identify(start)
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

def point_updater( point, coord ):
    coord_norm = np.linalg.norm(coord.astype(float))
    if int(coord_norm) != 0:
        normalized_coord = coord/coord_norm
    else:
         normalized_coord = (0,0,0)
    point.set(Vertex(*normalized_coord), coord_norm)
