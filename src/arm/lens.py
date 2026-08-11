import numpy as np

class Lens:

    def __init__(self, lens_config):
        self.angle = lens_config["angle"]
        self.position = np.array(lens_config["position"])
        