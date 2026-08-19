
class ArmDirector:
    RIGHT, LEFT = 1, -1
    DOWN, UP = 1, -1


    def __init__(self, r=16, a=0, h=0, da=-6, dh=1, padding_pct=5, cover_target_pct=80, max_lost_frames=2):
        self.r0 = r
        self.a0 = a
        self.h0 = h

        self.r = r
        self.a = a
        self.h = h

        self.da0 = da
        self.dh0 = dh
        self.mumentm_a = da
        self.mumentm_h = 0

        self.padding_pct = padding_pct
        self.cover_target_pct = cover_target_pct
        self.max_lost_frames = max_lost_frames
        self.lost_streak = 0

        self.done = False

    def first_position(self):
        return self.r0, self.a0, self.h0

    def at_edge(self, axis, direction, corners, frame_size):
        dim = frame_size[axis]
        coords = [c[axis] for c in corners]

        padding = (dim - max(coords)) if direction == 1 else min(coords)

        return padding <= dim * (self.padding_pct / 100.0)

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

        for axis, direction, edge_label in edges:
            if self.at_edge(axis, direction, corners, frame_size):
                return edge_label

        return None

    def delta_position(self, edge_label):
        nudge_a, nudge_h = 0, 0
        if edge_label == 'right':
            if self.mumentm_a: # intended right
                # pushing up
                self.mumentm_a = 0
                self.mumentm_h = self.dh0
            else:
                nudge_a = -(0.5 * self.da0) # correcting

        elif edge_label == 'up':
            if self.mumentm_h: # intended up
                # pushing left
                self.mumentm_a = -self.da0
                self.mumentm_h = 0
            else:
                nudge_h = -(0.5 * self.dh0) # correcting

        elif edge_label == 'left':
            if self.mumentm_a: # intended left
                # pushing down
                self.mumentm_a = 0
                self.mumentm_h = -self.dh0
            else:
                nudge_a = (0.5 * self.da0) # correcting

        elif edge_label == 'down':
            if self.mumentm_h: # intended down
                # pushing right
                self.mumentm_a = self.da0
                self.mumentm_h = 0
            else:
                nudge_h = (0.5 * self.dh0) # correcting

        return self.mumentm_a + nudge_a, self.mumentm_h + nudge_h

            

    def next_position(self, found, corners, frame_size, cover):
        self.done = self.cover_target_pct <= cover
        if not self.done:
            edge_label = self.edge_hit(corners, frame_size)

            print(edge_label)

            if not found and not edge_label:
                self.lost_streak += 1
                if self.max_lost_frames <= self.lost_streak:
                    raise ValueError("Board should be visible - probably lighting issue")
            else:
                self.lost_streak = 0

            da, dh = self.delta_position(edge_label)
            self.a += da
            self.h += dh
        return self.r, self.a, self.h
