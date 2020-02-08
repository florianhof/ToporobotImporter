# -*- coding: utf-8 -*-

import sys, os
packageFolderPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.dirname(packageFolderPath)) # one above to see it as a package
from ToporobotImporter import topoDrawer, topoData

import unittest
import math

quarter = math.pi / 2.0 # == 100 grades

class DummyWriter(object):
    def __init__(self):
        self.features =[]
    def addFeature(self, qgsFeature):
        self.features.append(qgsFeature)

class TopoDrawerTestCase(unittest.TestCase):

    def test_getMeanDir(self):
        self.assertEqual(topoDrawer.getMeanDir(None, None), None)
        self.assertEqual(topoDrawer.getMeanDir(None, quarter), quarter)
        self.assertEqual(topoDrawer.getMeanDir(quarter, None), quarter)
        self.assertEqual(topoDrawer.getMeanDir(quarter, quarter), quarter)
        self.assertEqual(topoDrawer.getMeanDir(0, 0), 0)
        self.assertEqual(topoDrawer.getMeanDir(0, quarter), 0.5*quarter)
        self.assertEqual(topoDrawer.getMeanDir(quarter, 0), 0.5*quarter)
        self.assertEqual(topoDrawer.getMeanDir(3*quarter, 3*quarter), 3*quarter)
        self.assertEqual(topoDrawer.getMeanDir(0, 3*quarter), 3.5*quarter)
        self.assertEqual(topoDrawer.getMeanDir(3*quarter, 0), 3.5*quarter)
        self.assertEqual(topoDrawer.getMeanDir(2*quarter, 3*quarter), 2.5*quarter)
        self.assertEqual(topoDrawer.getMeanDir(2*quarter, 2*quarter), 2*quarter)
        self.assertAlmostEqual(topoDrawer.getMeanDir(0, 1.8*quarter), 0.9*quarter)
        self.assertAlmostEqual(topoDrawer.getMeanDir(0, 2.2*quarter), 3.1*quarter)
        self.assertAlmostEqual(topoDrawer.getMeanDir(0, 3.8*quarter), 3.9*quarter)
        self.assertAlmostEqual(topoDrawer.getMeanDir(3.8*quarter, 0), 3.9*quarter)
        self.assertAlmostEqual(topoDrawer.getMeanDir(0, 0.2*quarter), 0.1*quarter)
        self.assertAlmostEqual(topoDrawer.getMeanDir(0.2*quarter, 0), 0.1*quarter)
        self.assertAlmostEqual(topoDrawer.getMeanDir(2*quarter, 0.2*quarter), 1.1*quarter)
        self.assertAlmostEqual(topoDrawer.getMeanDir(0.2*quarter, 2*quarter), 1.1*quarter)
        self.assertAlmostEqual(topoDrawer.getMeanDir(2*quarter, 3.8*quarter), 2.9*quarter)

    def test_StationsDrawer_Empty(self):
        drawer = topoDrawer.StationsDrawer()
        self._test_Drawer_Empty(drawer)

    def test_AimsDrawer_Empty(self):
        drawer = topoDrawer.AimsDrawer()
        self._test_Drawer_Empty(drawer)

    def test_AimsSurfaceDrawer_Empty(self):
        drawer = topoDrawer.AimsSurfaceDrawer()
        self._test_Drawer_Empty(drawer)

    def test_SeriesDrawer_Empty(self):
        drawer = topoDrawer.SeriesDrawer()
        self._test_Drawer_Empty(drawer)

    def test_SeriesSurfaceDrawer_Empty(self):
        drawer = topoDrawer.SeriesSurfaceDrawer()
        self._test_Drawer_Empty(drawer)

    def _test_Drawer_Empty(self, drawer):
        self.assertNotEqual(drawer.wkbType(), None)
        self.assertNotEqual(drawer.fields(), None)
        topofiles = {'EmptyCave.Text': topoData.TopoFile()}
        writer = DummyWriter()
        drawer.draw(topofiles, writer)
        self.assertEqual(writer.features, [])
        return writer.features

    def test_StationsDrawer_TwoShots(self):
        drawer = topoDrawer.StationsDrawer()
        features = self._test_Drawer_TwoShots(drawer)
        self.assertEqual(len(features), 3)

    def test_AimsDrawer_TwoShots(self):
        drawer = topoDrawer.AimsDrawer()
        features = self._test_Drawer_TwoShots(drawer)
        self.assertEqual(len(features), 2)

    def test_AimsSurfaceDrawer_TwoShots(self):
        drawer = topoDrawer.AimsSurfaceDrawer()
        features = self._test_Drawer_TwoShots(drawer)
        self.assertEqual(len(features), 2)

    def test_SeriesDrawer_TwoShots(self):
        drawer = topoDrawer.SeriesDrawer()
        features = self._test_Drawer_TwoShots(drawer)
        self.assertEqual(len(features), 1)

    def test_SeriesSurfaceDrawer_TwoShots(self):
        drawer = topoDrawer.SeriesSurfaceDrawer()
        features = self._test_Drawer_TwoShots(drawer)
        self.assertEqual(len(features), 1)

    def _test_Drawer_TwoShots(self, drawer):
        self.assertNotEqual(drawer.wkbType(), None)
        self.assertNotEqual(drawer.fields(), None)
        topofiles = getSimpleTopoFiles()
        writer = DummyWriter()
        drawer.draw(topofiles, writer)
        return writer.features

revolution = 2.0 * math.pi

def getSimpleTopoFiles():
    topofile = topoData.TopoFile()
    topofiles = {'SimpleCave.Text': topofile}
    trip = topoData.TopoTrip(1)
    trip.date = '2019-12-28'
    code = topoData.TopoCode(1)
    code.topofile = topofile
    code.visible = True
    code.computeLengthInMeter = (lambda length: length)
    code.computeDirectionInRadian = (lambda direction: revolution * direction / 400)
    serie = topoData.TopoSerie(1)
    serie.topofile = topofile
    serie.name = "gallery of the test"
    station0 = topoData.TopoStation(serie)
    station0.left = 0.8
    station0.right = 0.5
    station0.top = 3.6
    station0.bottom = 1.4
    station0.code = code
    station0.trip = trip
    station0.coordX = 0
    station0.coordY = 0
    station0.coordZ = 560
    station1 = topoData.TopoStation(serie)
    station1.distance = 6.73
    station1.direction = 100
    station1.slope = -3
    station1.left = 0.2
    station1.right = 0.3
    station1.top = 1.2
    station1.bottom = 0.7
    station1.code = code
    station1.trip = trip
    station1.coordX = station1.distance
    station1.coordY = 0
    station1.coordZ = 559
    station2 = topoData.TopoStation(serie)
    station2.distance = 1.32
    station2.direction = 142
    station2.slope = -27
    station2.left = 0.08
    station2.right = 0.11
    station2.top = 0.2
    station2.bottom = 0
    station2.code = code
    station2.trip = trip
    station2.coordX = station1.distance + 0.8
    station2.coordY = -0.3
    station2.coordZ = 558.8
    return topofiles


if __name__ == '__main__':
    unittest.main()

