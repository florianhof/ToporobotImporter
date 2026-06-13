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

from PyQt5.QtCore import Qt, QUrl, QRegExp
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox
from PyQt5.QtGui import QDesktopServices, QRegExpValidator
from .ui_toporobotimporter import Ui_ToporobotImporter
from qgis.core import QgsProject, QgsMapLayer, QgsCoordinateReferenceSystem
from qgis.gui import QgsGenericProjectionSelector
import qgis.utils
import os

from .topoimpProcess import ToporobotImporterProcess, getLayerFromDatapath
from . import topoReader
from . import topoDrawer


class ToporobotImporterDialog(QDialog):

    def __init__(self):
        super().__init__()
    # Set up the user interface from Designer.
        self.ui = Ui_ToporobotImporter()
        self.ui.setupUi(self)

        # Répertoires par défaut
        self.lastInputDirectory = os.getenv('USERPROFILE') or os.getenv('HOME') or "."
        self.lastOutputDirectory = QgsProject.instance().homePath() or "."
        self.process = None
        ui = self.ui

    # set validators where required
            # Validateur pour le champ SRS (ex: epsg:4326 ou +proj=...)
        regex = QRegExp("(^epsg:{1}\\s*\\d+)|(^\\+proj.*)", Qt.CaseInsensitive)
        ui.leSRS.setValidator(QRegExpValidator(regex, ui.leSRS))

    # connect the buttons to actions
            # Connexions des boutons aux fonctions de navigation
        ui.bBrowseToporobotText.clicked.connect(self.browseForInToporobotTextFileFunction(ui.leToporobotText))
        ui.bBrowseToporobotCoord.clicked.connect(self.browseForInToporobotCoordFileFunction(ui.leToporobotCoord))
        ui.bBrowseMergeMapping.clicked.connect(self.browseForInMergeMappingFileFunction(ui.leMergeMapping))

        # Liste des widgets de sortie shapefile avec leur drawer associé
        self.outShapeFileFormWidgets = [
            (ui.lbOutPoints, ui.leOutPoints, ui.bBrowseOutPoints, topoDrawer.StationsDrawer()),
            (ui.lbOutAims, ui.leOutAims, ui.bBrowseOutAims, topoDrawer.AimsDrawer()),
            (ui.lbOutAimsSurface, ui.leOutAimsSurface, ui.bBrowseOutAimsSurface, topoDrawer.AimsSurfaceDrawer()),
            (ui.lbOutSeries, ui.leOutSeries, ui.bBrowseOutSeries, topoDrawer.SeriesDrawer()),
            (ui.lbOutSeriesBorder, ui.leOutSeriesBorder, ui.bBrowseOutSeriesBorder, topoDrawer.SeriesSurfaceDrawer())
        ]
        for (label, lineedit, button, drawer) in self.outShapeFileFormWidgets:
            button.clicked.connect(self.browseForOutShapefileFunction(lineedit))

        ui.bSRS.clicked.connect(self.browseForSRS)
        ui.buttonBox.helpRequested.connect(self.showHelp)


    def show(self):
        ui = self.ui

        # init the dropdown with the possibly DEM layers
        currentLayerBand = None
        if ui.cbDemLayer.currentIndex() > 0:
            currentLayerBand = ui.cbDemLayer.currentText()

        # Vide le combo
        ui.cbDemLayer.clear()
        ui.cbDemLayer.addItem('----------', None)

        # Ajout des couches raster 1 bande (DEM)
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.RasterLayer:
                if layer.bandCount() == 1:
                    rasterLayerBand = topoReader.LayerBand(layer, 1, layer.bandName(1))
                    ui.cbDemLayer.addItem(layer.name(), rasterLayerBand)

        # Ajout des couches raster multi-bandes
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayer.RasterLayer:
                if layer.bandCount() > 1:
                    for j in range(layer.bandCount()):
                        rasterLayerBand = topoReader.LayerBand(layer, j + 1, layer.bandName(j + 1))
                        ui.cbDemLayer.addItem(f"{layer.name()} / {layer.bandName(j + 1)}", rasterLayerBand)

        # Restaure la sélection si possible
        if currentLayerBand:
            index = ui.cbDemLayer.findText(currentLayerBand)
            if index != -1:
                ui.cbDemLayer.setCurrentIndex(index)
            else:
                ui.cbDemLayer.setCurrentIndex(0)
        else:
            ui.cbDemLayer.setCurrentIndex(0)

        self.repaint()

        # now really show
        super().show()

    def browseForInToporobotTextFileFunction(self, lineedit):
        return lambda: self.browseForInFile(lineedit, "Input Toporobot .Text file", "Toporobot (*.Text);;All (*.*)")

    def browseForInToporobotCoordFileFunction(self, lineedit):
        return lambda: self.browseForInFile(lineedit, "Input Toporobot .Coord file", "Toporobot (*.Coord);;All (*.*)")

    def browseForInMergeMappingFileFunction(self, lineedit):
        return lambda: self.browseForInFile(lineedit, "Input Merge mapping file", "Comma-separated values (*.csv);;All (*.*)")

    def browseForInFile(self, lineedit, caption, selectedFilter):
        filename, _ = QFileDialog.getOpenFileName(self, caption, self.lastInputDirectory, selectedFilter)
        if filename:
            from PyQt5.QtCore import QFileInfo
            fileinfo = QFileInfo(filename)
            lineedit.clear()
            lineedit.setText(fileinfo.absoluteFilePath())
            self.lastInputDirectory = fileinfo.absolutePath()

