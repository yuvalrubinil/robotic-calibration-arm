
class ArmDirector:
    RIGHT, LEFT = 1, -1
    DOWN, UP = 1, -1

    def __init__(self, r=16, a=0, h=0, da=6, dh=1, padding_pct=5, cover_target_pct=80):
        self.r = r
        self.a = a
        self.h = h
        self.da = da
        self.dh = dh
        self.padding_pct = padding_pct
        self.cover_target_pct = cover_target_pct

        self.direction = self.RIGHT  # current horizontal sweep direction
        self.v_direction = self.DOWN  # current vertical step direction
        self._last_step = "a"  # which of da/dh produced the current a/h
        self._prev_a, self._prev_h = a, h
        self._prev_corners, self._prev_frame_size = None, None  # last found() frame, for diagnosing a miss

        self.done = False

    def first_target(self):
        return self.r, self.a, self.h

    def reached_edge(self, corners, frame_size, axis, direction):
        dim = frame_size[axis]
        coords = [c[axis] for c in corners]

        if direction == 1:
            padding = dim - max(coords)
        else:
            padding = min(coords)

        return padding <= dim * (self.padding_pct / 100)

    def reached_horizontal_edge(self, corners, frame_size):
        return self.reached_edge(corners, frame_size, axis=0, direction=self.direction)

    def reached_vertical_edge(self, corners, frame_size):
        return self.reached_edge(corners, frame_size, axis=1, direction=self.v_direction)

    def _edge_hit(self, corners, frame_size, axis):
        """Which edge (+1 max-side, -1 zero-side) along `axis` the given
        corners are within padding_pct of, or None if neither is close.
        """
        if not corners:
            return None
        if self.reached_edge(corners, frame_size, axis, direction=1):
            return 1
        if self.reached_edge(corners, frame_size, axis, direction=-1):
            return -1
        return None

    def next_target(self, found, corners, frame_size, cover):
        if self.done:
            return self.r, self.a, self.h

        if not found:
            self._handle_miss()
            return self.r, self.a, self.h

        if self.cover_target_pct <= cover:
            self.done = True
            return self.r, self.a, self.h

        self._prev_a, self._prev_h = self.a, self.h
        self._prev_corners, self._prev_frame_size = corners, frame_size

        if self.reached_horizontal_edge(corners, frame_size):
            # board is at the edge of this sweep: step to the next
            # row and reverse the horizontal direction
            if self.reached_vertical_edge(corners, frame_size):
                self.v_direction *= -1
            self.h += self.dh * self.v_direction
            self.direction *= -1
            self._last_step = "h"
        else:
            self.a += self.da * self.direction
            self._last_step = "a"

        return self.r, self.a, self.h

    def _handle_miss(self):
        """The board wasn't found after the last step. Diagnose which
        edge of the frame was actually crossed, using the last
        known-good corners (found=True) as a stand-in for what's
        happening now, since a miss gives us no corners to inspect
        directly:

        - the edge we were deliberately sweeping toward (e.g. the
          right edge while stepping `a` rightward): back off to the
          last known-good position and shrink that axis's step, to
          re-approach it more cautiously.
        - an orthogonal edge instead (e.g. the top edge while
          stepping `a`): fisheye distortion likely pushed us out of
          frame on an axis we weren't even trying to move on. Nudge
          that axis back away from its edge and retry the intended
          edge unchanged, rather than shrinking the intended step for
          a miss it didn't cause.
        - neither: unrelated tracking loss (e.g. glare). Fall back to
          the cautious backoff.
        """
        horizontal_hit = self._edge_hit(self._prev_corners, self._prev_frame_size, axis=0)
        vertical_hit = self._edge_hit(self._prev_corners, self._prev_frame_size, axis=1)

        if self._last_step == "a":
            intended_hit, intended_direction = horizontal_hit, self.direction
            stray_hit, stray_axis, stray_step = vertical_hit, "h", self.dh
        else:
            intended_hit, intended_direction = vertical_hit, self.v_direction
            stray_hit, stray_axis, stray_step = horizontal_hit, "a", self.da

        self.a, self.h = self._prev_a, self._prev_h

        if intended_hit == intended_direction:
            if self._last_step == "a":
                self.da /= 2
            else:
                self.dh /= 2
        elif stray_hit is not None:
            correction = (stray_step / 2) * stray_hit
            if stray_axis == "h":
                self.h -= correction
            else:
                self.a -= correction
        else:
            if self._last_step == "a":
                self.da /= 2
            else:
                self.dh /= 2


