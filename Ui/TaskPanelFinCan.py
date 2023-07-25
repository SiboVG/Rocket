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
"""Class for drawing fins"""

__title__ = "FreeCAD Fins"
__author__ = "David Carter"
__url__ = "https://www.davesrocketshop.com"
    

import FreeCAD
import FreeCADGui
import Part
import Sketcher

from PySide import QtGui, QtCore
from PySide.QtCore import QObject, Signal
from PySide2.QtWidgets import QDialog, QGridLayout, QVBoxLayout, QSizePolicy
import math

from DraftTools import translate

from Rocket.Constants import FIN_TYPE_TRAPEZOID, FIN_TYPE_TRIANGLE, FIN_TYPE_ELLIPSE, FIN_TYPE_SKETCH
from Rocket.Constants import FIN_CROSS_SAME, FIN_CROSS_SQUARE, FIN_CROSS_ROUND, FIN_CROSS_AIRFOIL, FIN_CROSS_WEDGE, \
    FIN_CROSS_DIAMOND, FIN_CROSS_TAPER_LE, FIN_CROSS_TAPER_TE, FIN_CROSS_TAPER_LETE, FIN_CROSS_BICONVEX, FIN_CROSS_ELLIPSE
from Rocket.Constants import FINCAN_STYLE_SLEEVE, FINCAN_STYLE_BODYTUBE
from Rocket.Constants import FINCAN_EDGE_SQUARE, FINCAN_EDGE_ROUND, FINCAN_EDGE_TAPER
from Rocket.Constants import FINCAN_PRESET_CUSTOM, FINCAN_PRESET_1_8, FINCAN_PRESET_3_16, FINCAN_PRESET_1_4
from Rocket.Constants import FINCAN_COUPLER_MATCH_ID, FINCAN_COUPLER_STEPPED

from Rocket.Material import Material

from Rocket.Utilities import _err, _toFloat

from Ui.TaskPanelLocation import TaskPanelLocation
from Ui.Commands.CmdSketcher import newSketchNoEdit

from Ui.Widgets.MaterialTab import MaterialTab
from Ui.Widgets.CommentTab import CommentTab

