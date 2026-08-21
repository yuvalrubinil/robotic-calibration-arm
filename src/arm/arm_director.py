class ArmDirector:

    def __init__(self, config):
        director_config = config["arm"]["director"]

        self.r0 = director_config["r"]
        self.a0 = director_config["a0"]
        self.h0 = director_config["h0"]
        self.ro0 = director_config["ro0"]

        self.r = self.r0
        self.a = self.a0
        self.h = self.h0
        self.ro = self.ro0

        self.da0 = director_config["da"]
        self.dh0 = director_config["dh"]
        self.mumentm_a = self.da0
        self.mumentm_h = 0
        self.target_edge = 'right'  # should be based on dh da (change later)

        self.final_rotations = director_config["final_rotations"]

        self.padding_pct = director_config["padding_pct"]
        self.cover_target_pct = director_config["cover_target_pct"]
        self.max_lost_frames = director_config["max_lost_frames"]
        self.lost_streak = 0

        self.steps = 0

        self.done = False

    def padding_ratio(self, edge, corners, frame_size):
        axis = 0 if edge == 'left' or edge == 'right' else 1
        direction = -1 if edge == 'left' or edge == 'up' else 1

        dim = frame_size[axis]
        coords = [c[axis] for c in corners]

        padding = (dim - max(coords)) if direction == 1 else min(coords)
        _padding_ratio = max(padding, 0) / dim

        return _padding_ratio

    def hit_edge(self, _padding_ratio):
        return _padding_ratio <= self.padding_pct / 100.0

    def edges_hit(self, corners, frame_size):
        if not corners:
            return None

        _edges_hit = []
        
        for edge in ['right', 'up', 'left', 'down']:
            _padding_ratio = self.padding_ratio(edge, corners, frame_size)
            if self.hit_edge(_padding_ratio):
                _edges_hit.append(edge)

        return _edges_hit

    def deceleration(self, _padding_ratio):
        return min(1.0, max(0.1,  _padding_ratio * 3.25))

    def set_mumentum(self, edge, _deceleration=1.0):
        if edge == 'up':
            self.target_edge = 'up'
            self.mumentm_a = 0
            self.mumentm_h = self.dh0 * _deceleration
        elif edge == 'left':
            self.target_edge = 'left'
            self.mumentm_a = -self.da0 * _deceleration
            self.mumentm_h = 0
        elif edge == 'down':
            self.target_edge = 'down'
            self.mumentm_a = 0
            self.mumentm_h = -self.dh0 * _deceleration
        elif edge == 'right':
            self.target_edge = 'right'
            self.mumentm_a = self.da0 * _deceleration
            self.mumentm_h = 0

    def delta_position(self, _edges_hit, corners, frame_size):
        nudge_a, nudge_h = 0, 0
        target_edge = self.target_edge  # snapshot: judge every edge hit this frame against the same target
        for edge_hit in _edges_hit:
            if edge_hit == 'right':
                if target_edge == 'right':
                    self.target_edge = 'up'
                else:
                    nudge_a -= (0.2 * self.da0) # correcting

            elif edge_hit == 'up':
                if target_edge == 'up':
                    self.target_edge = 'left'
                else:
                    nudge_h -= (0.2 * self.dh0) # correcting

            elif edge_hit == 'left':
                if target_edge == 'left':
                    self.target_edge = 'down'
                else:
                    nudge_a += (0.2 * self.da0) # correcting

            elif edge_hit == 'down':
                if target_edge == 'down':
                    self.target_edge ='right'
                else:
                    nudge_h += (0.2 * self.dh0) # correcting

        if corners:
            target_padding_ratio = self.padding_ratio(self.target_edge, corners, frame_size)
            self.set_mumentum(self.target_edge, self.deceleration(target_padding_ratio))

        da, dh = self.mumentm_a + nudge_a, self.mumentm_h + nudge_h
        if corners:
            print(self.padding_ratio('right', corners, frame_size))
            print(da)
        return da, dh



    def next_position(self, found, corners, frame_size, cover):
        if not self.steps:
            pass

        elif cover < self.cover_target_pct:
            edges = self.edges_hit(corners, frame_size)

            if not found and not edges:
                self.lost_streak += 1
                if self.max_lost_frames <= self.lost_streak:
                    raise ValueError("Board should be visible - probably lighting issue")
            else:
                self.lost_streak = 0

            da, dh = self.delta_position(edges or [], corners, frame_size)
            self.a += da
            self.h += dh

        elif self.steps < 40:
            self.a = self.a0
            self.h = self.h0
            self.ro = self.final_rotations.pop()

        else: 
            self.done = True

        self.steps += 1
        return self.r, self.a, self.h, self.ro
