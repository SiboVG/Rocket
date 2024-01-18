# ***************************************************************************
# *   Copyright (c) 2021-2024 David Carter <dcarter@davidcarter.ca>         *
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
"""Provides support for importing Open Rocket files."""

__title__ = "FreeCAD Open Rocket Importer"
__author__ = "David Carter"
__url__ = "https://www.davesrocketshop.com"

import FreeCAD

from Rocket.Importer.OpenRocket.ComponentElement import ExternalComponentElement

from Ui.Commands.CmdLaunchGuides import makeLaunchLug

class LaunchLugElement(ExternalComponentElement):

    def __init__(self, parent, tag, attributes, parentObj, filename, line):
        super().__init__(parent, tag, attributes, parentObj, filename, line)

        self._knownTags.extend(["instancecount", "instanceseparation", "radialdirection", "angleoffset", "radius", "outerradius", "length", "thickness"])

    def makeObject(self):
        self._feature = makeLaunchLug()
        if self._parentObj is not None:
            self._parentObj.addChild(self._feature)

    def handleEndTag(self, tag, content):
        _tag = tag.lower().strip()
        if _tag == "instancecount":
            # self.onInstanceCount(int(content))
            pass # Not yet supported
        elif tag == "instanceseparation":
            self.onInstanceSeparation(FreeCAD.Units.Quantity(content + " m").Value)
        elif tag == "radialdirection":
            self.onAngleOffset(FreeCAD.Units.Quantity(content + " deg").Value)
        elif tag == "angleoffset":
            self.onAngleOffset(FreeCAD.Units.Quantity(content + " deg").Value)
        elif _tag == "radius" or _tag == "outerradius":
            radius = float(content)
            if hasattr(self._feature, "setOuterRadius"):
                self._feature.setOuterRadius(FreeCAD.Units.Quantity(str(radius) + " m").Value)
            if hasattr(self._feature, "setOuterRadiusAutomatic"):
                self._feature.setOuterRadiusAutomatic(False)
        elif _tag == "length":
            self.onLength(FreeCAD.Units.Quantity(content + " m").Value)
        elif _tag == "thickness":
            self.onThickness(FreeCAD.Units.Quantity(content + " m").Value)
        else:
            super().handleEndTag(tag, content)

    def onLength(self, content):
        if hasattr(self._feature, "setLength"):
            self._feature.setLength(content)

    def onThickness(self, content):
        if hasattr(self._feature, "setThickness"):
            self._feature.setThickness(content)

    def onInstanceCount(self, count):
        if hasattr(self._feature._obj, "InstanceCount"):
            self._feature._obj.InstanceCount = count

    def onInstanceSeparation(self, value):
        if hasattr(self._feature._obj, "InstanceSeparation"):
            self._feature._obj.InstanceSeparation = value

    def onAngleOffset(self, value):
        if hasattr(self._feature._obj, "AngleOffset"):
            self._feature._obj.AngleOffset = value
