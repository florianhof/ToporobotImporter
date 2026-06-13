# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ToporobotImporter
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
from PyQt5.QtWidgets import *
from qgis.core import *
# Initialize Qt resources from file resources.py
from . import resources_rc
# Import the code for the dialog
from .topoimpDialog import ToporobotImporterDialog
import os.path

class ToporobotImporterPlugin:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]  #??? Vérifier si cette ligne peut lever une exception si "locale/userLocale" n'existe pas
        localePath = os.path.join(self.plugin_dir, 'i18n', 'toporobotimporter_{0}.qm'.format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            #??? Vérifier si cette méthode est toujours valide dans Qt5
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = ToporobotImporterDialog()

    def initGui(self):
        # Create action that will start plugin configuration
        #??? Vérifier si le chemin de l'icône est toujours valide dans QGIS 3.44
        self.action = QAction(
            QIcon(":/plugins/toporobotimporter/images/icon.png"),
            "Toporobot Importer", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        #??? Vérifier si ces méthodes sont toujours valides dans QGIS 3.44
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Import", self.action)

    def unload(self):
        # Remove the plugin menu item and icon
        #??? Vérifier si ces méthodes sont toujours valides dans QGIS 3.44
        self.iface.removePluginMenu("&Import", self.action)
        self.iface.removeToolBarIcon(self.action)

    # run method that performs all the real work
    def run(self):
        # show the dialog
        self.dlg.setModal(True)
        self.dlg.show()
        # Run the dialog event loop
        #??? Vérifier si exec_() est toujours valide dans Qt5 ou si exec() doit être utilisé
        result = self.dlg.exec_()

        # See if OK was pressed
        if result == 1:
            # do something useful
            #??? Vérifier si cette méthode est toujours valide dans le contexte de QGIS 3.44
            self.dlg.process.run()  # in the same thread, otherwise there are problems

