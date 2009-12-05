"""
Camera tracks a position, orientation and zoom level, and applies openGL
transforms so that subsequent renders are drawn at the correct place, size
and orientation on screen
"""
from __future__ import division
from math import sin, cos

from pyglet.gl import (
    glLoadIdentity, glMatrixMode, gluLookAt, gluOrtho2D,
    GL_MODELVIEW, GL_PROJECTION, glViewport
)

class Target(object):

    def __init__(self, camera):
        self.x, self.y = 0, 0
        self.scale = camera.scale
        self.angle = camera.angle

class Camera(object):
    def __init__(self, position=None, scale=None, angle=None):
        if position is None:
            position = (0, 0)
        self.x, self.y = position
        if scale is None:
            scale = 1
        self.scale = scale
        if angle is None:
            angle = 0
        self.angle = angle
        self.target = Target(self)
        self.desc_layer_scale = 512

    def zoom(self, factor):
        self.target.scale *= factor

    def pan(self, length, angle):
        self.target.x += length * sin(angle + self.angle)
        self.target.y += length * cos(angle + self.angle)

    def tilt(self, angle):
        self.target.angle += angle        
    
    def scr2map(self, sx, sy):
        gluProject( sx, 
                    sy, 
                    1, 
                    self.model_matrix,
                    win.proj_matrix,
                    win.view_matrix,
                    wx, 
                    wy, 
                    sz)


    def update(self):
        update_factor = 0.3
        self.x += (self.target.x - self.x) * update_factor
        self.y += (self.target.y - self.y) * update_factor
        self.scale += (self.target.scale - self.scale) * update_factor
        self.angle += (self.target.angle - self.angle) * update_factor


    def focus(self, width, height):
        "Set projection and modelview matrices ready for rendering"
        glViewport(0, 0, width, height)
        # Set projection matrix suitable for 2D rendering"
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        aspect = width/height
        gluOrtho2D(
                -self.scale * aspect,
                +self.scale * aspect,
                -self.scale,
                +self.scale)

        # Set modelview matrix to move, scale & rotate to camera position"
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            self.x, self.y, +1.0,
            self.x, self.y, -1.0,
            sin(self.angle), cos(self.angle), 0.0)

    def focus2(self, width, height):
        "Set projection and modelview matrices ready for rendering"

        # Set projection matrix suitable for 2D rendering"
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width/height
        gluOrtho2D(
                -self.desc_layer_scale * aspect ,
                +self.desc_layer_scale * aspect,
                -self.desc_layer_scale,
                +self.desc_layer_scale)
        
        # Set modelview matrix to move, scale & rotate to camera position"
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        diff = self.desc_layer_scale /self.scale
        gluLookAt(
            self.x * diff, self.y * diff, +1.0,
            self.x * diff, self.y * diff, -1.0,
            sin(self.angle), cos(self.angle), 0.0)

    def hud_mode(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, width, 0, height)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
