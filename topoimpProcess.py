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

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
import qgis.utils
from qgis.gui import QgsMessageBar
import sys
import string
import os.path
import traceback
from . import topoReader
from . import topoDrawer

#??? Vérifier si `QReadWriteLock` est disponible dans PyQt5 (oui, mais à confirmer dans ton environnement)
from PyQt5.QtCore import QReadWriteLock

class ToporobotImporterProcess:

    def __init__(self):
        # Status infos
        self.statusLock = QReadWriteLock()
        self.statusText = ''
        self.statusProgressValue = 0
        self.statusProgressMax = -1
        self.messageBarItem = None
        self.progressBar = None

        # Work parameters
        self.topoTextFilePath = None
        self.topoCoordFilePath = None
        self.mergeMappingFilePath = None
        self.demLayerBands = []
        self.outFilePathWithLayerNameAndDrawer = []
        self.coordRefSystemAsText = None
        self.shouldOverride = False
        self.shouldShowLayer = False

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
            #??? Vérifier si `iface` est accessible dans QGIS 3.44
            iface.mainWindow().statusBar().showMessage(text)
        self.statusText = text
        self.statusLock.unlock()
        QCoreApplication.processEvents()

    def initStatusProgress(self, nbStepsOfProcessing):
        self.statusLock.lockForWrite()
        self.statusProgressMax = nbStepsOfProcessing
        self.statusProgressValue = 0
        #??? Vérifier si `iface` est accessible dans QGIS 3.44
        iface = qgis.utils.iface
        self.messageBarItem = iface.messageBar().createMessage("Start importing")
        self.messageBarItem.setIcon(QIcon(":/plugins/toporobotimporter/images/icon.png"))
        self.progressBar = QProgressBar()
        self.progressBar.setMaximum(nbStepsOfProcessing)
        self.progressBar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
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
        #??? Vérifier si `iface` est accessible dans QGIS 3.44
        iface = qgis.utils.iface
        if self.messageBarItem:
            self.messageBarItem.setText(message)
            # PyQt5 utilise `QgsMessageBar.CRITICAL` (pas `Icon.Critical`)
            self.messageBarItem.setLevel(QgsMessageBar.CRITICAL)
        else:
            # the error comes so early that the message bar is not yet created
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
            if outFilePath:
                nbOutFiles += 1
        nbStepsOfProcessing += nbOutFiles

        # Initialisation de la barre de progression
        self.initStatusProgress(nbStepsOfProcessing)
        self.incStatusProgressValue()  # input validation and progress computing already done

        # read the input files

        self.setStatusText("Reading the input Text file")
        topofile = topoReader.readToporobotText(self.topoTextFilePath)
        self.incStatusProgressValue()
        self.setStatusText("Text file successfully read")

        self.setStatusText("Reading the input Coord file")
        topoReader.readToporobotCoord(self.topoCoordFilePath, topofile)
        self.incStatusProgressValue()
        self.setStatusText("Coord file successfully read")

        if self.demLayerBands:
            self.setStatusText("Reading the input DEM Layers")
            topoReader.readGroundAlti(topofile, self.demLayerBands)
            self.incStatusProgressValue()
            self.setStatusText("DEM Layers successfully read")

        if self.mergeMappingFilePath:
            self.setStatusText("Reading the input Merge mapping file")
            topofiles = topoReader.readMergeMapping(self.mergeMappingFilePath, topofile)
            self.incStatusProgressValue()
            self.setStatusText("Merge mapping file successfully read")
        else:
            topofiles = {topofile.name: topofile}

        self.setStatusText("Input files successfully read")

        # write the output shapefiles

        self.setStatusText("Writing the output files")
        if self.coordRefSystemAsText:
            #??? : Vérifie si QgsCoordinateReferenceSystem accepte toujours une chaîne de caractères en entrée.
            # Compatibilité : En QGIS 3.x, QgsCoordinateReferenceSystem peut accepter une chaîne de caractères (ex: "EPSG:4326").
            # Si des erreurs surviennent, il faudra utiliser une méthode alternative comme QgsCoordinateReferenceSystem.fromEpsgId(4326).
            self.srs = QgsCoordinateReferenceSystem(self.coordRefSystemAsText)
        else:
            self.srs = None

    self.setStatusText("Writing the outputs")

    for (outFilePath, layerName, drawer) in self.outFilePathWithLayerNameAndDrawer:
        if not outFilePath:
            continue
        self.draw(topofiles, drawer, outFilePath, layerName)

    self.setStatusText("Output files successfully written. Import is finished.")

except Exception as e:
    # Gestion des erreurs avec sys et traceback pour un débogage précis.
    exc_type, exc_value, exc_traceback = sys.exc_info()
    #??? : La fonction `unicode()` n'existe pas en Python 3. Utilise `str()` ou retire cette conversion.
    # Compatibilité : En Python 3, `str(e)` suffit pour convertir une exception en chaîne.
    self.error(f"Error {e.__class__.__name__}: {str(e)}")
    #??? : Vérifie si `string.join` est toujours nécessaire ou si `str.join` peut être utilisé directement.
    # Compatibilité : En Python 3, `str.join()` est la méthode standard.
    QgsMessageLog.logMessage(
        "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
        "Toporobot Importer",
        QgsMessageLog.WARNING
    )


