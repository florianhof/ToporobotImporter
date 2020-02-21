# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ToporobotImporterDialog
                                 A QGIS plugin
 Imports Cave galleries from Toporobot 
                             -------------------
        begin                : 2014-01-04
        copyright            : (C) 2014 by Florian Hof
        email                : florian@speleo.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import absolute_import

from builtins import str
from builtins import range
from qgis.PyQt.QtCore import Qt, QRegExp, QFileInfo
from qgis.PyQt.QtGui import QRegExpValidator, QDesktopServices
from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QMessageBox
from .toporobotimporter_ui import Ui_ToporobotImporter
from qgis.core import QgsProject, QgsVectorLayer, QgsMapLayer, QgsCoordinateReferenceSystem
from qgis.gui import QgsFileWidget, QgsProjectionSelectionWidget
import qgis.utils
import os.path
from .topoimpProcess import ToporobotImporterProcess, getLayerFromDatapath
from . import topoReader
from . import topoDrawer


class ToporobotImporterDialog(QDialog):

  def __init__(self):
    QDialog.__init__(self)
    # Set up the user interface from Designer.
    self.ui = Ui_ToporobotImporter()
    self.ui.setupUi(self)

    self.lastInputDirectory = os.getenv('USERPROFILE') or os.getenv('HOME') or "."
    self.lastOutputDirectory = QgsProject.instance().homePath() or "."
    self.process = None
    ui = self.ui
    
    ui.leEncoding.insert('mac_roman') # Toporobot comes from Mac

    # unsuccessful trial to set file filter on QgsFileWidget
    ui.leToporobotText.filter = "*.Text;;*.*"
    ui.leToporobotText.dialogTitle = "Input Toporobot .Text file"
    ui.leToporobotText.defaultRoot = self.lastInputDirectory
    ui.leToporobotText.fileChanged.connect(self.updateLastInputDirectory)
    ui.leToporobotCoord.filter = "Toporobot (*.Coord)"
    ui.leToporobotCoord.lineEdit().filters = "Toporobot (*.Coord)"
    ui.leMergeMapping.selectedFilter = "*.csv"
    ui.leOutPoints.storageMode = QgsFileWidget.StorageMode.SaveFile
    ui.leOutAims.storageMode = QgsFileWidget.SaveFile

    # connect the buttons to actions
    ui.bBrowseToporobotText.clicked.connect(self.browseForInToporobotTextFileFunction(ui.leToporobotText))
    ui.bBrowseToporobotCoord.clicked.connect(self.browseForInToporobotCoordFileFunction(ui.leToporobotCoord))
    ui.bBrowseMergeMapping.clicked.connect(self.browseForInMergeMappingFileFunction(ui.leMergeMapping))
    self.outShapeFileFormWidgets = [
      (ui.lbOutPoints, ui.leOutPoints, ui.bBrowseOutPoints, topoDrawer.StationsDrawer()),
      (ui.lbOutAims, ui.leOutAims, ui.bBrowseOutAims, topoDrawer.AimsDrawer()),
      (ui.lbOutAimsSurface, ui.leOutAimsSurface, ui.bBrowseOutAimsSurface, topoDrawer.AimsSurfaceDrawer()),
      (ui.lbOutSeries, ui.leOutSeries, ui.bBrowseOutSeries, topoDrawer.SeriesDrawer()),
      (ui.lbOutSeriesBorder, ui.leOutSeriesBorder, ui.bBrowseOutSeriesBorder, topoDrawer.SeriesSurfaceDrawer())]
    for (label, lineedit, button, drawer) in self.outShapeFileFormWidgets:
      button.clicked.connect(self.browseForOutShapefileFunction(lineedit))
    ui.buttonBox.helpRequested.connect(self.showHelp)
    ui.leSRS.setOptionVisible(QgsProjectionSelectionWidget.CrsOption.CrsNotSet, True)


  def show(self):
    ui = self.ui

    # init the dropdown with the possibly DEM layers
    currentLayerBand = None
    if (ui.cbDemLayer.currentIndex() > 0):
      currentLayerBand = ui.cbDemLayer.itemText(ui.cbDemLayer.currentIndex())
    for j in reversed(list(range(ui.cbDemLayer.count()))):
      ui.cbDemLayer.removeItem(j)
    ui.cbDemLayer.addItem('----------', None)
    for layer in list(QgsProject.instance().mapLayers().values()):
      if layer.type() == QgsMapLayer.RasterLayer:
        if layer.bandCount() == 1: # first the one-band images, so should be a DEM
            rasterLayerBand = topoReader.LayerBand(layer, 1, layer.bandName(1))
            ui.cbDemLayer.addItem(layer.name(), rasterLayerBand)
    for layer in list(QgsProject.instance().mapLayers().values()):
      if layer.type() == QgsMapLayer.RasterLayer:
        if layer.bandCount() > 1: # then the multi-bands images, just in case
          for j in range(layer.bandCount()):
            rasterLayerBand = topoReader.LayerBand(layer, j+1, layer.bandName(j+1))
            ui.cbDemLayer.addItem(layer.name() + ' / ' + layer.bandName(j+1), rasterLayerBand)
    if (currentLayerBand):
      ui.cbDemLayer.setCurrentIndex(ui.cbDemLayer.findText(currentLayerBand))
    else:
      ui.cbDemLayer.setCurrentIndex(0)
    ui.leSRS.setCrs(QgsCoordinateReferenceSystem())
    self.repaint()

    # now really show
    super(ToporobotImporterDialog, self).show()
    ui.leToporobotText.filter = "*.Text;;*.*"
    ui.leMergeMapping.setSelectedFilter("*.csv")


  def browseForInToporobotTextFileFunction(self, lineedit):
    return lambda: self.browseForInFile(lineedit, "Input Toporobot .Text file", "Toporobot (*.Text);;All (*.*)")

  def browseForInToporobotCoordFileFunction(self, lineedit):
    return lambda: self.browseForInFile(lineedit, "Input Toporobot .Coord file", "Toporobot (*.Coord);;All (*.*)")

  def browseForInMergeMappingFileFunction(self, lineedit):
    return lambda: self.browseForInFile(lineedit, "Input Merge mapping file", "Comma-separated values (*.csv);;All (*.*)")

  def browseForInFile(self, lineedit, caption, selectedFilter):
    filename, __ = QFileDialog.getOpenFileName(self, caption, self.lastInputDirectory, selectedFilter)
    if filename:
      fileinfo = QFileInfo(filename)
      lineedit.setFilePath(fileinfo.absoluteFilePath())
      self.lastInputDirectory = fileinfo.absolutePath()

  def updateLastInputDirectory(self, filepath):
    self.lastInputDirectory = os.path.dirname(filepath)

  def browseForOutShapefile(self, lineedit):
    filename, __ = QFileDialog.getSaveFileName(self, "Output Shapefile", self.lastOutputDirectory, "Shapefiles (*.shp)")
    if filename:
      if not filename.lower().endswith(".shp"):
        filename = filename + ".shp"
      fileinfo = QFileInfo(filename)
      lineedit.setFilePath(fileinfo.absoluteFilePath())
      self.lastOutputDirectory = fileinfo.absolutePath()

  def browseForOutShapefileFunction(self, lineedit):
    return lambda: self.browseForOutShapefile(lineedit)


  def done(self, resultCode):
    self.process = None
    if resultCode == QDialog.Accepted:
      if self.validateInputs():
        self.defineProcess()
      else:
        return # stay on the dialog, the user has to correct
    super(ToporobotImporterDialog, self).done(resultCode) # close and exit the dialog


  def showHelp(self):
    qgis.utils.showPluginHelp(filename="help/index")



  def validateInputs(self):
    errorMsgs = []
    ui = self.ui
    if   ui.leToporobotText.filePath() == "":
      errorMsgs.append("The Toporobot .Text file has to be filled")
    if ui.leToporobotCoord.filePath() == "":
      errorMsgs.append("The Toporobot .Coord file has to be filled")
    nbOutFiles = 0
    for (label, lineedit, button, drawer) in self.outShapeFileFormWidgets:
      if lineedit.filePath():
        outPath = str(lineedit.filePath())
        nbOutFiles += 1
        existingLayer = getLayerFromDatapath(outPath)
        if (not existingLayer) and ui.rbAppend.isChecked() and os.path.exists(outPath):
          existingLayer = QgsVectorLayer(outPath, None, "ogr")
        if existingLayer:
          if existingLayer.wkbType() != drawer.wkbType():
            errorMsgs.append("Cannot append to the file \""+os.path.basename(outPath)+"\" because its type is not compatible")
          del existingLayer
    if nbOutFiles == 0:
      errorMsgs.append("No output shapefile has been filled")
    if len(errorMsgs) > 0:
      QMessageBox.information(self, self.windowTitle(), "\n".join(errorMsgs))
      return False
    else:
      return True


  def defineProcess(self):
    self.process = ToporobotImporterProcess()
    ui = self.ui
    self.process.topoTextFilePath = str(ui.leToporobotText.filePath())
    self.process.topoCoordFilePath = str(ui.leToporobotCoord.filePath())
    self.process.mergeMappingFilePath = str(ui.leMergeMapping.filePath())
    self.process.encoding = ui.leEncoding.text()
    self.process.demLayerBands = []
    if (ui.cbDemLayer.currentIndex() >= 0):
      rasterLayerBand = ui.cbDemLayer.itemData(ui.cbDemLayer.currentIndex())
      if (rasterLayerBand):
        self.process.demLayerBands.append(rasterLayerBand)
    self.process.outFilePathWithLayerNameAndDrawer = []
    for (label, lineedit, button, drawer) in self.outShapeFileFormWidgets:
      if lineedit.filePath():
        self.process.outFilePathWithLayerNameAndDrawer.append((lineedit.filePath(), self.toLayerName(lineedit, label), drawer))
    self.process.coordRefSystem = ui.leSRS.crs()
    self.process.shouldOverride = ui.rbOverride.isChecked()
    self.process.shouldShowLayer = ui.cbDisplayInQgis.isChecked()


  def run(self):
    self.process.run()


  def toLayerName(self, lineeditpath, label):
    return os.path.splitext(os.path.basename(lineeditpath.filePath()))[0] #+ " - " + label.text()


