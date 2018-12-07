from math import *

class CoordinateTransform:

    def __init__(self, r_y=0.0):
        self.r_y = float(r_y) # angle of rotation about Y, degrees
        self.decimal_places = 6

    def set_theta(self, theta):
        self.r_y = theta

    def forward(self, x_real, y_real, z_real, theta=None, pitch=0.0, roll=0.0):
        XPOS = float(x_real)
        YPOS = float(y_real)
        ZPOS = float(z_real)

        if theta is None:
            theta = self.r_y

        KPOS = float(roll) * pi / 180.0
        PPOS = float(theta) * pi / 180.0
        OPOS = float(pitch) * pi / 180.0

        VIRTUAL_X = (XPOS * cos(KPOS) * cos(PPOS)) + (YPOS * (
        (cos(KPOS) * sin(PPOS) * sin(OPOS)) - (sin(KPOS) * cos(OPOS)))) + (
                    ZPOS * ((cos(KPOS) * sin(PPOS) * cos(OPOS)) + (
                    sin(KPOS) * sin(OPOS))))
        VIRTUAL_Y = (XPOS * sin(KPOS) * cos(PPOS)) + (YPOS * (
        (sin(KPOS) * sin(PPOS) * sin(OPOS)) + (cos(KPOS) * cos(OPOS)))) + (
                    ZPOS * ((sin(KPOS) * sin(PPOS) * cos(OPOS)) - (
                    cos(KPOS) * sin(OPOS))))
        VIRTUAL_Z = (XPOS * (-sin(PPOS))) + (YPOS * cos(PPOS) * sin(OPOS)) + (
        ZPOS * cos(PPOS) * cos(OPOS))

        x_lab = round(VIRTUAL_X, self.decimal_places)
        y_lab = round(VIRTUAL_Y, self.decimal_places)
        z_lab = round(VIRTUAL_Z, self.decimal_places)

        return x_lab, y_lab, z_lab

    def inverse(self, x_lab, y_lab, z_lab, theta=None, pitch=0.0, roll=0.0):
        VIRTUAL_X = x_lab
        VIRTUAL_Y = y_lab
        VIRTUAL_Z = z_lab

        if theta is None:
            theta = self.r_y

        KPOS = float(roll) * pi / 180.0
        PPOS = float(theta) * pi / 180.0
        OPOS = float(pitch) * pi / 180.0

        INVERSE_X = VIRTUAL_X * (cos(KPOS) * cos(PPOS)) + VIRTUAL_Y * (
        sin(KPOS) * cos(PPOS)) - VIRTUAL_Z * sin(PPOS)
        INVERSE_Y = VIRTUAL_X * (
        cos(KPOS) * sin(PPOS) * sin(OPOS) - sin(KPOS) * cos(
            OPOS)) + VIRTUAL_Y * (
        sin(KPOS) * sin(PPOS) * sin(OPOS) + cos(KPOS) * cos(
            OPOS)) + VIRTUAL_Z * cos(PPOS) * sin(OPOS)
        INVERSE_Z = VIRTUAL_X * (
        cos(KPOS) * sin(PPOS) * cos(OPOS) + sin(KPOS) * sin(
            OPOS)) + VIRTUAL_Y * (
        sin(KPOS) * sin(PPOS) * cos(OPOS) - cos(KPOS) * sin(
            OPOS)) + VIRTUAL_Z * cos(PPOS) * cos(OPOS)

        x_real = round(INVERSE_X, self.decimal_places)
        y_real = round(INVERSE_Y, self.decimal_places)
        z_real = round(INVERSE_Z, self.decimal_places)

        return x_real, y_real, z_real
