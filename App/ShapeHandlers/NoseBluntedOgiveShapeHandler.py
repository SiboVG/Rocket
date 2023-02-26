# ***************************************************************************
# *   Copyright (c) 2021-2023 David Carter <dcarter@davidcarter.ca>         *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************
"""Base class for drawing ogive nose cones"""

__title__ = "FreeCAD Ogive Nose Shape Handler"
__author__ = "David Carter"
__url__ = "https://www.davesrocketshop.com"
    
import FreeCAD
import Part
import math

from App.ShapeHandlers.NoseShapeHandler import NoseShapeHandler

class NoseBluntedOgiveShapeHandler(NoseShapeHandler):

    def getRho(self, radius, length):
        rho = (radius * radius + length * length) / (2.0 * radius)
        return rho
            
    def ogive_y(self, x, length, radius, rho):
        y = math.sqrt(rho * rho - math.pow(length - x, 2)) + radius - rho
        return y

    def innerMinor(self, length, radius, offset):
        rho = self.getRho(radius - offset, length - offset)

        inner_minor = self.ogive_y(length - offset, length, radius - offset, rho)
        return inner_minor

    def getXt(self, Xo, Yt, noseRadius):
        return Xo - math.sqrt((noseRadius * noseRadius) - (Yt * Yt))

    def getYt(self, rho, radius, noseRadius):
        return (noseRadius * (rho - radius)) / (rho - noseRadius)

    def getXo(self, rho, length, radius, noseRadius):
        return length - math.sqrt(math.pow(rho - noseRadius, 2) - math.pow(rho - radius, 2))

    def getXa(self, Xo, noseRadius):
        return Xo - noseRadius

    def getOgiveCurve(self, rho, length, vLength, radius, resolution, min = 0):
        points = []
        for i in range(0, resolution):
            
            x = float(i) * ((length - min) / float(resolution))
            y = self.ogive_y(x + (vLength - length), vLength, radius, rho)
            points.append(FreeCAD.Vector(min + x, y))

        points.append(FreeCAD.Vector(min + length, radius))
        return points
            
    def getBluntedLength(self, length, radius, noseRadius):

        min = length - noseRadius
        max = (-radius * length) / (noseRadius - radius)

        # Do a binary search to 0.0001 mm
        precision = 0.0001
        while abs(max - min) > precision:
            mid = (max + min) / 2.0
            rho = self.getRho(radius, mid)
            Xo = self.getXo(rho, mid, radius, noseRadius)
            Yt = self.getYt(rho, radius, noseRadius)
            Xt = self.getXt(Xo, Yt, noseRadius)
            Xa = self.getXa(Xo, noseRadius)

            if (length + Xa) > mid:
                min = mid
            else:
                max = mid

        return (rho, mid, Xt, Yt, Xo, Xa)

    def getMidArc(self, Yt, radius):
        y = Yt / 2.0
        x = radius - math.sqrt(radius * radius - y * y)
        return (x, y)

    def getCurve(self, length, radius, noseRadius, offset=0.0):
        (rho, vLength, Xt, Yt, Xo, Xa) = self.getBluntedLength(length, radius, noseRadius)

        midX, midY = self.getMidArc(Yt, noseRadius)

        self._offsetRadius = radius
        if offset > 0:
            self._offsetRadius = self.innerMinor(vLength, radius, offset)

        points = self.getOgiveCurve(rho, length - Xt + Xa, vLength, radius, self._resolution, Xt - Xa + offset)
        ogive = self.makeSpline(points)
        blunt = Part.Arc(
            # FreeCAD.Vector(Xt - Xa + offset, Yt),
            points[0], # Make sure we line up exactly
            FreeCAD.Vector(midX + offset, midY),
            FreeCAD.Vector(offset, 0.0)
        )

        curve = Part.Wire([blunt.toShape(), ogive.toShape()])

        return curve

    def drawSolid(self):
        outer_curve = self.getCurve(self._length, self._radius, self._noseRadius)

        edges = self.solidLines(outer_curve)
        return edges

    def drawSolidShoulder(self):
        outer_curve = self.getCurve(self._length, self._radius, self._noseRadius)

        edges = self.solidShoulderLines(outer_curve)
        return edges

    def drawHollow(self):
        outer_curve = self.getCurve(self._length, self._radius, self._noseRadius)
        inner_curve = self.getCurve(self._length - self._thickness, self._radius - self._thickness, self._noseRadius - self._thickness, self._thickness)

        edges = self.hollowLines(self._thickness, outer_curve, inner_curve)
        return edges

    def drawHollowShoulder(self):
        outer_curve = self.getCurve(self._length, self._radius, self._noseRadius)
        inner_curve = self.getCurve(self._length - 2.0 * self._thickness, self._radius - self._thickness, self._noseRadius - self._thickness, self._thickness)
        minor_y = inner_curve.Vertexes[-1].Point.y

        edges = self.hollowShoulderLines(self._thickness, minor_y, outer_curve, inner_curve)
        return edges

    def drawCapped(self):
        outer_curve = self.getCurve(self._length, self._radius, self._noseRadius)
        inner_curve = self.getCurve(self._length - 2.0 * self._thickness, self._radius - self._thickness, self._noseRadius - self._thickness, self._thickness)
        minor_y = inner_curve.Vertexes[-1].Point.y

        edges = self.cappedLines(self._thickness, minor_y, outer_curve, inner_curve)
        return edges

    def drawCappedShoulder(self):
        outer_curve = self.getCurve(self._length, self._radius, self._noseRadius)
        inner_curve = self.getCurve(self._length - 2.0 * self._thickness, self._radius - self._thickness, self._noseRadius - self._thickness, self._thickness)
        minor_y = inner_curve.Vertexes[-1].Point.y

        edges = self.cappedShoulderLines(self._thickness, minor_y, outer_curve, inner_curve)
        return edges
