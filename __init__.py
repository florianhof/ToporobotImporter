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
 This script initializes the plugin, making it known to QGIS.
"""

def classFactory(iface):
    # load ToporobotImporter class from file ToporobotImporter
    from topoimpPlugin import ToporobotImporterPlugin
    return ToporobotImporterPlugin(iface)
