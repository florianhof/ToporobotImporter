# -*- coding: utf-8 -*-

import sys, os
packageFolderPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.dirname(packageFolderPath)) # one above to see it as a package
from ToporobotImporter import topoimpProcess, topoDrawer
from ToporobotImporter.tests.topoDrawer_test import getSimpleTopoFiles
from ToporobotImporter.tests.topoReader_test import extraFile

import unittest
from qgis.core import QgsCoordinateReferenceSystem, QgsVectorLayer

class ToporobotImporterProcessTestCase(unittest.TestCase):

    def test_init(self):
        topoimpProcess.ToporobotImporterProcess()

    def test_drawOnNewFile(self):
        process = topoimpProcess.ToporobotImporterProcess()
        process.srs = QgsCoordinateReferenceSystem()
        drawer = topoDrawer.AimsSurfaceDrawer()
        process.drawOnNewFile(getSimpleTopoFiles(), drawer, "out.shp")

    def test_drawOnLayer(self):
        process = topoimpProcess.ToporobotImporterProcess()
        drawer = topoDrawer.AimsSurfaceDrawer()
        process.drawOnLayer(getSimpleTopoFiles(), drawer, QgsVectorLayer())

    def test_run_SampleFiles(self):
        process = topoimpProcess.ToporobotImporterProcess()
        process.topoTextFilePath = extraFile('CaveMerged.Text')
        process.topoCoordFilePath = extraFile('CaveMerged.Coord')
        process.mergeMappingFilePath = extraFile('CaveMerged-MergeInfo.csv')
        process.run()


if __name__ == '__main__':
    unittest.main()
