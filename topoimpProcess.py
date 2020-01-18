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
from builtins import object
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.core import *
import qgis.utils
from qgis.gui import QgsMessageBar
import sys
import string
import os.path
import traceback
from . import topoReader
from . import topoDrawer

class ToporobotImporterProcess(object):

  def __init__(self):

    # Status infos
    self.statusLock = QReadWriteLock()
    self.statusText = ''
    self.statusProgressValue = 0
    self.statusProgressMax = -1
    self.messageBarItem = None
    self.progressBar = None

    # Work parameters
    self.topoTextFilePath = None;
    self.topoCoordFilePath = None;
    self.mergeMappingFilePath = None;
    self.demLayerBands = [];
    self.outFilePathWithLayerNameAndDrawer = [];
    self.coordRefSystemAsText = None;
    self.shouldOverride = False;
    self.shouldShowLayer = False;


  def getStatus(self):
    self.statusLock.lockForRead()
    result = (self.statusText, self.statusProgressValue, self.statusProgressMax)
    self.statusLock.unlock()
    return result

  def setStatusText(self, text):
    self.statusLock.lockForWrite()
    if self.messageBarItem:
      self.messageBarItem.setText(text)
    else:
      iface.mainWindow().statusBar().showMessage(text)
    self.statusText = text
    self.statusLock.unlock()
    QCoreApplication.processEvents()

  def initStatusProgress(self, nbStepsOfProcessing):
    self.statusLock.lockForWrite()
    self.statusProgressMax = nbStepsOfProcessing
    self.statusProgressValue = 0
    iface = qgis.utils.iface
    self.messageBarItem = iface.messageBar().createMessage("Start importing")
    self.messageBarItem.setIcon(QIcon(":/plugins/toporobotimporter/images/icon.png"))
    self.progressBar = QProgressBar()
    self.progressBar.setMaximum(nbStepsOfProcessing)
    self.progressBar.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
    self.messageBarItem.layout().addWidget(self.progressBar)
    iface.messageBar().pushWidget(self.messageBarItem, level=QgsMessageBar.INFO)
    self.statusLock.unlock()

  def incStatusProgressValue(self):
    self.statusLock.lockForWrite()
    self.statusProgressValue += 1
    self.progressBar.setValue(self.statusProgressValue)
    self.statusLock.unlock()
    QCoreApplication.processEvents()

  def error(self, message):
    iface = qgis.utils.iface
    if self.messageBarItem:
      self.messageBarItem.setText(message)
      self.messageBarItem.setLevel(iface.messageBar().CRITICAL)
    else: # the error comes so early that the message bar not yet created is
      iface.messageBar().pushMessage("Toporobot Importer", message, level=QgsMessageBar.CRITICAL)


  def run(self):
    try:

      # compute the number of steps

      nbStepsOfProcessing = 3 # validate input, read .Text, read .Coord
      if self.mergeMappingFilePath:
        nbStepsOfProcessing += 1
      if self.demLayerBands:
        nbStepsOfProcessing += 1
      nbOutFiles = 0
      for (outFilePath, layerName, drawer) in self.outFilePathWithLayerNameAndDrawer:
        if outFilePath: nbOutFiles += 1
      nbStepsOfProcessing += nbOutFiles
      self.initStatusProgress(nbStepsOfProcessing)
      self.incStatusProgressValue() # input validation and progress computing already done

      # read the input files

      self.setStatusText(u"Reading the input Text file")
      topofile = topoReader.readToporobotText(self.topoTextFilePath)
      self.incStatusProgressValue()
      self.setStatusText(u"Textfile successfully readen")

      self.setStatusText(u"Reading the input Coord file")
      topoReader.readToporobotCoord(self.topoCoordFilePath, topofile)
      self.incStatusProgressValue()
      self.setStatusText(u"Coord file successfully readen")

      if self.demLayerBands:
        self.setStatusText(u"Reading the input DEM Layers")
        topoReader.readGroundAlti(topofile, self.demLayerBands)
        self.incStatusProgressValue()
        self.setStatusText(u"DEM Layers successfully readen")

      if self.mergeMappingFilePath:
        self.setStatusText(u"Reading the input Merge mapping file")
        topofiles = topoReader.readMergeMapping(self.mergeMappingFilePath, topofile)
        self.incStatusProgressValue()
        self.setStatusText(u"Merge mapping file successfully readen")
      else:
        topofiles = {topofile.name: topofile}

      self.setStatusText(u"Input files successfully readen")

      # write the output shapefiles

      self.setStatusText(u"Writting the output files")
      if self.coordRefSystemAsText:
        self.srs = QgsCoordinateReferenceSystem(self.coordRefSystemAsText)
      else:
        self.srs = None

      self.setStatusText(u"Writing the outputs")

      for (outFilePath, layerName, drawer) in self.outFilePathWithLayerNameAndDrawer:
        if not outFilePath: continue
        self.draw(topofiles, drawer, outFilePath, layerName)

      self.setStatusText(u"Output files successfully written. Import is finished. ")

    except Exception as e:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      self.error(u"Error "+e.__class__.__name__+u": "+str(e))
      QgsMessageLog.logMessage(string.join(traceback.format_exception(exc_type, exc_value, exc_traceback), ""),
                               "Toporobot Importer", QgsMessageLog.WARNING)


  def draw(self, topofiles, drawer, outPath, layerName):

    existingLayer = getLayerFromDatapath(outPath)
    existingFile = os.path.exists(outPath)
    shouldOverride = self.shouldOverride
    shouldAppend = not shouldOverride

    if existingLayer:
      if existingFile:
        if not existingLayer.startEditing():
          IOError("cannot edit the layer "+existingLayer.name())
        if shouldOverride:
          self.clearLayer(existingLayer)
        self.drawOnLayer(topofiles, drawer, existingLayer)
        if not existingLayer.commitChanges():
          existingLayer.rollBack()
          IOError("cannot save the layer "+existingLayer.name())
      else:
        self.drawOnNewFile(topofiles, drawer, outPath)
        existingLayer.dataProvider().dataChanged()

    else: # no such layer in QGIS
      if shouldAppend and existingFile:
        layer = QgsVectorLayer(outPath, layerName, "ogr")
        if not layer.startEditing():
          IOError("cannot edit the layer "+layer.name())
        self.drawOnLayer(topofiles, drawer, layer)
        if not layer.commitChanges():
          layer.rollBack()
          IOError("cannot save the layer "+layer.name())
        QgsMapLayerRegistry.instance().addMapLayer(layer)
        #del layer
      else: # override or no existing file
        if existingFile:
          self.deleteShapeFile(outPath)
        self.drawOnNewFile(topofiles, drawer, outPath)
        if self.shouldShowLayer:
          self.displayLayer(outPath, layerName)

    self.incStatusProgressValue()


  def deleteShapeFile(self, outPath):
    if not QgsVectorFileWriter.deleteShapeFile(outPath):
      raise IOError(u"cannot delete the shapefile \'"+os.path.basename(outPath)+u"\'")


  def drawOnNewFile(self, topofiles, drawer, outPath):
    writer = QgsVectorFileWriter(outPath, 'UTF-8', drawer.fields(), drawer.wkbType(), self.srs, "ESRI Shapefile")
    if writer.hasError():
      raise IOError(u"cannot create the shapefile \'"+os.path.basename(outPath)+u"\'")
    drawer.draw(topofiles, writer)
    #drawer.draw(topofiles, WriterWrapper(writer, os.path.basename(outPath)))
    del writer # flush and close the output file


  def clearLayer(self, layer):
    layer.selectAll()
    if not layer.deleteSelectedFeatures():
      raise IOError("cannot delete the features of the layer "+layer.name())


  def drawOnLayer(self, topofiles, drawer, layer):
    drawer.draw(topofiles, layer)
    #drawer.draw(topofiles, WriterWrapper(layer, layer.name()))


  def displayLayer(self, outPath, layerName):
    iface = qgis.utils.iface
    if not outPath[-4:].lower().endswith(".shp"):
      outPath = outPath + ".shp"
    if not iface.addVectorLayer(outPath, layerName, "ogr"):
      QgsMessageLog.logMessage(u"cannot add the layer "+os.path.basename(outPath),
                               "Toporobot Importer", QgsMessageLog.WARNING)
      #QMessageBox.warning(self, self.windowTitle(), u"cannot add the layer "+os.path.basename(outPath))


def getLayerFromDatapath(datapath):
    existingLayer = None
    datapath = os.path.abspath(str(datapath))
    if datapath[-4:].lower().endswith(".shp"):
      datapath2 = datapath[0:-4]
    else:
      datapath2 = datapath + ".shp"
    for layer in list(QgsMapLayerRegistry.instance().mapLayers().values()):
      layerpath = os.path.abspath(str(layer.source()))
      if layerpath == datapath or layerpath == datapath2:
        existingLayer = layer
        break
    return existingLayer


class WriterWrapper(object):
  """Writer as a Wrapper to detect Error"""

  def __init__(self, writer, outName):
    self.writer = writer
    self.outName = outName

  def addFeature(self, feature):
    if not self.writer.addFeature(feature):
      raise IOError("cannot write the feature to "+outName)

