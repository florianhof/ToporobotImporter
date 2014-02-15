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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_toporobotimporter import Ui_ToporobotImporter
from qgis.core import *
from qgis.gui import QgsGenericProjectionSelector
import qgis.utils
import os
import os.path
from topoimpProcess import ToporobotImporterProcess, getLayerFromDatapath
import topoReader
import topoDrawer


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

    # set validators where required
    ui.leSRS.setValidator(QRegExpValidator(QRegExp("(^epsg:{1}\\s*\\d+)|(^\\+proj.*)", Qt.CaseInsensitive), ui.leSRS));

    # connect the buttons to actions
    QObject.connect(ui.bBrowseToporobotText, SIGNAL("clicked()"), self.browseForInToporobotTextFileFunction(ui.leToporobotText))
    QObject.connect(ui.bBrowseToporobotCoord, SIGNAL("clicked()"), self.browseForInToporobotCoordFileFunction(ui.leToporobotCoord))
    QObject.connect(ui.bBrowseMergeMapping, SIGNAL("clicked()"), self.browseForInMergeMappingFileFunction(ui.leMergeMapping))
    self.outShapeFileFormWidgets = [
      (ui.lbOutPoints, ui.leOutPoints, ui.bBrowseOutPoints, topoDrawer.StationsDrawer()),
      (ui.lbOutAims, ui.leOutAims, ui.bBrowseOutAims, topoDrawer.AimsDrawer()),
      (ui.lbOutAimsSurface, ui.leOutAimsSurface, ui.bBrowseOutAimsSurface, topoDrawer.AimsSurfaceDrawer()),
      (ui.lbOutSeries, ui.leOutSeries, ui.bBrowseOutSeries, topoDrawer.SeriesDrawer()),
      (ui.lbOutSeriesBorder, ui.leOutSeriesBorder, ui.bBrowseOutSeriesBorder, topoDrawer.SeriesSurfaceDrawer())]
    for (label, lineedit, button, drawer) in self.outShapeFileFormWidgets:
      QObject.connect(button, SIGNAL("clicked()"), self.browseForOutShapefileFunction(lineedit))
    QObject.connect(ui.bSRS, SIGNAL("clicked()"), self.browseForSRS)
    QObject.connect(ui.buttonBox, SIGNAL("helpRequested()"), self.showHelp)


  def show(self):
    ui = self.ui

    # init the dropdown with the possibly DEM layers
    self.rasterLayerBands = [(-1, None, -1, '')]
    for j in reversed(range(ui.cbDemLayer.count())):
      ui.cbDemLayer.removeItem(j)
    ui.cbDemLayer.addItem('----------');
    i = -1
    for layer in QgsMapLayerRegistry.instance().mapLayers().values():
      i = i + 1
      if layer.type() == layer.RasterLayer:
        if layer.bandCount() == 1: # first the one-band images, so should be a DEM
            self.rasterLayerBands.append((i, layer, 1, layer.bandName(1)))
            ui.cbDemLayer.addItem(layer.name());
    i = -1
    for layer in QgsMapLayerRegistry.instance().mapLayers().values():
      i = i + 1
      if layer.type() == layer.RasterLayer:
        if layer.bandCount() > 1: # then the multi-bands images, just in case
          for j in range(layer.bandCount()):
            self.rasterLayerBands.append((i, layer, j+1, layer.bandName(j+1)))
            ui.cbDemLayer.addItem(layer.name() + ' / ' + layer.bandName(j+1));
    ui.cbDemLayer.setCurrentIndex(0)
    self.repaint()

    # now really show
    super(ToporobotImporterDialog, self).show()

  def browseForInToporobotTextFileFunction(self, lineedit):
    return lambda: self.browseForInFile(lineedit, u"Input Toporobot .Text file", u"Toporobot (*.Text);;All (*.*)")

  def browseForInToporobotCoordFileFunction(self, lineedit):
    return lambda: self.browseForInFile(lineedit, u"Input Toporobot .Coord file", u"Toporobot (*.Coord);;All (*.*)")

  def browseForInMergeMappingFileFunction(self, lineedit):
    return lambda: self.browseForInFile(lineedit, u"Input Merge mapping file", u"Comma-separated values (*.csv);;All (*.*)")

  def browseForInFile(self, lineedit, caption, selectedFilter):
    filename = QFileDialog.getOpenFileName(self, caption, self.lastInputDirectory, selectedFilter)
    if filename:
      fileinfo = QFileInfo(filename)
      lineedit.clear()
      lineedit.insert(fileinfo.absoluteFilePath())
      self.lastInputDirectory = fileinfo.absolutePath()

  def browseForOutShapefile(self, lineedit):
    filename = QFileDialog.getSaveFileName(self, u"Output Shapefile", self.lastOutputDirectory, u"Shapefiles (*.shp)")
    if filename:
      if not filename.lower().endswith(".shp"):
        filename = filename + ".shp"
      fileinfo = QFileInfo(filename)
      lineedit.clear()
      lineedit.insert(fileinfo.absoluteFilePath())
      self.lastOutputDirectory = fileinfo.absolutePath()

  def browseForOutShapefileFunction(self, lineedit):
    return lambda: self.browseForOutShapefile(lineedit)

  def browseForSRS(self):
    srsSelector = QgsGenericProjectionSelector(self)
    srsSelector.setSelectedCrsName(self.ui.leSRS.text())
    if srsSelector.exec_():
      self.ui.leSRS.clear()
      self.ui.leSRS.insert(srsSelector.selectedProj4String())


  def done(self, resultCode):
    self.process = None
    if resultCode == QDialog.Accepted:
      if self.validateInputs():
        self.defineProcess()
      else:
        return # stay on the dialog, the user has to correct
    super(ToporobotImporterDialog, self).done(resultCode) # close and exit the dialog


  def showHelp(self):
    #qgis.utils.showPluginHelp() # doesn't work :-(
    help_file = "file:///"+ qgis.utils.pluginDirectory('ToporobotImporter') + "/help/index.html"
    QDesktopServices.openUrl(QUrl(help_file))



  def validateInputs(self):
    errorMsgs = []
    ui = self.ui
    if   ui.leToporobotText.text() == "":
      errorMsgs.append(u"The Toporobot .Text file has to be filled")
    if ui.leToporobotCoord.text() == "":
      errorMsgs.append(u"The Toporobot .Coord file has to be filled")
    nbOutFiles = 0
    for (label, lineedit, button, drawer) in self.outShapeFileFormWidgets:
      if lineedit.text():
        outPath = unicode(lineedit.text())
        nbOutFiles += 1
        existingLayer = getLayerFromDatapath(outPath)
        if (not existingLayer) and ui.rbAppend.isChecked() and os.path.exists(outPath):
          existingLayer = QgsVectorLayer(outPath, None, "ogr")
        if existingLayer:
          if existingLayer.wkbType() <> drawer.wkbType():
            errorMsgs.append(u"Cannot append to the file \""+os.path.basename(outPath)+u"\" because its type is not compatible")
          del existingLayer
    if nbOutFiles == 0:
      errorMsgs.append(u"No output shapefile has been filled")
    if len(errorMsgs) > 0:
      QMessageBox.information(self, self.windowTitle(), u"\n".join(errorMsgs))
      return False
    else:
      return True


  def defineProcess(self):
    self.process = ToporobotImporterProcess()
    ui = self.ui
    self.process.topoTextFilePath = unicode(ui.leToporobotText.text())
    self.process.topoCoordFilePath = unicode(ui.leToporobotCoord.text())
    self.process.mergeMappingFilePath = unicode(ui.leMergeMapping.text())
    self.process.demLayerBands = []
    rasterLayerBand = self.rasterLayerBands[ui.cbDemLayer.currentIndex()]
    if rasterLayerBand[1]:
      demLayerBand = topoReader.LayerBand(layer=rasterLayerBand[1],
                                          bandnr=rasterLayerBand[2],
                                          bandname=rasterLayerBand[3] )
      self.process.demLayerBands.append(demLayerBand)
    self.process.outFilePathWithLayerNameAndDrawer = [];
    for (label, lineedit, button, drawer) in self.outShapeFileFormWidgets:
      if lineedit.text():
        self.process.outFilePathWithLayerNameAndDrawer.append((lineedit.text(), self.toLayerName(lineedit, label), drawer))
    self.process.coordRefSystemAsText = ui.leSRS.text()
    self.process.shouldOverride = ui.rbOverride.isChecked()
    self.process.shouldShowLayer = ui.cbDisplayInQgis.isChecked()


  def toLayerName(self, lineeditpath, label):
    return os.path.splitext(os.path.basename(lineeditpath.text()))[0] #+ " - " + label.text()