def browseForOutShapefile(self, lineedit):
    """Ouvre une boîte de dialogue pour choisir un fichier de sortie Shapefile."""
    filename, _ = QFileDialog.getSaveFileName(
        self,
        "Output Shapefile",
        self.lastOutputDirectory,
        "Shapefiles (*.shp)"
    )
    if filename:
        # Ajoute l'extension .shp si elle est manquante
        if not filename.lower().endswith(".shp"):
            filename += ".shp"
        fileinfo = QFileInfo(filename)
        lineedit.clear()
        lineedit.setText(fileinfo.absoluteFilePath())
        self.lastOutputDirectory = fileinfo.absolutePath()

def browseForOutShapefileFunction(self, lineedit):
    """Retourne une lambda pour appeler browseForOutShapefile avec le lineedit."""
    return lambda: self.browseForOutShapefile(lineedit)

def browseForSRS(self):
    """Ouvre le sélecteur de projection pour choisir un SRS."""
    srsSelector = QgsGenericProjectionSelector(self)
    current_text = self.ui.leSRS.text()
    if current_text:
        srsSelector.setSelectedCrsId(QgsCoordinateReferenceSystem().fromProj4(current_text).authid())
    if srsSelector.exec_():
        selected_crs = srsSelector.selectedCrs()
        self.ui.leSRS.clear()
        #??? : Vérifie si `selectedCrs().toProj4()` est la méthode correcte pour obtenir la chaîne Proj4.
        # Compatibilité : En QGIS 3.x, `selectedCrs().toProj4()` devrait fonctionner.
        self.ui.leSRS.insert(selected_crs.toProj4())


def done(self, resultCode):
    """Gère la fermeture du dialogue."""
    self.process = None
    if resultCode == QDialog.Accepted:
        if self.validateInputs():
            self.defineProcess()
        else:
            return  # Rester sur le dialogue si les entrées ne sont pas valides
    super().done(resultCode)  # Ferme le dialogue

def showHelp(self):
    """Affiche la page d'aide du plugin."""
    # Chemin vers le fichier d'aide du plugin
    help_file = os.path.join(
        qgis.utils.pluginDirectory('ToporobotImporter'),
        "help",
        "index.html"
    )
    help_file = QUrl.fromLocalFile(help_file).toString()
    QDesktopServices.openUrl(QUrl(help_file))



def validateInputs(self):
    """Valide les entrées utilisateur et retourne une liste d'erreurs."""
    errorMsgs = []
    ui = self.ui

    # Vérification des fichiers d'entrée
    if not ui.leToporobotText.text():
        errorMsgs.append("The Toporobot .Text file has to be filled")
    if not ui.leToporobotCoord.text():
        errorMsgs.append("The Toporobot .Coord file has to be filled")

    # Vérification des fichiers de sortie
    nbOutFiles = 0
    for (label, lineedit, button, drawer) in self.outShapeFileFormWidgets:
        if lineedit.text():
            outPath = str(lineedit.text())  # Remplace unicode() par str()
            nbOutFiles += 1
            existingLayer = getLayerFromDatapath(outPath)
            if (not existingLayer) and ui.rbAppend.isChecked() and os.path.exists(outPath):
                existingLayer = QgsVectorLayer(outPath, None, "ogr")
            if existingLayer:
                # Comparaison des types de géométrie
                if existingLayer.wkbType() != drawer.wkbType():  # <> remplacé par !=
                    errorMsgs.append(f"Cannot append to the file \"{os.path.basename(outPath)}\" because its type is not compatible")
                del existingLayer

    if nbOutFiles == 0:
        errorMsgs.append("No output shapefile has been filled")

    # Affichage des erreurs si nécessaire
    if errorMsgs:
        QMessageBox.information(self, self.windowTitle(), "\n".join(errorMsgs))
        return False
    return True


def defineProcess(self):
    """Initialise le processus de traitement avec les paramètres utilisateur."""
    self.process = ToporobotImporterProcess()
    ui = self.ui

    # Chemins des fichiers d'entrée
    self.process.topoTextFilePath = str(ui.leToporobotText.text())
    self.process.topoCoordFilePath = str(ui.leToporobotCoord.text())
    self.process.mergeMappingFilePath = str(ui.leMergeMapping.text())

    # Couches DEM sélectionnées
    self.process.demLayerBands = []
    if ui.cbDemLayer.currentIndex() >= 0:
        rasterLayerBand = ui.cbDemLayer.itemData(ui.cbDemLayer.currentIndex())
        if rasterLayerBand:
            self.process.demLayerBands.append(rasterLayerBand)

    # Chemins de sortie et leurs propriétés
    self.process.outFilePathWithLayerNameAndDrawer = []
    for (label, lineedit, button, drawer) in self.outShapeFileFormWidgets:
        if lineedit.text():
            self.process.outFilePathWithLayerNameAndDrawer.append(
                (str(lineedit.text()), self.toLayerName(lineedit, label), drawer)
            )

    # Système de coordonnées et options
    self.process.coordRefSystemAsText = str(ui.leSRS.text())
    self.process.shouldOverride = ui.rbOverride.isChecked()
    self.process.shouldShowLayer = ui.cbDisplayInQgis.isChecked()

def toLayerName(self, lineeditpath, label):
    """Génère un nom de couche à partir du chemin du fichier."""
    # Remplace les caractères non valides pour un nom de couche
    base_name = os.path.splitext(os.path.basename(str(lineeditpath.text())))
    return base_name  # Optionnel : + " - " + label.text()

