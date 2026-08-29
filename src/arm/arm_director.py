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
        self.target_edge = 'right'  

        self.rotations = director_config["rotations"]
        self.rotation_idx = 0

        self.padding_pct = director_config["padding_pct"]
        self.lost_streak = 0
        self.used_last_resort = False

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
        _edges_hit = []

        if corners:
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
        target_edge = self.target_edge 
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
        return da, dh

    def last_resort(self):  
        if self.used_last_resort:
            self.used_last_resort = False
            raise ValueError("Board should be visible - probably lighting issue")
        
        self.used_last_resort = True

        if self.target_edge == 'right':
            self.a -= (0.2 * self.da0) # correcting
        elif self.target_edge == 'up':
            self.h -= (0.2 * self.dh0) # correcting
        elif self.target_edge == 'left':
            self.a += (0.2 * self.da0) # correcting
        elif self.target_edge == 'down':
            self.h += (0.2 * self.dh0) # correcting

        self.lost_streak = 0    

    def next_position(self, found, corners, frame_size):
        self.ro = self.rotations[self.rotation_idx % len(self.rotations)]
        self.rotation_idx += 1

        edges = self.edges_hit(corners, frame_size)

        if not found and not edges:
            self.lost_streak += 1
            if len(self.rotations) < self.lost_streak:
                self.last_resort()
        else:
            self.lost_streak = 0
            da, dh = self.delta_position(edges, corners, frame_size)
            self.a += da
            self.h += dh

        return self.r, self.a, self.h, self.ro