def draw(self, topofiles, drawer, outPath, layerName):
    # Vérifie si le fichier ou la couche existe déjà
    existingLayer = getLayerFromDatapath(outPath)
    existingFile = os.path.exists(outPath)
    shouldOverride = self.shouldOverride
    shouldAppend = not shouldOverride

    if existingLayer:
        if existingFile:
            if not existingLayer.startEditing():
                raise IOError(f"Cannot edit the layer {existingLayer.name()}")
            if shouldOverride:
                self.clearLayer(existingLayer)
            self.drawOnLayer(topofiles, drawer, existingLayer)
            if not existingLayer.commitChanges():
                existingLayer.rollBack()
                raise IOError(f"Cannot save the layer {existingLayer.name()}")
        else:
            self.drawOnNewFile(topofiles, drawer, outPath)
            #??? : Vérifie si `dataProvider().dataChanged()` est toujours nécessaire ou si une autre méthode est recommandée.
            # Compatibilité : Cette méthode semble toujours valide en QGIS 3.x, mais à tester pour les performances.
            existingLayer.dataProvider().dataChanged()

    else:  # no such layer in QGIS
        if shouldAppend and existingFile:
            layer = QgsVectorLayer(outPath, layerName, "ogr")
            if not layer.startEditing():
                raise IOError(f"Cannot edit the layer {layer.name()}")
            self.drawOnLayer(topofiles, drawer, layer)
            if not layer.commitChanges():
                layer.rollBack()
                raise IOError(f"Cannot save the layer {layer.name()}")
            QgsProject.instance().addMapLayer(layer)  #???
            # Compatibilité : `QgsMapLayerRegistry.instance()` est déprécié depuis QGIS 3.0. Utilise `QgsProject.instance().addMapLayer()` à la place.
        else:  # override or no existing file
            if existingFile:
                self.deleteShapeFile(outPath)
            self.drawOnNewFile(topofiles, drawer, outPath)
            if self.shouldShowLayer:
                self.displayLayer(outPath, layerName)

    self.incStatusProgressValue()


def deleteShapeFile(self, outPath):
    if not QgsVectorFileWriter.deleteShapeFile(outPath):
        #??? : Vérifie si `os.path.basename(outPath)` est toujours nécessaire ou si une autre méthode est recommandée.
        # Compatibilité : En Python 3, `os.path.basename` est toujours valide.
        raise IOError(f"Cannot delete the shapefile '{os.path.basename(outPath)}'")


def drawOnNewFile(self, topofiles, drawer, outPath):
    writer = QgsVectorFileWriter(outPath, 'UTF-8', drawer.fields(), drawer.wkbType(), self.srs, "ESRI Shapefile")
    if writer.hasError():
        raise IOError(f"Cannot create the shapefile '{os.path.basename(outPath)}'")
    drawer.draw(topofiles, writer)
    #drawer.draw(topofiles, WriterWrapper(writer, os.path.basename(outPath)))
    del writer  # flush and close the output file


def clearLayer(self, layer):
    layer.selectAll()
    if not layer.deleteSelectedFeatures():
        raise IOError(f"Cannot delete the features of the layer {layer.name()}")


def drawOnLayer(self, topofiles, drawer, layer):
    drawer.draw(topofiles, layer)
    # drawer.draw(topofiles, WriterWrapper(layer, layer.name()))


def displayLayer(self, outPath, layerName):
    iface = qgis.utils.iface
    # Vérifie si le chemin se termine par '.shp' et l'ajoute si nécessaire.
    if not outPath.lower().endswith(".shp"):
        outPath = outPath + ".shp"
    if not iface.addVectorLayer(outPath, layerName, "ogr"):
        QgsMessageLog.logMessage(
            f"Cannot add the layer {os.path.basename(outPath)}",
            "Toporobot Importer",
            QgsMessageLog.WARNING
        )
      #QMessageBox.warning(self, self.windowTitle(), u"cannot add the layer "+os.path.basename(outPath))
      
        #??? : La ligne commentée avec QMessageBox est conservée pour référence, mais QMessageBox.warning nécessite un parent (ex: QDialog).
        # Compatibilité : Si tu veux afficher une boîte de dialogue, utilise un parent comme `self` ou `iface.mainWindow()`.
        # Exemple : QMessageBox.warning(iface.mainWindow(), self.windowTitle(), f"Cannot add the layer {os.path.basename(outPath)}")


def getLayerFromDatapath(datapath):
    existingLayer = None
    #??? : Vérifie si `unicode(datapath)` est nécessaire. En Python 3, `str` est déjà Unicode.
    # Compatibilité : En Python 3, `str(datapath)` suffit.
    datapath = os.path.abspath(str(datapath))
    if datapath.lower().endswith(".shp"):
        datapath2 = datapath[:-4]
    else:
        datapath2 = datapath + ".shp"

    #??? : Vérifie si `QgsMapLayerRegistry.instance()` est toujours valide ou si `QgsProject.instance()` doit être utilisé.
    # Compatibilité : `QgsMapLayerRegistry` est déprécié depuis QGIS 3.0. Utilise `QgsProject.instance().mapLayers().values()`.
    for layer in QgsProject.instance().mapLayers().values():
        layerpath = os.path.abspath(str(layer.source()))
        if layerpath == datapath or layerpath == datapath2:
            existingLayer = layer
            break
    return existingLayer


class WriterWrapper:
    """Writer as a Wrapper to detect Error"""

    def __init__(self, writer, outName):
        self.writer = writer
        self.outName = outName

    def addFeature(self, feature):
        if not self.writer.addFeature(feature):
            #??? : Vérifie si `outName` est bien défini ou si une autre variable doit être utilisée.
            # Compatibilité : Si `outName` n'est pas défini, utilise `self.outName`.
            raise IOError(f"Cannot write the feature to {self.outName}")

