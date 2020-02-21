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

from builtins import str
from builtins import object
from qgis.PyQt.QtCore import Qt, QCoreApplication, QReadWriteLock
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QProgressBar
from qgis.core import Qgis, QgsMessageLog, QgsProject, QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateReferenceSystem
import qgis.utils
import sys
import os.path
import traceback
from . import topoReader
from . import topoDrawer

class ToporobotImporterProcess(object):

  def __init__(self):

    # Work parameters
    self.topoTextFilePath = None
    self.topoCoordFilePath = None
    self.mergeMappingFilePath = None
    self.encoding = None
    self.demLayerBands = []
    self.outFilePathWithLayerNameAndDrawer = []
    self.coordRefSystem = None
    self.shouldOverride = False
    self.shouldShowLayer = False

    # Status infos
    self.statusLock = QReadWriteLock()
    self.statusText = ''
    self.statusProgressValue = 0
    self.statusProgressMax = -1
    self.messageBarItem = None
    self.progressBar = None


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
      iface = qgis.utils.iface
      if iface is not None:
        iface.mainWindow().statusBar().showMessage(text)
    self.statusText = text
    self.statusLock.unlock()
    QCoreApplication.processEvents()

  def initStatusProgress(self, nbStepsOfProcessing):
    self.statusLock.lockForWrite()
    self.statusProgressMax = nbStepsOfProcessing
    self.statusProgressValue = 0
    iface = qgis.utils.iface
    if iface is not None:
      self.messageBarItem = iface.messageBar().createMessage("Start importing")
      self.messageBarItem.setIcon(QIcon(":/plugins/toporobotimporter/images/icon.png"))
      self.progressBar = QProgressBar()
      self.progressBar.setMaximum(nbStepsOfProcessing)
      self.progressBar.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
      self.messageBarItem.layout().addWidget(self.progressBar)
      iface.messageBar().pushWidget(self.messageBarItem, level=Qgis.MessageLevel.Info)
    self.statusLock.unlock()

  def incStatusProgressValue(self):
    self.statusLock.lockForWrite()
    self.statusProgressValue += 1
    if self.progressBar:
      self.progressBar.setValue(self.statusProgressValue)
    self.statusLock.unlock()
    QCoreApplication.processEvents()

  def error(self, message):
    iface = qgis.utils.iface
    if self.messageBarItem:
      self.messageBarItem.setText(message)
      self.messageBarItem.setLevel(Qgis.MessageLevel.Critical)
    else: # the error comes so early that the message bar not yet created is
      iface.messageBar().pushMessage("Toporobot Importer", message, level=Qgis.MessageLevel.Critical)


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

      self.setStatusText("Reading the input Text file")
      topofile = topoReader.readToporobotText(self.topoTextFilePath, self.encoding)
      self.incStatusProgressValue()
      self.setStatusText("Textfile successfully readen")

      self.setStatusText("Reading the input Coord file")
      topoReader.readToporobotCoord(self.topoCoordFilePath, topofile)
      self.incStatusProgressValue()
      self.setStatusText("Coord file successfully readen")

      if self.demLayerBands:
        self.setStatusText("Reading the input DEM Layers")
        topoReader.readGroundAlti(topofile, self.demLayerBands)
        self.incStatusProgressValue()
        self.setStatusText("DEM Layers successfully readen")

      if self.mergeMappingFilePath:
        self.setStatusText("Reading the input Merge mapping file")
        topofiles = topoReader.readMergeMapping(self.mergeMappingFilePath, topofile)
        self.incStatusProgressValue()
        self.setStatusText("Merge mapping file successfully readen")
      else:
        topofiles = {topofile.name: topofile}

      self.setStatusText("Input files successfully readen")

      # write the output shapefiles

      self.setStatusText("Writting the output files")
      if not self.coordRefSystem:
        self.coordRefSystem = QgsCoordinateReferenceSystem()

      self.setStatusText("Writing the outputs")

      for (outFilePath, layerName, drawer) in self.outFilePathWithLayerNameAndDrawer:
        if not outFilePath: continue
        self.draw(topofiles, drawer, outFilePath, layerName)

      self.setStatusText("Output files successfully written. Import is finished. ")

    except Exception as e:
      exc_type, exc_value, exc_traceback = sys.exc_info()
      if qgis.utils.iface is None:
          raise e
      else:
        self.error("Error "+e.__class__.__name__+": "+str(e))
        QgsMessageLog.logMessage("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
                                 "Toporobot Importer", Qgis.MessageLevel.Warning)


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
        QgsProject.instance().addMapLayer(layer)
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
      raise IOError("cannot delete the shapefile \'"+os.path.basename(outPath)+"\'")


  def drawOnNewFile(self, topofiles, drawer, outPath):
    writer = QgsVectorFileWriter(outPath, 'UTF-8', drawer.fields(), drawer.wkbType(), self.coordRefSystem, "ESRI Shapefile")
    if writer.hasError():
      raise IOError("cannot create the shapefile \'"+os.path.basename(outPath)+"\'")
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
      QgsMessageLog.logMessage("cannot add the layer "+os.path.basename(outPath),
                               "Toporobot Importer", QgsMessageLog.WARNING)
      #QMessageBox.warning(self, self.windowTitle(), "cannot add the layer "+os.path.basename(outPath))


def getLayerFromDatapath(datapath):
    existingLayer = None
    datapath = os.path.abspath(str(datapath))
    if datapath[-4:].lower().endswith(".shp"):
      datapath2 = datapath[0:-4]
    else:
      datapath2 = datapath + ".shp"
    for layer in list(QgsProject.instance().mapLayers().values()):
      layerpath = os.path.abspath(str(layer.source()))
      if layerpath == datapath or layerpath == datapath2:
        existingLayer = layer
        break
    return existingLayer


class WriterWrapper(object):
  """Writer as a Wrapper to detect Error"""

  outName = None
  
  def __init__(self, writer, outName):
    self.writer = writer
    self.outName = outName

  def addFeature(self, feature):
    if not self.writer.addFeature(feature):
      raise IOError("cannot write the feature to "+self.outName)

