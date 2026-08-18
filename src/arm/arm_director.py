
class ArmDirector:
    RIGHT, LEFT = 1, -1
    DOWN, UP = 1, -1

    # edge label -> (axis to move on when heading toward that edge, sign of that move)
    _EDGE_AXIS = {
        'right': ('a', RIGHT),
        'left':  ('a', LEFT),
        'down':  ('h', DOWN),
        'up':    ('h', UP),
    }

    def __init__(self, r=16, a=0, h=0, da=6, dh=1, padding_pct=5, cover_target_pct=80):
        self.r0 = r
        self.a0 = a
        self.h0 = h
        self.r = r
        self.a = a
        self.h = h

        self.da0 = da
        self.dh0 = dh
        self.da = da
        self.dh = 0

        self.padding_pct = padding_pct
        self.cover_target_pct = cover_target_pct

        self.prev_a, self.prev_h = a, h
        self.prev_corners, self.prev_frame_size = None, None  # last found() frame, for diagnosing a miss

        self.last_found_a, self.last_found_h = a, h  # last position found() was True at
        self._search_edge = None   # edge label we're currently binary-searching toward
        self._search_step = None   # current (shrinking) step of that search

        self.done = False

    def first_position(self):
        return self.r0, self.a0, self.h0

    def edge_hit(self, corners, frame_size):
        if not corners:
            return None

        # edge = (axis, direction, label)
        edges = [
            (0,  1, 'right'),
            (0, -1, 'left'),
            (1,  1, 'down'),
            (1, -1, 'up'),
        ]

        threshold = self.padding_pct / 100.0

        for axis, direction, edge_label in edges:
            dim = frame_size[axis]
            coords = [c[axis] for c in corners]
            
            padding = (dim - max(coords)) if direction == 1 else min(coords)

            if padding <= dim * threshold:
                return edge_label

        return None

    def reposition(self, edge_label):
        axis, sign = self._EDGE_AXIS[edge_label]
        base_step = self.da0 if axis == 'a' else self.dh0

        if edge_label == self._search_edge:
            self._search_step /= 2
        else:
            self._search_edge = edge_label
            self._search_step = base_step

        offset = sign * self._search_step
        self.a = self.last_found_a + (offset if axis == 'a' else 0)
        self.h = self.last_found_h + (offset if axis == 'h' else 0)



    def next_position(self, found, corners, frame_size, cover):
        if found:
            self.last_found_a, self.last_found_h = self.a, self.h
            self._search_edge, self._search_step = None, None

        if self.done:
            return self.r, self.a, self.h

        if not found:
            edge_label = self.edge_hit(corners, frame_size)
            if not edge_label:
                raise ValueError("Board should be visible - probably lighting issue")

            self.prev_a, self.prev_h = self.a, self.h
            self.reposition(edge_label)

            return self.r, self.a, self.h

        