class _FinCanDialog(QDialog):

    def __init__(self, sketch, parent=None):
        super(_FinCanDialog, self).__init__(parent)

        # define our window
        self.setGeometry(250, 250, 400, 350)
        self.setWindowTitle(translate('Rocket', "Fin Parameter"))

        self.tabWidget = QtGui.QTabWidget()
        self.tabGeneral = QtGui.QWidget()
        self.tabFinCan = QtGui.QWidget()
        self.tabCoupler = QtGui.QWidget()
        self.tabLaunchLug = QtGui.QWidget()
        self.tabMaterial = MaterialTab()
        self.tabComment = CommentTab()
        self.tabWidget.addTab(self.tabGeneral, translate('Rocket', "Fins"))
        self.tabWidget.addTab(self.tabFinCan, translate('Rocket', "Fin Can"))
        self.tabWidget.addTab(self.tabCoupler, translate('Rocket', "Coupler"))
        self.tabWidget.addTab(self.tabLaunchLug, translate('Rocket', "Launch Lug"))
        self.tabWidget.addTab(self.tabMaterial, translate('Rocket', "Material"))
        self.tabWidget.addTab(self.tabComment, translate('Rocket', "Comment"))

        layout = QVBoxLayout()
        layout.addWidget(self.tabWidget)
        self.setLayout(layout)

        self.setTabGeneral()
        self.setTabCan()
        self.setTabCoupler()
        self.setTabLaunchLug()

    def setTabGeneral(self):

        ui = FreeCADGui.UiLoader()

        # Select the type of fin
        self.finTypeLabel = QtGui.QLabel(translate('Rocket', "Fin type"), self)

        self.finTypes = (FIN_TYPE_TRAPEZOID,
            FIN_TYPE_TRIANGLE,
            FIN_TYPE_ELLIPSE, 
            #FIN_TYPE_TUBE,
            FIN_TYPE_SKETCH,
            )
        self.finTypesCombo = QtGui.QComboBox(self)
        self.finTypesCombo.addItems(self.finTypes)

        self.finSetGroup = QtGui.QGroupBox(translate('Rocket', "Fin Set"), self)
        
        self.finCountLabel = QtGui.QLabel(translate('Rocket', "Fin Count"), self)

        self.finCountSpinBox = QtGui.QSpinBox(self)
        self.finCountSpinBox.setMinimumWidth(100)
        self.finCountSpinBox.setMinimum(0)
        self.finCountSpinBox.setMaximum(10000)

        self.finSpacingLabel = QtGui.QLabel(translate('Rocket', "Fin Spacing"), self)

        self.finSpacingInput = ui.createWidget("Gui::InputField")
        self.finSpacingInput.unit = 'deg'
        self.finSpacingInput.setMinimumWidth(100)

        self.finCantLabel = QtGui.QLabel(translate('Rocket', "Fin Cant"), self)

        self.finCantInput = ui.createWidget("Gui::InputField")
        self.finCantInput.unit = 'deg'
        self.finCantInput.setMinimumWidth(100)

        # Get the fin parameters: length, width, etc...
        self.rootGroup = QtGui.QGroupBox(translate('Rocket', "Fin Root"), self)

        # Select the type of cross section
        self.rootCrossSectionLabel = QtGui.QLabel(translate('Rocket', "Cross Section"), self)

        self.rootCrossSections = (FIN_CROSS_SQUARE, FIN_CROSS_ROUND, FIN_CROSS_ELLIPSE, FIN_CROSS_BICONVEX, FIN_CROSS_AIRFOIL, FIN_CROSS_WEDGE,
            FIN_CROSS_DIAMOND, FIN_CROSS_TAPER_LE, FIN_CROSS_TAPER_TE, FIN_CROSS_TAPER_LETE)
        self.rootEllipseCrossSections = (FIN_CROSS_SQUARE, FIN_CROSS_ROUND, FIN_CROSS_ELLIPSE, FIN_CROSS_BICONVEX, FIN_CROSS_AIRFOIL, FIN_CROSS_WEDGE,
            FIN_CROSS_TAPER_LETE)
        self.rootCrossSectionsCombo = QtGui.QComboBox(self)
        self.rootCrossSectionsCombo.addItems(self.rootCrossSections)

        # Get the fin parameters: length, width, etc...
        self.rootChordLabel = QtGui.QLabel(translate('Rocket', "Chord"), self)

        self.rootChordInput = ui.createWidget("Gui::InputField")
        self.rootChordInput.unit = 'mm'
        self.rootChordInput.setMinimumWidth(100)

        self.rootThicknessLabel = QtGui.QLabel(translate('Rocket', "Thickness"), self)

        self.rootThicknessInput = ui.createWidget("Gui::InputField")
        self.rootThicknessInput.unit = 'mm'
        self.rootThicknessInput.setMinimumWidth(100)

        self.rootPerCentLabel = QtGui.QLabel(translate('Rocket', "Use percentage"), self)

        self.rootPerCentCheckbox = QtGui.QCheckBox(self)
        self.rootPerCentCheckbox.setCheckState(QtCore.Qt.Unchecked)

        self.rootLength1Label = QtGui.QLabel(translate('Rocket', "Length 1"), self)

        self.rootLength1Input = ui.createWidget("Gui::InputField")
        self.rootLength1Input.unit = 'mm'
        self.rootLength1Input.setMinimumWidth(100)

        self.rootLength2Label = QtGui.QLabel(translate('Rocket', "Length 2"), self)

        self.rootLength2Input = ui.createWidget("Gui::InputField")
        self.rootLength2Input.unit = 'mm'
        self.rootLength2Input.setMinimumWidth(100)

        self.tipGroup = QtGui.QGroupBox(translate('Rocket', "Fin Tip"), self)

        # Select the type of cross section
        self.tipCrossSectionLabel = QtGui.QLabel(translate('Rocket', "Cross Section"), self)

        self.tipCrossSections = (FIN_CROSS_SAME, FIN_CROSS_SQUARE, FIN_CROSS_ROUND, FIN_CROSS_ELLIPSE, FIN_CROSS_BICONVEX, FIN_CROSS_AIRFOIL, FIN_CROSS_WEDGE,
            FIN_CROSS_DIAMOND, FIN_CROSS_TAPER_LE, FIN_CROSS_TAPER_TE, FIN_CROSS_TAPER_LETE)
        self.tipCrossSectionsCombo = QtGui.QComboBox(self)
        self.tipCrossSectionsCombo.addItems(self.tipCrossSections)

        self.tipChordLabel = QtGui.QLabel(translate('Rocket', "Chord"), self)

        self.tipChordInput = ui.createWidget("Gui::InputField")
        self.tipChordInput.unit = 'mm'
        self.tipChordInput.setMinimumWidth(100)

        self.tipThicknessLabel = QtGui.QLabel(translate('Rocket', "Thickness"), self)

        self.tipThicknessInput = ui.createWidget("Gui::InputField")
        self.tipThicknessInput.unit = 'mm'
        self.tipThicknessInput.setMinimumWidth(100)

        self.tipSameThicknessCheckbox = QtGui.QCheckBox(translate('Rocket', "Tip thickness same as root"), self)
        self.tipSameThicknessCheckbox.setCheckState(QtCore.Qt.Unchecked)

        self.tipPerCentLabel = QtGui.QLabel(translate('Rocket', "Use percentage"), self)

        self.tipPerCentCheckbox = QtGui.QCheckBox(self)
        self.tipPerCentCheckbox.setCheckState(QtCore.Qt.Unchecked)

        self.tipLength1Label = QtGui.QLabel(translate('Rocket', "Length 1"), self)

        self.tipLength1Input = ui.createWidget("Gui::InputField")
        self.tipLength1Input.unit = 'mm'
        self.tipLength1Input.setMinimumWidth(100)

        self.tipLength2Label = QtGui.QLabel(translate('Rocket', "Length 2"), self)

        self.tipLength2Input = ui.createWidget("Gui::InputField")
        self.tipLength2Input.unit = 'mm'
        self.tipLength2Input.setMinimumWidth(100)

        self.heightLabel = QtGui.QLabel(translate('Rocket', "Height"), self)

        self.heightInput = ui.createWidget("Gui::InputField")
        self.heightInput.unit = 'mm'
        self.heightInput.setMinimumWidth(100)

        # Sweep can be forward (-sweep) or backward (+sweep)
        self.sweepLengthLabel = QtGui.QLabel(translate('Rocket', "Sweep Length"), self)

        self.sweepLengthInput = ui.createWidget("Gui::InputField")
        self.sweepLengthInput.unit = 'mm'
        self.sweepLengthInput.setMinimumWidth(100)

        # Sweep angle is tied to sweep length. It can be forward (> -90) or backward (< 90)
        self.sweepAngleLabel = QtGui.QLabel(translate('Rocket', "Sweep Angle"), self)

        self.sweepAngleInput = ui.createWidget("Gui::InputField")
        self.sweepAngleInput.unit = 'deg'
        self.sweepAngleInput.setMinimumWidth(100)

        # Fin set group
        row = 0
        grid = QGridLayout()

        grid.addWidget(self.finCountLabel, row, 0)
        grid.addWidget(self.finCountSpinBox, row, 1)
        row += 1

        grid.addWidget(self.finSpacingLabel, row, 0)
        grid.addWidget(self.finSpacingInput, row, 1)

        self.finSetGroup.setLayout(grid)

        # Root group
        row = 0
        grid = QGridLayout()

        grid.addWidget(self.rootCrossSectionLabel, row, 0)
        grid.addWidget(self.rootCrossSectionsCombo, row, 1)
        row += 1

        grid.addWidget(self.rootChordLabel, row, 0)
        grid.addWidget(self.rootChordInput, row, 1)
        row += 1

        grid.addWidget(self.rootThicknessLabel, row, 0)
        grid.addWidget(self.rootThicknessInput, row, 1)
        row += 1

        grid.addWidget(self.rootPerCentLabel, row, 0)
        grid.addWidget(self.rootPerCentCheckbox, row, 1)
        row += 1

        grid.addWidget(self.rootLength1Label, row, 0)
        grid.addWidget(self.rootLength1Input, row, 1)
        row += 1

        grid.addWidget(self.rootLength2Label, row, 0)
        grid.addWidget(self.rootLength2Input, row, 1)

        self.rootGroup.setLayout(grid)

        # Tip group
        row = 0
        grid = QGridLayout()

        grid.addWidget(self.tipCrossSectionLabel, row, 0)
        grid.addWidget(self.tipCrossSectionsCombo, row, 1)
        row += 1

        grid.addWidget(self.tipChordLabel, row, 0)
        grid.addWidget(self.tipChordInput, row, 1)
        row += 1

        grid.addWidget(self.tipThicknessLabel, row, 0)
        grid.addWidget(self.tipThicknessInput, row, 1)
        row += 1

        grid.addWidget(self.tipSameThicknessCheckbox, row, 1)
        row += 1

        grid.addWidget(self.tipPerCentLabel, row, 0)
        grid.addWidget(self.tipPerCentCheckbox, row, 1)
        row += 1

        grid.addWidget(self.tipLength1Label, row, 0)
        grid.addWidget(self.tipLength1Input, row, 1)
        row += 1

        grid.addWidget(self.tipLength2Label, row, 0)
        grid.addWidget(self.tipLength2Input, row, 1)

        self.tipGroup.setLayout(grid)

        # Main items
        row = 0
        grid = QGridLayout()

        grid.addWidget(self.finTypeLabel, row, 0)
        grid.addWidget(self.finTypesCombo, row, 1)
        row += 1

        grid.addWidget(self.heightLabel, row, 0)
        grid.addWidget(self.heightInput, row, 1)
        row += 1

        grid.addWidget(self.sweepLengthLabel, row, 0)
        grid.addWidget(self.sweepLengthInput, row, 1)
        row += 1

        grid.addWidget(self.sweepAngleLabel, row, 0)
        grid.addWidget(self.sweepAngleInput, row, 1)
        row += 1

        grid.addWidget(self.finCantLabel, row, 0)
        grid.addWidget(self.finCantInput, row, 1)


        layout = QVBoxLayout()
        layout.addItem(grid)
        layout.addWidget(self.finSetGroup)
        layout.addWidget(self.rootGroup)
        layout.addWidget(self.tipGroup)
        layout.addItem(QtGui.QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        self.tabGeneral.setLayout(layout)

    def setTabCan(self):

        ui = FreeCADGui.UiLoader()

        self.canDiameterLabel = QtGui.QLabel(translate('Rocket', "Inner Diameter"), self)

        self.canDiameterInput = ui.createWidget("Gui::InputField")
        self.canDiameterInput.unit = 'mm'
        self.canDiameterInput.setMinimumWidth(100)

        self.canAutoDiameterCheckbox = QtGui.QCheckBox(translate('Rocket', "auto"), self)
        self.canAutoDiameterCheckbox.setCheckState(QtCore.Qt.Checked)

        self.canThicknessLabel = QtGui.QLabel(translate('Rocket', "Thickness"), self)

        self.canThicknessInput = ui.createWidget("Gui::InputField")
        self.canThicknessInput.unit = 'mm'
        self.canThicknessInput.setMinimumWidth(100)

        self.canLengthLabel = QtGui.QLabel(translate('Rocket', "Length"), self)

        self.canLengthInput = ui.createWidget("Gui::InputField")
        self.canLengthInput.unit = 'mm'
        self.canLengthInput.setMinimumWidth(100)

        self.canLeadingOffsetLabel = QtGui.QLabel(translate('Rocket', "Leading Edge Offset"), self)

        self.canLeadingOffsetInput = ui.createWidget("Gui::InputField")
        self.canLeadingOffsetInput.unit = 'mm'
        self.canLeadingOffsetInput.setMinimumWidth(100)

        # Fin can leading and trailing edges
        self.canLeadingGroup = QtGui.QGroupBox(translate('Rocket', "Leading Edge"), self)

        self.canLeadingLabel = QtGui.QLabel(translate('Rocket', "Edge Style"), self)

        self.canEdges = (FINCAN_EDGE_SQUARE, FINCAN_EDGE_ROUND, FINCAN_EDGE_TAPER)
        self.canLeadingCombo = QtGui.QComboBox(self)
        self.canLeadingCombo.addItems(self.canEdges)

        self.canLeadingLengthLabel = QtGui.QLabel(translate('Rocket', "Length"), self)

        self.canLeadingLengthInput = ui.createWidget("Gui::InputField")
        self.canLeadingLengthInput.unit = 'mm'
        self.canLeadingLengthInput.setMinimumWidth(100)

        self.canTrailingGroup = QtGui.QGroupBox(translate('Rocket', "Trailing Edge"), self)

        self.canTrailingLabel = QtGui.QLabel(translate('Rocket', "Edge Style"), self)

        self.canTrailingCombo = QtGui.QComboBox(self)
        self.canTrailingCombo.addItems(self.canEdges)

        self.canTrailingLengthLabel = QtGui.QLabel(translate('Rocket', "Length"), self)

        self.canTrailingLengthInput = ui.createWidget("Gui::InputField")
        self.canTrailingLengthInput.unit = 'mm'
        self.canTrailingLengthInput.setMinimumWidth(100)

        # Leading Edge group
        row = 0
        grid = QGridLayout()

        grid.addWidget(self.canLeadingLabel, row, 0)
        grid.addWidget(self.canLeadingCombo, row, 1)
        row += 1

        grid.addWidget(self.canLeadingLengthLabel, row, 0)
        grid.addWidget(self.canLeadingLengthInput, row, 1)

        self.canLeadingGroup.setLayout(grid)

        # Trailing Edge group
        row = 0
        grid = QGridLayout()

        grid.addWidget(self.canTrailingLabel, row, 0)
        grid.addWidget(self.canTrailingCombo, row, 1)
        row += 1

        grid.addWidget(self.canTrailingLengthLabel, row, 0)
        grid.addWidget(self.canTrailingLengthInput, row, 1)

        self.canTrailingGroup.setLayout(grid)

        row = 0
        grid = QGridLayout()

        grid.addWidget(self.canDiameterLabel, row, 0)
        grid.addWidget(self.canDiameterInput, row, 1)
        grid.addWidget(self.canAutoDiameterCheckbox, row, 2)
        row += 1

        grid.addWidget(self.canThicknessLabel, row, 0)
        grid.addWidget(self.canThicknessInput, row, 1)
        row += 1

        grid.addWidget(self.canLengthLabel, row, 0)
        grid.addWidget(self.canLengthInput, row, 1)
        row += 1

        grid.addWidget(self.canLeadingOffsetLabel, row, 0)
        grid.addWidget(self.canLeadingOffsetInput, row, 1)

        layout = QVBoxLayout()
        layout.addItem(grid)
        layout.addWidget(self.canLeadingGroup)
        layout.addWidget(self.canTrailingGroup)
        layout.addItem(QtGui.QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        self.tabFinCan.setLayout(layout)

    def setTabCoupler(self):

        ui = FreeCADGui.UiLoader()

        self.couplerGroup = QtGui.QGroupBox(translate('Rocket', "Coupler"), self)
        self.couplerGroup.setCheckable(True)

        self.couplerStyleLabel = QtGui.QLabel(translate('Rocket', "Coupler Style"), self)

        # self.couplerStyles = (FINCAN_COUPLER_MATCH_ID, FINCAN_COUPLER_STEPPED)
        self.couplerStylesCombo = QtGui.QComboBox(self)
        self.couplerStylesCombo.addItem(translate('Rocket', "Flush with fin can"), FINCAN_COUPLER_MATCH_ID)
        self.couplerStylesCombo.addItem(translate('Rocket', "Stepped"), FINCAN_COUPLER_STEPPED)

        self.couplerDiameterLabel = QtGui.QLabel(translate('Rocket', "Outer Diameter"), self)

        self.couplerDiameterInput = ui.createWidget("Gui::InputField")
        self.couplerDiameterInput.unit = 'mm'
        self.couplerDiameterInput.setMinimumWidth(100)

        self.couplerAutoDiameterCheckbox = QtGui.QCheckBox(translate('Rocket', "auto"), self)
        self.couplerAutoDiameterCheckbox.setCheckState(QtCore.Qt.Checked)

        self.couplerThicknessLabel = QtGui.QLabel(translate('Rocket', "Thickness"), self)

        self.couplerThicknessInput = ui.createWidget("Gui::InputField")
        self.couplerThicknessInput.unit = 'mm'
        self.couplerThicknessInput.setMinimumWidth(100)

        self.couplerLengthLabel = QtGui.QLabel(translate('Rocket', "Length"), self)

        self.couplerLengthInput = ui.createWidget("Gui::InputField")
        self.couplerLengthInput.unit = 'mm'
        self.couplerLengthInput.setMinimumWidth(100)

        # Group
        row = 0
        grid = QGridLayout()

        grid.addWidget(self.couplerStyleLabel, row, 0)
        grid.addWidget(self.couplerStylesCombo, row, 1)
        row += 1

        grid.addWidget(self.couplerDiameterLabel, row, 0)
        grid.addWidget(self.couplerDiameterInput, row, 1)
        grid.addWidget(self.couplerAutoDiameterCheckbox, row, 2)
        row += 1

        grid.addWidget(self.couplerThicknessLabel, row, 0)
        grid.addWidget(self.couplerThicknessInput, row, 1)
        row += 1

        grid.addWidget(self.couplerLengthLabel, row, 0)
        grid.addWidget(self.couplerLengthInput, row, 1)
        row += 1

        self.couplerGroup.setLayout(grid)

        layout = QVBoxLayout()
        layout.addWidget(self.couplerGroup)
        layout.addItem(QtGui.QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        self.tabCoupler.setLayout(layout)

    def setTabLaunchLug(self):

        ui = FreeCADGui.UiLoader()

        self.lugGroup = QtGui.QGroupBox(translate('Rocket', "Launch Lug"), self)
        self.lugGroup.setCheckable(True)

        self.lugInnerDiameterLabel = QtGui.QLabel(translate('Rocket', "Inner Diameter"), self)

        self.lugInnerDiameterInput = ui.createWidget("Gui::InputField")
        self.lugInnerDiameterInput.unit = 'mm'
        self.lugInnerDiameterInput.setMinimumWidth(100)

        self.lugInnerDiameterPresetLabel = QtGui.QLabel(translate('Rocket', "Presets"), self)

        self.lugPresets = (FINCAN_PRESET_CUSTOM, FINCAN_PRESET_1_8, FINCAN_PRESET_3_16, FINCAN_PRESET_1_4)
        self.lugPresetsCombo = QtGui.QComboBox(self)
        self.lugPresetsCombo.addItems(self.lugPresets)

        self.lugThicknessLabel = QtGui.QLabel(translate('Rocket', "Thickness"), self)

        self.lugThicknessInput = ui.createWidget("Gui::InputField")
        self.lugThicknessInput.unit = 'mm'
        self.lugThicknessInput.setMinimumWidth(100)

        self.lugAutoThicknessCheckbox = QtGui.QCheckBox(translate('Rocket', "auto"), self)
        self.lugAutoThicknessCheckbox.setCheckState(QtCore.Qt.Checked)

        self.lugLengthLabel = QtGui.QLabel(translate('Rocket', "Length"), self)

        self.lugLengthInput = ui.createWidget("Gui::InputField")
        self.lugLengthInput.unit = 'mm'
        self.lugLengthInput.setMinimumWidth(100)

        self.lugAutoLengthCheckbox = QtGui.QCheckBox(translate('Rocket', "auto"), self)
        self.lugAutoLengthCheckbox.setCheckState(QtCore.Qt.Checked)

        self.lugLeadingOffsetLabel = QtGui.QLabel(translate('Rocket', "Leading Edge Offset"), self)

        self.lugLeadingOffsetInput = ui.createWidget("Gui::InputField")
        self.lugLeadingOffsetInput.unit = 'mm'
        self.lugLeadingOffsetInput.setMinimumWidth(100)

        self.lugFilletRadiusLabel = QtGui.QLabel(translate('Rocket', "Fillet radius"), self)

        self.lugFilletRadiusInput = ui.createWidget("Gui::InputField")
        self.lugFilletRadiusInput.unit = 'mm'
        self.lugFilletRadiusInput.setMinimumWidth(100)

        # Sweep parameters
        self.forwardSweepGroup = QtGui.QGroupBox(translate('Rocket', "Forward Sweep"), self)
        self.forwardSweepGroup.setCheckable(True)

        self.forwardSweepLabel = QtGui.QLabel(translate('Rocket', "Sweep Angle"), self)

        self.forwardSweepInput = ui.createWidget("Gui::InputField")
        self.forwardSweepInput.unit = 'deg'
        self.forwardSweepInput.setMinimumWidth(100)

        self.aftSweepGroup = QtGui.QGroupBox(translate('Rocket', "Aft Sweep"), self)
        self.aftSweepGroup.setCheckable(True)

        self.aftSweepLabel = QtGui.QLabel(translate('Rocket', "Sweep Angle"), self)

        self.aftSweepInput = ui.createWidget("Gui::InputField")
        self.aftSweepInput.unit = 'deg'
        self.aftSweepInput.setMinimumWidth(100)

        # Forward sweep group
        row = 0
        grid = QGridLayout()

        grid.addWidget(self.forwardSweepLabel, row, 0)
        grid.addWidget(self.forwardSweepInput, row, 1)
        row += 1

        self.forwardSweepGroup.setLayout(grid)

        # Aft sweep group
        row = 0
        grid = QGridLayout()

        grid.addWidget(self.aftSweepLabel, row, 0)
        grid.addWidget(self.aftSweepInput, row, 1)
        row += 1

        self.aftSweepGroup.setLayout(grid)

        # Launch Lug group
        row = 0
        grid = QGridLayout()

        grid.addWidget(self.lugInnerDiameterLabel, row, 0)
        grid.addWidget(self.lugPresetsCombo, row, 1)
        grid.addWidget(self.lugInnerDiameterPresetLabel, row, 2)
        row += 1

        grid.addWidget(self.lugInnerDiameterInput, row, 1)
        row += 1

        grid.addWidget(self.lugThicknessLabel, row, 0)
        grid.addWidget(self.lugThicknessInput, row, 1)
        grid.addWidget(self.lugAutoThicknessCheckbox, row, 2)
        row += 1

        grid.addWidget(self.lugLengthLabel, row, 0)
        grid.addWidget(self.lugLengthInput, row, 1)
        grid.addWidget(self.lugAutoLengthCheckbox, row, 2)
        row += 1

        grid.addWidget(self.lugLeadingOffsetLabel, row, 0)
        grid.addWidget(self.lugLeadingOffsetInput, row, 1)
        row += 1

        grid.addWidget(self.lugFilletRadiusLabel, row, 0)
        grid.addWidget(self.lugFilletRadiusInput, row, 1)
        row += 1

        grid.addWidget(self.forwardSweepGroup, row, 0, 1, 3) # 1 row, 3 columns
        row += 1

        grid.addWidget(self.aftSweepGroup, row, 0, 1, 3)
        row += 1

        self.lugGroup.setLayout(grid)

        layout = QVBoxLayout()
        layout.addWidget(self.lugGroup)
        layout.addItem(QtGui.QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        self.tabLaunchLug.setLayout(layout)

class TaskPanelFinCan(QObject):

    redrawRequired = Signal()   # Allows for async redraws to allow for longer processing times

    def __init__(self,obj,mode):
        super().__init__()

        self._obj = obj
        self._isAssembly = self._obj.Proxy.isRocketAssembly()
        
        self._finForm = _FinCanDialog(self._obj.FinType == FIN_TYPE_SKETCH)

        self._location = TaskPanelLocation(obj)
        self._locationForm = self._location.getForm()

        self.form = [self._finForm, self._locationForm]
        self._finForm.setWindowIcon(QtGui.QIcon(FreeCAD.getUserAppDataDir() + "Mod/Rocket/Resources/icons/Rocket_Fin.svg"))
        
        self.update()
        
        self._finForm.finTypesCombo.currentTextChanged.connect(self.onFinTypes)
        
        self._finForm.finCountSpinBox.valueChanged.connect(self.onCount)
        self._finForm.finSpacingInput.textEdited.connect(self.onSpacing)
        self._finForm.finCantInput.textEdited.connect(self.onCant)

        self._finForm.rootCrossSectionsCombo.currentTextChanged.connect(self.onRootCrossSection)
        self._finForm.rootChordInput.textEdited.connect(self.onRootChord)
        self._finForm.rootThicknessInput.textEdited.connect(self.onRootThickness)
        self._finForm.rootPerCentCheckbox.clicked.connect(self.onRootPerCent)
        self._finForm.rootLength1Input.textEdited.connect(self.onRootLength1)
        self._finForm.rootLength2Input.textEdited.connect(self.onRootLength2)

        self._finForm.tipCrossSectionsCombo.currentTextChanged.connect(self.onTipCrossSection)
        self._finForm.tipChordInput.textEdited.connect(self.onTipChord)
        self._finForm.tipThicknessInput.textEdited.connect(self.onTipThickness)
        self._finForm.tipSameThicknessCheckbox.stateChanged.connect(self.onTipSameThickness)
        self._finForm.tipPerCentCheckbox.clicked.connect(self.onTipPerCent)
        self._finForm.tipLength1Input.textEdited.connect(self.onTipLength1)
        self._finForm.tipLength2Input.textEdited.connect(self.onTipLength2)

        self._finForm.heightInput.textEdited.connect(self.onHeight)
        self._finForm.sweepLengthInput.textEdited.connect(self.onSweepLength)
        self._finForm.sweepAngleInput.textEdited.connect(self.onSweepAngle)

        self._finForm.canDiameterInput.textEdited.connect(self.onCanDiameter)
        self._finForm.canAutoDiameterCheckbox.stateChanged.connect(self.onCanAutoDiameter)
        self._finForm.canThicknessInput.textEdited.connect(self.onCanThickness)
        self._finForm.canLengthInput.textEdited.connect(self.onCanLength)
        self._finForm.canLeadingOffsetInput.textEdited.connect(self.onCanLeadingEdgeOffset)

        self._finForm.canLeadingCombo.currentTextChanged.connect(self.onCanLeadingEdge)
        self._finForm.canLeadingLengthInput.textEdited.connect(self.onCanLeadingLength)
        self._finForm.canTrailingCombo.currentTextChanged.connect(self.onCanTrailingEdge)
        self._finForm.canTrailingLengthInput.textEdited.connect(self.onCanTrailingLength)

        self._finForm.couplerGroup.toggled.connect(self.onCoupler)
        self._finForm.couplerStylesCombo.currentIndexChanged.connect(self.onCouplerStyle)
        self._finForm.couplerThicknessInput.textEdited.connect(self.onCouplerThickness)
        self._finForm.couplerDiameterInput.textEdited.connect(self.onCouplerDiameter)
        self._finForm.couplerAutoDiameterCheckbox.stateChanged.connect(self.onCouplerAutoDiameter)
        self._finForm.couplerLengthInput.textEdited.connect(self.onCouplerLength)

        self._finForm.lugGroup.toggled.connect(self.onLug)
        self._finForm.lugInnerDiameterInput.textEdited.connect(self.onLugInnerDiameter)
        self._finForm.lugPresetsCombo.currentTextChanged.connect(self.onLugPreset)
        self._finForm.lugThicknessInput.textEdited.connect(self.onLugThickness)
        self._finForm.lugAutoThicknessCheckbox.stateChanged.connect(self.onLugAutoThickness)
        self._finForm.lugLengthInput.textEdited.connect(self.onLugLength)
        self._finForm.lugLeadingOffsetInput.textEdited.connect(self.onLugLeadingEdgeOffset)
        self._finForm.lugAutoLengthCheckbox.stateChanged.connect(self.onLugAutoLength)
        self._finForm.lugFilletRadiusInput.textEdited.connect(self.onLugFilletRadius)

        self._finForm.forwardSweepGroup.toggled.connect(self.onForwardSweep)
        self._finForm.forwardSweepInput.textEdited.connect(self.onForwardSweepAngle)
        self._finForm.aftSweepGroup.toggled.connect(self.onAftSweep)
        self._finForm.aftSweepInput.textEdited.connect(self.onAftSweepAngle)

        self._location.locationChange.connect(self.onLocation)

        self._redrawPending = False
        self.redrawRequired.connect(self.onRedraw, QtCore.Qt.QueuedConnection)
        
        if mode == 0: # fresh created
            self.redraw()  # calculate once 
            FreeCAD.Gui.SendMsgToActiveView("ViewFit")
        
    def transferTo(self):
        "Transfer from the dialog to the object" 
        self._obj.FinType = str(self._finForm.finTypesCombo.currentText())
        
        self._obj.FinCount = self._finForm.finCountSpinBox.value()
        self._obj.FinSpacing = self._finForm.finSpacingInput.text()
        self._obj.Cant = self._finForm.finCantInput.text()

        self._obj.RootCrossSection = str(self._finForm.rootCrossSectionsCombo.currentText())
        self._obj.RootChord = self._finForm.rootChordInput.text()
        self._obj.RootThickness = self._finForm.rootThicknessInput.text()
        self._obj.RootPerCent = self._finForm.rootPerCentCheckbox.isChecked()
        self._obj.RootLength1 = self._finForm.rootLength1Input.text()
        self._obj.RootLength2 = self._finForm.rootLength2Input.text()

        self._obj.TipCrossSection = str(self._finForm.tipCrossSectionsCombo.currentText())
        self._obj.TipChord = self._finForm.tipChordInput.text()
        self._obj.TipThickness = self._finForm.tipThicknessInput.text()
        self._obj.TipSameThickness = self._finForm.tipSameThicknessCheckbox.isChecked()
        self._obj.TipPerCent = self._finForm.tipPerCentCheckbox.isChecked()
        self._obj.TipLength1 = self._finForm.tipLength1Input.text()
        self._obj.TipLength2 =self._finForm.tipLength2Input.text()

        self._obj.Height = self._finForm.heightInput.text()
        self._obj.SweepLength = self._finForm.sweepLengthInput.text()
        self._obj.SweepAngle = self._finForm.sweepAngleInput.text()

        self._obj.Diameter = self._finForm.canDiameterInput.text()
        self._obj.AutoDiameter = self._finForm.canAutoDiameterCheckbox.isChecked()
        self._obj.Thickness = self._finForm.canThicknessInput.text()
        self._obj.Length = self._finForm.canLengthInput.text()
        self._obj.LeadingEdgeOffset = self._finForm.canLeadingOffsetInput.text()

        self._obj.LeadingEdge = str(self._finForm.canLeadingCombo.currentText())
        self._obj.LeadingLength = self._finForm.canLeadingLengthInput.text()
        self._obj.TrailingEdge = str(self._finForm.canTrailingCombo.currentText())
        self._obj.TrailingLength = self._finForm.canTrailingLengthInput.text()

        self._obj.Coupler = self._finForm.couplerGroup.isChecked()
        self._obj.CouplerStyle = str(self._finForm.couplerStylesCombo.currentData())
        self._obj.CouplerThickness = self._finForm.couplerThicknessInput.text()
        self._obj.CouplerDiameter = self._finForm.couplerDiameterInput.text()
        self._obj.CouplerAutoDiameter = self._finForm.couplerAutoDiameterCheckbox.isChecked()
        self._obj.CouplerLength = self._finForm.couplerLengthInput.text()

        self._obj.LaunchLug = self._finForm.lugGroup.isChecked()
        self._obj.LugInnerDiameter = self._finForm.lugInnerDiameterInput.text()
        self._obj.LaunchLugPreset = str(self._finForm.lugPresetsCombo.currentText())
        self._obj.LugThickness = self._finForm.lugThicknessInput.text()
        self._obj.LugAutoThickness = self._finForm.lugAutoThicknessCheckbox.isChecked()
        self._obj.LugLength = self._finForm.lugLengthInput.text()
        self._obj.LugAutoLength = self._finForm.lugAutoLengthCheckbox.isChecked()
        self._obj.LugLeadingEdgeOffset = self._finForm.lugLeadingOffsetInput.text()
        self._obj.LugFilletRadius = self._finForm.lugFilletRadiusInput.text()

        self._obj.LaunchLugForwardSweep = self._finForm.forwardSweepGroup.isChecked()
        self._obj.LaunchLugForwardSweepAngle = self._finForm.forwardSweepInput.text()
        self._obj.LaunchLugAftSweep = self._finForm.aftSweepGroup.isChecked()
        self._obj.LaunchLugAftSweepAngle = self._finForm.aftSweepInput.text()

        self._finForm.tabMaterial.transferTo(self._obj)
        self._finForm.tabComment.transferTo(self._obj)

    def transferFrom(self):
        "Transfer from the object to the dialog"
        self._finForm.finTypesCombo.setCurrentText(self._obj.FinType)

        self._finForm.finCountSpinBox.setValue(self._obj.FinCount)
        self._finForm.finSpacingInput.setText(self._obj.FinSpacing.UserString)
        self._finForm.finCantInput.setText(self._obj.Cant.UserString)

        self._finForm.rootCrossSectionsCombo.setCurrentText(self._obj.RootCrossSection)
        self._finForm.rootChordInput.setText(self._obj.RootChord.UserString)
        self._finForm.rootThicknessInput.setText(self._obj.RootThickness.UserString)
        self._finForm.rootPerCentCheckbox.setChecked(self._obj.RootPerCent)
        self._finForm.rootLength1Input.setText(self._obj.RootLength1.UserString)
        self._finForm.rootLength2Input.setText(self._obj.RootLength2.UserString)

        self._finForm.tipCrossSectionsCombo.setCurrentText(self._obj.TipCrossSection)
        self._finForm.tipChordInput.setText(self._obj.TipChord.UserString)
        self._finForm.tipThicknessInput.setText(self._obj.TipThickness.UserString)
        self._finForm.tipSameThicknessCheckbox.setChecked(self._obj.TipSameThickness)
        self._finForm.tipPerCentCheckbox.setChecked(self._obj.TipPerCent)
        self._finForm.tipLength1Input.setText(self._obj.TipLength1.UserString)
        self._finForm.tipLength2Input.setText(self._obj.TipLength2.UserString)

        self._finForm.heightInput.setText(self._obj.Height.UserString)
        self._finForm.sweepLengthInput.setText(self._obj.SweepLength.UserString)
        self._finForm.sweepAngleInput.setText(self._obj.SweepAngle.UserString)

        self._finForm.canDiameterInput.setText(self._obj.Diameter.UserString)
        self._finForm.canAutoDiameterCheckbox.setChecked(self._obj.AutoDiameter)
        self._finForm.canThicknessInput.setText(self._obj.Thickness.UserString)
        self._finForm.canLengthInput.setText(self._obj.Length.UserString)
        self._finForm.canLeadingOffsetInput.setText(self._obj.LeadingEdgeOffset.UserString)

        self._finForm.canLeadingCombo.setCurrentText(self._obj.LeadingEdge)
        self._finForm.canLeadingLengthInput.setText(self._obj.LeadingLength.UserString)
        self._finForm.canTrailingCombo.setCurrentText(self._obj.TrailingEdge)
        self._finForm.canTrailingLengthInput.setText(self._obj.TrailingLength.UserString)

        self._finForm.couplerGroup.setChecked(self._obj.Coupler)
        self._finForm.couplerStylesCombo.setCurrentIndex(self._finForm.couplerStylesCombo.findData(self._obj.CouplerStyle))
        self._finForm.couplerThicknessInput.setText(self._obj.CouplerThickness.UserString)
        self._finForm.couplerDiameterInput.setText(self._obj.CouplerDiameter.UserString)
        self._finForm.couplerAutoDiameterCheckbox.setChecked(self._obj.CouplerAutoDiameter)
        self._finForm.couplerLengthInput.setText(self._obj.CouplerLength.UserString)

        self._finForm.lugGroup.setChecked(self._obj.LaunchLug)
        self._finForm.lugInnerDiameterInput.setText(self._obj.LugInnerDiameter.UserString)
        self._finForm.lugPresetsCombo.setCurrentText(self._obj.LaunchLugPreset)
        self._finForm.lugThicknessInput.setText(self._obj.LugThickness.UserString)
        self._finForm.lugAutoThicknessCheckbox.setChecked(self._obj.LugAutoThickness)
        self._finForm.lugLengthInput.setText(self._obj.LugLength.UserString)
        self._finForm.lugAutoLengthCheckbox.setChecked(self._obj.LugAutoLength)
        self._finForm.lugLeadingOffsetInput.setText(self._obj.LugLeadingEdgeOffset.UserString)
        self._finForm.lugFilletRadiusInput.setText(self._obj.LugFilletRadius.UserString)

        self._finForm.forwardSweepGroup.setChecked(self._obj.LaunchLugForwardSweep)
        self._finForm.forwardSweepInput.setText(self._obj.LaunchLugForwardSweepAngle.UserString)
        self._finForm.aftSweepGroup.setChecked(self._obj.LaunchLugAftSweep)
        self._finForm.aftSweepInput.setText(self._obj.LaunchLugAftSweepAngle.UserString)

        self._finForm.tabMaterial.transferFrom(self._obj)
        self._finForm.tabComment.transferFrom(self._obj)

        self._setFinSetState()
        self._enableRootLengths()
        self._enableFinTypes() # This calls _enableTipLengths()
        self._enableRootPercent()
        self._enableTipPercent()
        self._sweepAngleFromLength(self._obj.SweepLength)
        self._enableLeadingEdge()
        self._enableTrailingEdge()
        self._setCanStyle()
        self._setCanAutoDiameterState()
        self._setCouplerAutoDiameterState()
        self._setLugAutoThicknessState()
        self._setLugAutoLengthState()
    
    def updateMaterials(self):
        "fills the combo with the existing FCMat cards"
        self._finForm.materialPresetCombo.addItem('')
        cards = Material.materialDictionary()
        if cards:
            for k in sorted(cards.keys()):
                self._finForm.materialPresetCombo.addItem(k)

    def setEdited(self):
        try:
            self._obj.Proxy.setEdited()
        except ReferenceError:
            # Object may be deleted
            pass

    def redraw(self):
        if not self._redrawPending:
            self._redrawPending = True
            self.redrawRequired.emit()
        
    def onCount(self, value):
        self._obj.FinCount = value
        if self._obj.FinCount > 0:
            self._obj.FinSpacing = 360.0 / float(value)
        else:
            self._obj.FinSpacing = 360.0
        self._finForm.finSpacingInput.setText(self._obj.FinSpacing.UserString)
        self.redraw()
        self.setEdited()
        
    def onSpacing(self, value):
        self._obj.FinSpacing = value
        self.redraw()
        self.setEdited()
        
    def onCant(self, value):
        self._obj.Cant = value
        self.redraw()
        self.setEdited()

    def _enableFinTypes(self):
        if self._obj.FinType == FIN_TYPE_TRAPEZOID:
            self._enableFinTypeTrapezoid()
        elif self._obj.FinType == FIN_TYPE_TRIANGLE:
            self._enableFinTypeTriangle()
        elif self._obj.FinType == FIN_TYPE_ELLIPSE:
            self._enableFinTypeEllipse()
        else:
            self._enableFinTypeSketch()

    def _enableFinTypeTrapezoid(self):
        old = self._obj.RootCrossSection # This must be saved and restored
        self._finForm.rootCrossSectionsCombo.clear()
        self._finForm.rootCrossSectionsCombo.addItems(self._finForm.rootCrossSections)
        self._obj.RootCrossSection = old

        self._finForm.rootCrossSectionsCombo.setCurrentText(self._obj.RootCrossSection)

        self._finForm.heightLabel.setHidden(False)
        self._finForm.heightInput.setHidden(False)

        self._finForm.sweepLengthLabel.setHidden(False)
        self._finForm.sweepLengthInput.setHidden(False)
        self._finForm.sweepAngleLabel.setHidden(False)
        self._finForm.sweepAngleInput.setHidden(False)

        self._finForm.rootChordLabel.setHidden(False)
        self._finForm.rootChordInput.setHidden(False)
        self._finForm.rootLength2Label.setHidden(False)
        self._finForm.rootLength2Input.setHidden(False)

        self._finForm.tipGroup.setHidden(False)

        self._enableTipLengths()

    def _enableFinTypeTriangle(self):
        old = self._obj.RootCrossSection # This must be saved and restored
        self._finForm.rootCrossSectionsCombo.clear()
        self._finForm.rootCrossSectionsCombo.addItems(self._finForm.rootCrossSections)
        self._obj.RootCrossSection = old

        self._finForm.rootCrossSectionsCombo.setCurrentText(self._obj.RootCrossSection)

        self._finForm.heightLabel.setHidden(False)
        self._finForm.heightInput.setHidden(False)

        self._finForm.sweepLengthLabel.setHidden(False)
        self._finForm.sweepLengthInput.setHidden(False)
        self._finForm.sweepAngleLabel.setHidden(False)
        self._finForm.sweepAngleInput.setHidden(False)

        self._finForm.rootChordLabel.setHidden(False)
        self._finForm.rootChordInput.setHidden(False)
        self._finForm.rootLength2Label.setHidden(False)
        self._finForm.rootLength2Input.setHidden(False)

        self._finForm.tipGroup.setHidden(True)

    def _enableFinTypeEllipse(self):
        old = self._obj.RootCrossSection # This must be saved and restored
        self._finForm.rootCrossSectionsCombo.clear()
        self._finForm.rootCrossSectionsCombo.addItems(self._finForm.rootEllipseCrossSections)
        self._obj.RootCrossSection = old

        if self._obj.RootCrossSection in [FIN_CROSS_TAPER_LE, FIN_CROSS_TAPER_TE]:
            self._obj.RootCrossSection = FIN_CROSS_TAPER_LETE
        self._finForm.rootCrossSectionsCombo.setCurrentText(self._obj.RootCrossSection)

        self._finForm.heightLabel.setHidden(False)
        self._finForm.heightInput.setHidden(False)
        
        self._finForm.sweepLengthLabel.setHidden(True)
        self._finForm.sweepLengthInput.setHidden(True)
        self._finForm.sweepAngleLabel.setHidden(True)
        self._finForm.sweepAngleInput.setHidden(True)

        self._finForm.rootChordLabel.setHidden(False)
        self._finForm.rootChordInput.setHidden(False)
        self._finForm.rootLength2Label.setHidden(True)
        self._finForm.rootLength2Input.setHidden(True)

        self._finForm.tipGroup.setHidden(True)

    def _enableFinTypeSketch(self):
        old = self._obj.RootCrossSection # This must be saved and restored
        self._finForm.rootCrossSectionsCombo.clear()
        self._finForm.rootCrossSectionsCombo.addItems(self._finForm.rootCrossSections)
        self._obj.RootCrossSection = old

        self._finForm.rootCrossSectionsCombo.setCurrentText(self._obj.RootCrossSection)

        self._finForm.heightLabel.setHidden(True)
        self._finForm.heightInput.setHidden(True)
        
        self._finForm.sweepLengthLabel.setHidden(True)
        self._finForm.sweepLengthInput.setHidden(True)
        self._finForm.sweepAngleLabel.setHidden(True)
        self._finForm.sweepAngleInput.setHidden(True)

        self._finForm.rootChordLabel.setHidden(True)
        self._finForm.rootChordInput.setHidden(True)

        self._finForm.tipGroup.setHidden(True)

        # Create a default sketch if none exists
        self._defaultFinSketch()

    def _drawLines(self, sketch, points):
        last = points[-1]
        for index, point in enumerate(points):
            sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(float(last[0]), float(last[1]), 0),
                                                        FreeCAD.Vector(float(point[0]), float(point[1]), 0)))
            sketch.addConstraint(Sketcher.Constraint("DistanceX", index, 2, point[0]))
            sketch.addConstraint(Sketcher.Constraint("DistanceY", index, 2, point[1]))
            last = point

        count = len(points)
        for index in range(count):
            if index == 0:
                sketch.addConstraint(Sketcher.Constraint("Coincident", count-1, 2, index, 1))
            else:
                sketch.addConstraint(Sketcher.Constraint("Coincident", index-1, 2, index, 1))

        return sketch

    def _defaultFinSketch(self):
        if self._obj.Profile is None:
            sketch = newSketchNoEdit()
            points = []
            points.append((0.0, 0.0))
            points.append((float(self._obj.RootChord), 0.0))
            points.append((float(self._obj.SweepLength) + float(self._obj.TipChord), float(self._obj.Height)))
            points.append((float(self._obj.SweepLength), float(self._obj.Height)))

            sketch = self._drawLines(sketch, points)
            FreeCAD.ActiveDocument.recompute([sketch]) # Compute the sketch
            self._obj.Profile = sketch
            sketch.Visibility = False
        
    def onFinTypes(self, value):
        self._obj.FinType = value
        self._enableFinTypes()
        self.redraw()
        self.setEdited()
       
    def _setFinSetState(self):
        # if self._isAssembly:
        #     checked = self._finForm.finSetGroup.isChecked()
        #     self._finForm.finSetGroup.setEnabled(True)
        # else:
        #     if self._obj.FinSet:
        #         self._obj.FinSet = False
        #         self._finForm.finSetGroup.setChecked(self._obj.FinSet)
        #     checked = False
        #     self._finForm.finSetGroup.setEnabled(False)
        self._finForm.finSetGroup.setEnabled(True)
        self._finForm.finSetGroup.setChecked(self._obj.FinSet)
        # checked = self._finForm.finSetGroup.isChecked()

        # self._finForm.finCountSpinBox.setEnabled(checked)
        # self._finForm.finSpacingInput.setEnabled(checked)
        self._finForm.tipThicknessInput.setEnabled(not self._obj.TipSameThickness)

    def _enableRootLengths(self):
        value = self._obj.RootCrossSection
        if value in [FIN_CROSS_DIAMOND, FIN_CROSS_TAPER_LE, FIN_CROSS_TAPER_TE, FIN_CROSS_TAPER_LETE]:
            self._finForm.rootPerCentCheckbox.setEnabled(True)
            self._finForm.rootLength1Input.setEnabled(True)
            if value == FIN_CROSS_TAPER_LETE:
                self._finForm.rootLength2Input.setEnabled(True)
            else:
                self._finForm.rootLength2Input.setEnabled(False)
        else:
            self._finForm.rootPerCentCheckbox.setEnabled(False)
            self._finForm.rootLength1Input.setEnabled(False)
            self._finForm.rootLength2Input.setEnabled(False)

    def _enableTipLengths(self):
        if self._obj.FinType == FIN_TYPE_TRAPEZOID:
            value = self._obj.TipCrossSection
            if value == FIN_CROSS_SAME:
                value = self._obj.RootCrossSection
            if value in [FIN_CROSS_DIAMOND, FIN_CROSS_TAPER_LE, FIN_CROSS_TAPER_TE, FIN_CROSS_TAPER_LETE]:
                self._finForm.tipPerCentCheckbox.setEnabled(True)
                self._finForm.tipLength1Input.setEnabled(True)
                if value == FIN_CROSS_TAPER_LETE:
                    self._finForm.tipLength2Input.setEnabled(True)
                else:
                    self._finForm.tipLength2Input.setEnabled(False)
            else:
                self._finForm.tipPerCentCheckbox.setEnabled(False)
                self._finForm.tipLength1Input.setEnabled(False)
                self._finForm.tipLength2Input.setEnabled(False)
        
    def onRootCrossSection(self, value):
        if len(value) <= 0:
            return
            
        self._obj.RootCrossSection = value
        self._enableRootLengths()

        if self._obj.TipCrossSection == FIN_CROSS_SAME:
            self._enableTipLengths()

        self.redraw()
        self.setEdited()
        
    def onRootChord(self, value):
        try:
            self._obj.RootChord = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
        
    def onRootThickness(self, value):
        try:
            self._obj.RootThickness = FreeCAD.Units.Quantity(value).Value
            if self._obj.TipSameThickness:
                self._obj.TipThickness = FreeCAD.Units.Quantity(value).Value
                self._finForm.tipThicknessInput.setText(self._obj.TipThickness.UserString)
            self.redraw()
        except ValueError:
            pass
        self.setEdited()

    def _toPercent(self, length, chord):
        percent = 100.0 * length / chord
        if percent > 100.0:
            percent = 100.0
        if percent < 0.0:
            percent = 0.0
        return percent

    def _toLength(self, percent, chord):
        length = percent * chord / 100.0
        if length > chord:
            length = chord
        if length < 0.0:
            length = 0.0
        return length

    def _enableRootPercent(self):
        if self._obj.RootPerCent:
            self._finForm.rootLength1Input.unit = ''
            self._finForm.rootLength2Input.unit = ''
            self._finForm.rootLength1Input.setText(str(self._obj.RootLength1.Value))
            self._finForm.rootLength2Input.setText(str(self._obj.RootLength2.Value))
        else:
            self._finForm.rootLength1Input.unit = 'mm'
            self._finForm.rootLength2Input.unit = 'mm'
            self._finForm.rootLength1Input.setText(self._obj.RootLength1.UserString)
            self._finForm.rootLength2Input.setText(self._obj.RootLength2.UserString)

    def _convertRootPercent(self):
        if self._obj.RootPerCent:
            # Convert to percentages
            self._obj.RootLength1 = self._toPercent(self._obj.RootLength1.Value, self._obj.RootChord.Value)
            self._obj.RootLength2 = self._toPercent(self._obj.RootLength2.Value, self._obj.RootChord.Value)
        else:
            # Convert to lengths
            self._obj.RootLength1 = self._toLength(self._obj.RootLength1.Value, self._obj.RootChord.Value)
            self._obj.RootLength2 = self._toLength(self._obj.RootLength2.Value, self._obj.RootChord.Value)
        self._enableRootPercent()
        
    def onRootPerCent(self, value):
        self._obj.RootPerCent = self._finForm.rootPerCentCheckbox.isChecked()
        self._convertRootPercent()

        self.redraw()
        self.setEdited()
        
    def onRootLength1(self, value):
        try:
            self._obj.RootLength1 = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
        
    def onRootLength2(self, value):
        try:
            self._obj.RootLength2 = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
        
    def onTipCrossSection(self, value):
        self._obj.TipCrossSection = value
        self._enableTipLengths()

        self.redraw()
        self.setEdited()
        
    def onTipChord(self, value):
        try:
            self._obj.TipChord = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
        
    def onTipThickness(self, value):
        try:
            self._obj.TipThickness = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
        
    def onTipSameThickness(self, value):
        try:
            self._obj.TipSameThickness = value
            self.redraw()
            self._setFinSetState()
        except ValueError:
            pass
        self.setEdited()

    def _enableTipPercent(self):
        if self._obj.TipPerCent:
            self._finForm.tipLength1Input.unit = ''
            self._finForm.tipLength2Input.unit = ''
            self._finForm.tipLength1Input.setText(str(self._obj.TipLength1.Value))
            self._finForm.tipLength2Input.setText(str(self._obj.TipLength2.Value))
        else:
            self._finForm.tipLength1Input.unit = 'mm'
            self._finForm.tipLength2Input.unit = 'mm'
            self._finForm.tipLength1Input.setText(self._obj.TipLength1.UserString)
            self._finForm.tipLength2Input.setText(self._obj.TipLength2.UserString)

    def _convertTipPercent(self):
        if self._obj.TipPerCent:
            # Convert to percentages
            self._obj.TipLength1 = self._toPercent(self._obj.TipLength1.Value, self._obj.TipChord.Value)
            self._obj.TipLength2 = self._toPercent(self._obj.TipLength2.Value, self._obj.TipChord.Value)
        else:
            # Convert to lengths
            self._obj.TipLength1 = self._toLength(self._obj.TipLength1.Value, self._obj.TipChord.Value)
            self._obj.TipLength2 = self._toLength(self._obj.TipLength2.Value, self._obj.TipChord.Value)
        self._enableTipPercent()
        
    def onTipPerCent(self, value):
        self._obj.TipPerCent = self._finForm.tipPerCentCheckbox.isChecked()
        self._convertTipPercent()

        self.redraw()
        self.setEdited()
        
    def onTipLength1(self, value):
        try:
            self._obj.TipLength1 = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
        
    def onTipLength2(self, value):
        try:
            self._obj.TipLength2 = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        self.setEdited()

    def onHeight(self, value):
        try:
            self._obj.Height = FreeCAD.Units.Quantity(value).Value
            self._sweepAngleFromLength(self._obj.SweepLength)
            self.redraw()
        except ValueError:
            pass
        self.setEdited()

    def _sweepLengthFromAngle(self, value):
        theta = _toFloat(value)
        if theta <= -90.0 or theta >= 90.0:
            _err("Sweep angle must be greater than -90 and less than +90")
            return
        theta = math.radians(-1.0 * (theta + 90.0))
        length = _toFloat(self._obj.Height) / math.tan(theta)
        self._obj.SweepLength = length
        self._finForm.sweepLengthInput.setText(self._obj.SweepLength.UserString)

    def _sweepAngleFromLength(self, value):
        length = _toFloat(value)
        theta = 90.0 - math.degrees(math.atan2(_toFloat(self._obj.Height), length))
        self._obj.SweepAngle = theta
        self._finForm.sweepAngleInput.setText(self._obj.SweepAngle.UserString)
        
    def onSweepLength(self, value):
        try:
            self._obj.SweepLength = FreeCAD.Units.Quantity(value).Value
            self._sweepAngleFromLength(self._obj.SweepLength)
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
        
    def onSweepAngle(self, value):
        try:
            self._obj.SweepAngle = FreeCAD.Units.Quantity(value).Value
            self._sweepLengthFromAngle(self._obj.SweepAngle)
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
       
    def _setCanStyle(self):
        if self._obj.FinCanStyle == FINCAN_STYLE_SLEEVE:
            self._finForm.canDiameterLabel.setText(translate('Rocket', "Inner Diameter"))
            self._finForm.canLeadingGroup.setHidden(False)
            if self._isAssembly:
                self._finForm.couplerGroup.setEnabled(False)
            else:
                self._finForm.couplerGroup.setEnabled(True)
            self._obj.Coupler = False
        else:
            self._finForm.canDiameterLabel.setText(translate('Rocket', "Outer Diameter"))
            if self._isAssembly:
                self._finForm.canLeadingGroup.setHidden(True)
            else:
                self._finForm.canLeadingGroup.setHidden(False)
            self._finForm.couplerGroup.setEnabled(True)
        self._finForm.couplerGroup.setChecked(self._obj.Coupler)
    
    def onCanDiameter(self, value):
        try:
            self._obj.Diameter = FreeCAD.Units.Quantity(value).Value
            self._obj.ParentRadius = (self._obj.Diameter / 2.0) # + self._obj.Thickness
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
     
    def _setCanAutoDiameterState(self):
        if self._isAssembly:
            self._finForm.canDiameterInput.setEnabled(not self._obj.AutoDiameter)
            self._finForm.canAutoDiameterCheckbox.setChecked(self._obj.AutoDiameter)
        else:
            self._obj.AutoDiameter = False
            self._finForm.canAutoDiameterCheckbox.setEnabled(False)
            self._finForm.canDiameterInput.setEnabled(not self._obj.AutoDiameter)
            self._finForm.canAutoDiameterCheckbox.setChecked(self._obj.AutoDiameter)

        if self._obj.AutoDiameter:
            self._obj.Diameter = (self._obj.ParentRadius * 2.0)
            self._finForm.canDiameterInput.setText(self._obj.Diameter.UserString)

    def onCanAutoDiameter(self, value):
        self._obj.AutoDiameter = value
        self._setCanAutoDiameterState()

        self.redraw()
        self.setEdited()
        
    def onCanThickness(self, value):
        try:
            self._obj.Thickness = FreeCAD.Units.Quantity(value).Value
            self._obj.ParentRadius = (self._obj.Diameter / 2.0) # + self._obj.Thickness
            self._setLugAutoThicknessState()
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
        
    def onCanLength(self, value):
        try:
            self._obj.Length = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
        
    def onCanLeadingEdgeOffset(self, value):
        try:
            self._obj.LeadingEdgeOffset = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        self.setEdited()


    def _enableLeadingEdge(self):
        if self._obj.LeadingEdge == FINCAN_EDGE_SQUARE:
            self._finForm.canLeadingLengthInput.setEnabled(False)
        else:
            self._finForm.canLeadingLengthInput.setEnabled(True)
        
    def onCanLeadingEdge(self, value):
        if len(value) <= 0:
            return
            
        self._obj.LeadingEdge = value
        self._enableLeadingEdge()
        self._setLugAutoLengthState()

        self.redraw()
        self.setEdited()
        
    def onCanLeadingLength(self, value):
        try:
            self._obj.LeadingLength = FreeCAD.Units.Quantity(value).Value
            self._setLugAutoLengthState()
            self.redraw()
        except ValueError:
            pass
        self.setEdited()

    def _enableTrailingEdge(self):
        if self._obj.TrailingEdge == FINCAN_EDGE_SQUARE:
            self._finForm.canTrailingLengthInput.setEnabled(False)
        else:
            self._finForm.canTrailingLengthInput.setEnabled(True)
        
    def onCanTrailingEdge(self, value):
        if len(value) <= 0:
            return
            
        self._obj.TrailingEdge = value
        self._enableTrailingEdge()
        self._setLugAutoLengthState()

        self.redraw()
        self.setEdited()
        
    def onCanTrailingLength(self, value):
        try:
            self._obj.TrailingLength = FreeCAD.Units.Quantity(value).Value
            self._setLugAutoLengthState()
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
       
    def onCoupler(self, value):
        self._obj.Coupler = self._finForm.couplerGroup.isChecked()

        self.redraw()
        
    def onCouplerStyle(self, value):
        self._obj.CouplerStyle = self._finForm.couplerStylesCombo.itemData(value)

        self.redraw()
        
    def onCouplerThickness(self, value):
        try:
            self._obj.CouplerThickness = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
     
    def _setCouplerAutoDiameterState(self):
        if self._isAssembly:
            self._finForm.couplerDiameterInput.setEnabled(not self._obj.CouplerAutoDiameter)
            self._finForm.couplerAutoDiameterCheckbox.setChecked(self._obj.CouplerAutoDiameter)
        else:
            self._obj.CouplerAutoDiameter = False
            self._finForm.couplerAutoDiameterCheckbox.setEnabled(False)
            self._finForm.couplerDiameterInput.setEnabled(not self._obj.CouplerAutoDiameter)
            self._finForm.couplerAutoDiameterCheckbox.setChecked(self._obj.CouplerAutoDiameter)

        if self._obj.CouplerAutoDiameter:
            pass
            # self._obj.Diameter = (self._obj.ParentRadius * 2.0)
            # self._finForm.canDiameterInput.setText(self._obj.Diameter.UserString)

    def onCouplerAutoDiameter(self, value):
        self._obj.CouplerAutoDiameter = value
        self._setCouplerAutoDiameterState()

        self.redraw()
        self.setEdited()
        
    def onCouplerDiameter(self, value):
        try:
            self._obj.CouplerDiameter = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        
    def onCouplerLength(self, value):
        try:
            self._obj.CouplerLength = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
       
    def onLug(self, value):
        self._obj.LaunchLug = self._finForm.lugGroup.isChecked()

        self.redraw()
        self.setEdited()
        
    def onLugInnerDiameter(self, value):
        try:
            self._obj.LugInnerDiameter = FreeCAD.Units.Quantity(value).Value
            self._finForm.lugPresetsCombo.setCurrentText(FINCAN_PRESET_CUSTOM)
            self.redraw()
        except ValueError:
            pass
        self.setEdited()

    def _setLugDiameter(self, value):
        try:
            self._obj.LugInnerDiameter = value
            self._finForm.lugInnerDiameterInput.setText(self._obj.LugInnerDiameter.UserString)
            self.redraw()
        except ValueError:
            pass
        self.setEdited()

    def onLugPreset(self, value):
        if value == FINCAN_PRESET_1_8:
            self._setLugDiameter(3.56)
        elif value == FINCAN_PRESET_3_16:
            self._setLugDiameter(5.56)
        elif value == FINCAN_PRESET_1_4:
            self._setLugDiameter(6.35)

    def onLugThickness(self, value):
        try:
            self._obj.LugThickness = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
     
    def _setLugAutoThicknessState(self):
        self._finForm.lugThicknessInput.setEnabled(not self._obj.LugAutoThickness)
        self._finForm.lugAutoThicknessCheckbox.setChecked(self._obj.LugAutoThickness)

        if self._obj.LugAutoThickness:
            self._obj.LugThickness = self._obj.Thickness
            self._finForm.lugThicknessInput.setText(self._obj.Thickness.UserString)

    def onLugAutoThickness(self, value):
        self._obj.LugAutoThickness = value
        self._setLugAutoThicknessState()

        self.redraw()
        self.setEdited()
        
    def onLugLength(self, value):
        try:
            self._obj.LugLength = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
     
    def _setLugAutoLengthState(self):
        self._finForm.lugLengthInput.setEnabled(not self._obj.LugAutoLength)
        self._finForm.lugAutoLengthCheckbox.setChecked(self._obj.LugAutoLength)

        if self._obj.LugAutoLength:
            length = float(self._obj.Length)

            if self._obj.LugLeadingEdgeOffset > 0:
                length -= float(self._obj.LugLeadingEdgeOffset)
            elif self._obj.LeadingEdge != FINCAN_EDGE_SQUARE:
                length -= float(self._obj.LeadingLength)

            if self._obj.TrailingEdge != FINCAN_EDGE_SQUARE:
                length -= float(self._obj.TrailingLength)
                
            self._obj.LugLength = length
            self._finForm.lugLengthInput.setText(self._obj.LugLength.UserString)

    def onLugAutoLength(self, value):
        self._obj.LugAutoLength = value
        self._setLugAutoLengthState()

        self.redraw()
        self.setEdited()
        
    def onLugLeadingEdgeOffset(self, value):
        try:
            self._obj.LugLeadingEdgeOffset = FreeCAD.Units.Quantity(value).Value
            self._setLugAutoLengthState()
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
        
    def onLugFilletRadius(self, value):
        try:
            self._obj.LugFilletRadius = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        self.setEdited()
        
    def _setForwardSweepState(self):
        # self._finForm.forwardSweepInput.setEnabled(self._obj.LaunchLugForwardSweep)
        self._finForm.forwardSweepGroup.setChecked(self._obj.LaunchLugForwardSweep)
        
    def onForwardSweep(self, value):
        self._obj.LaunchLugForwardSweep = value
        self._setForwardSweepState()

        self.redraw()
        
    def onForwardSweepAngle(self, value):
        try:
            self._obj.LaunchLugForwardSweepAngle = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass
        
    def _setAftSweepState(self):
        # self._finForm.aftSweepInput.setEnabled(self._obj.LaunchLugAftSweep)
        self._finForm.aftSweepGroup.setChecked(self._obj.LaunchLugAftSweep)
        
    def onAftSweep(self, value):
        self._obj.LaunchLugAftSweep = value
        self._setAftSweepState()

        self.redraw()
        
    def onAftSweepAngle(self, value):
        try:
            self._obj.LaunchLugAftSweepAngle = FreeCAD.Units.Quantity(value).Value
            self.redraw()
        except ValueError:
            pass

    def onLocation(self):
        self._obj.Proxy.updateChildren()
        self.redraw()
        self.setEdited()

    def onRedraw(self):
        self._obj.Proxy.execute(self._obj)
        self._redrawPending = False
        
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok) | int(QtGui.QDialogButtonBox.Cancel)| int(QtGui.QDialogButtonBox.Apply)

    def clicked(self,button):
        if button == QtGui.QDialogButtonBox.Apply:
            self.transferTo()
            self.redraw() 
        
    def update(self):
        'fills the widgets'
        self.transferFrom()
                
    def accept(self):
        self.transferTo()
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.ActiveDocument.resetEdit()
        
                    
    def reject(self):
        FreeCAD.ActiveDocument.abortTransaction()
        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.ActiveDocument.resetEdit()
