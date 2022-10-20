# ***************************************************************************
# *   Copyright (c) 2021 David Carter <dcarter@davidcarter.ca>              *
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
"""Class for editing the rocket tree"""

__title__ = "FreeCAD Body Tubes"
__author__ = "David Carter"
__url__ = "https://www.davesrocketshop.com"
    
import FreeCAD
import FreeCADGui

from DraftTools import translate

def moveUp():
    for obj in FreeCADGui.Selection.getSelection():
        print("Selected %s" % (obj.Label))
        obj.Proxy.moveUp()

def moveDown():
    for obj in FreeCADGui.Selection.getSelection():
        print("Selected %s" % (obj.Label))
        obj.Proxy.moveDown()

def edit():
    for obj in FreeCADGui.Selection.getSelection():
        print("Selected %s" % (obj.Label))
        FreeCADGui.activeDocument().setEdit(obj.Label,0)
        return # Only process the first in the selection

def delete():
    for obj in FreeCADGui.Selection.getSelection():
        print("Selected %s" % (obj.Label))
        stage=FreeCADGui.ActiveDocument.ActiveView.getActiveObject("stage")
        if stage is not None:
            stage.Proxy.removeChild(obj.Proxy)
        FreeCAD.ActiveDocument.removeObject(obj.Label)

class CmdMoveUp:
    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Move up")
        FreeCADGui.addModule("Ui.Commands.CmdEditTree")
        FreeCADGui.doCommand("Ui.Commands.CmdEditTree.moveUp()")
        FreeCADGui.doCommand("App.activeDocument().recompute(None,True,True)")

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        return False
            
    def GetResources(self):
        return {'MenuText': translate("Rocket", 'Move Up'),
                'ToolTip': translate("Rocket", 'Move the object up in the rocket tree'),
                'Pixmap': FreeCAD.getUserAppDataDir() + "Mod/Rocket/Resources/icons/button_up.svg"}

class CmdMoveDown:
    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Move down")
        FreeCADGui.addModule("Ui.Commands.CmdEditTree")
        FreeCADGui.doCommand("Ui.Commands.CmdEditTree.moveDown()")
        FreeCADGui.doCommand("App.activeDocument().recompute(None,True,True)")

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        return False
            
    def GetResources(self):
        return {'MenuText': translate("Rocket", 'Move Down'),
                'ToolTip': translate("Rocket", 'Move the object down in the rocket tree'),
                'Pixmap': FreeCAD.getUserAppDataDir() + "Mod/Rocket/Resources/icons/button_down.svg"}

class CmdEdit:
    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Edit")
        FreeCADGui.addModule("Ui.Commands.CmdEditTree")
        FreeCADGui.doCommand("Ui.Commands.CmdEditTree.edit()")
        FreeCADGui.doCommand("App.activeDocument().recompute(None,True,True)")

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        return False
            
    def GetResources(self):
        return {'MenuText': translate("Rocket", 'Edit'),
                'ToolTip': translate("Rocket", 'Edit the selected part'),
                'Pixmap': FreeCAD.getUserAppDataDir() + "Mod/Rocket/Resources/icons/edit-edit.svg"}

class CmdDelete:
    def Activated(self):
        FreeCAD.ActiveDocument.openTransaction("Delete")
        FreeCADGui.addModule("Ui.Commands.CmdEditTree")
        FreeCADGui.doCommand("Ui.Commands.CmdEditTree.delete()")
        FreeCADGui.doCommand("App.activeDocument().recompute(None,True,True)")

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        return False
            
    def GetResources(self):
        return {'MenuText': translate("Rocket", 'Delete'),
                'ToolTip': translate("Rocket", 'Delete the selected part'),
                'Pixmap': FreeCAD.getUserAppDataDir() + "Mod/Rocket/Resources/icons/edit-delete.svg"}
