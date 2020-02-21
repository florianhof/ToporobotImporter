# -*- coding: utf-8 -*-

import sys, os
packageFolderPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.dirname(packageFolderPath)) # one above to see it as a package
from ToporobotImporter import topoData, topoReader

import unittest
import math
from qgis.core import QgsRasterLayer

quarter = math.pi / 2.0 # == 100 grades

def extraFile(filename):
    return os.path.join(packageFolderPath, 'extras', filename)

tmpfolderpath = os.path.join(packageFolderPath, "tmp")
if not os.path.exists(tmpfolderpath):
    os.makedirs(tmpfolderpath)

class TopoReaderTestCase(unittest.TestCase):

    def getComputeDirectionInRadian(self, directionUnit):
        code = topoData.TopoCode(1)
        code.directionUnit = directionUnit
        return topoReader.getComputeDirectionInRadian(code)

    def test_getComputeDirectionInRadian_FromGrade(self):
        computeDirectionInRadian = self.getComputeDirectionInRadian(400)
        self.assertEqual(computeDirectionInRadian(0), 0)
        self.assertEqual(computeDirectionInRadian(100), quarter)
        self.assertEqual(computeDirectionInRadian(347), 3.47*quarter)

        computeDirectionInRadian = self.getComputeDirectionInRadian(399)
        self.assertEqual(computeDirectionInRadian(100), quarter)

    def test_getComputeDirectionInRadian_FromGradeReversed(self):
        computeDirectionInRadian = self.getComputeDirectionInRadian(390)
        self.assertEqual(computeDirectionInRadian(300), quarter)
        self.assertEqual(computeDirectionInRadian(147), 3.47*quarter)

    def test_getComputeDirectionInRadian_FromDegree(self):
        computeDirectionInRadian = self.getComputeDirectionInRadian(360)
        self.assertEqual(computeDirectionInRadian(90), quarter)

    def test_getComputeDirectionInRadian_FromDegreeReversed(self):
        computeDirectionInRadian = self.getComputeDirectionInRadian(350)
        self.assertEqual(computeDirectionInRadian(270), quarter)

        computeDirectionInRadian = self.getComputeDirectionInRadian(347)
        self.assertEqual(computeDirectionInRadian(270), quarter)

    def test_getComputeDirectionInRadian_FromUnknownUnit(self):
        with self.assertRaisesRegex(ValueError, "'1'"):
            self.getComputeDirectionInRadian(1)

    def getComputeLengthInMeter(self, directionUnit):
        code = topoData.TopoCode(1)
        code.directionUnit = directionUnit
        return topoReader.getComputeLengthInMeter(code)

    def test_getComputeLengthInMeter_FromMeter(self):
        computeLengthInMeter = self.getComputeLengthInMeter(400)
        self.assertEqual(computeLengthInMeter(0), 0)
        self.assertEqual(computeLengthInMeter(1.83), 1.83)

        computeLengthInMeter = self.getComputeLengthInMeter(399)
        self.assertEqual(computeLengthInMeter(1.83), 1.83)
        
    def test_getComputeLengthInMeter_FromFeet(self):
        computeLengthInMeter = self.getComputeLengthInMeter(398)
        self.assertEqual(computeLengthInMeter(0), 0)
        self.assertAlmostEqual(computeLengthInMeter(6), 1.83, 2)
        
        computeLengthInMeter = self.getComputeLengthInMeter(397)
        self.assertEqual(computeLengthInMeter(0), 0)
        self.assertAlmostEqual(computeLengthInMeter(6), 1.83, 2)
        self.assertAlmostEqual(computeLengthInMeter(6.1), 1.859, 2)
        self.assertEqual(computeLengthInMeter(0.5), 0.1524)

    def test_getComputeLengthInMeter_FromUnknownUnit(self):
        with self.assertRaisesRegex(ValueError, "'3'"):
            self.getComputeLengthInMeter(3)

    def test_readToporobot_Text(self):
        topofiles = topoReader.readToporobot(extraFile('CaveMerged.Text'))
        self.assertNotEqual(topofiles['CaveMerged.Text'], None)
        self.assertEqual(len(topofiles['CaveMerged.Text'].series), 6)
        self.assertEqual(len(topofiles['CaveMerged.Text'].trips), 4)
        self.assertEqual(len(topofiles['CaveMerged.Text'].codes), 4)
        self.assertEqual(len(topofiles['CaveMerged.Text'].entries), 1)
        # check that stings are stripped
        self.assertEqual(topofiles['CaveMerged.Text'].name, "CaveMerged.Text")
        self.assertEqual(topofiles['CaveMerged.Text'].caveName, "CaveMerged")
        self.assertEqual(topofiles['CaveMerged.Text'].entries[1].name, "D10.10")
        self.assertEqual(topofiles['CaveMerged.Text'].trips[1].speleometer, "MCH")
        self.assertEqual(topofiles['CaveMerged.Text'].trips[1].speleograph, "AH")
        self.assertEqual(topofiles['CaveMerged.Text'].trips[1].date, "2007-08-25")
        self.assertEqual(topofiles['CaveMerged.Text'].series[2].name, "SUITE DU COURANT D'AIR")

    def test_readToporobot_TextMacClassic(self):
        self._test_readToporobot_Text("mac_roman", b'\x0D')
 
    def test_readToporobot_TextUnix(self):
        topofiles = self._test_readToporobot_Text("utf_8", b'\x0A')
        self.assertEqual(topofiles['non_latin_utf_8.Text'].caveName, "non_latin_utf") # without version at end
 
    def test_readToporobot_TextWindows(self):
        self._test_readToporobot_Text("windows-1252", b'\x0D\x0A')
 
    def _test_readToporobot_Text(self, encoding, eol):
        textWithNonLatinCharacters = "méandre du süsses glaçon dans la forêt"
        namesWithNonLatinCharacters = "François      Jürg         "
        filename = "non_latin_"+encoding+".Text"
        filepath = os.path.join(tmpfolderpath, filename)
        with open(filepath, 'wb') as file:
            file.write(b"    -2     1   1   1   1 25/08/07  " + namesWithNonLatinCharacters.encode(encoding=encoding) + b" 1    0.00   0   1" + eol)
            file.write(b"    -1     3   1   1   1  400.00  400.00    0.10    2.00    2.00  100.00    0.00" + eol)
            file.write(b"     1    -2   1   1   1 " + textWithNonLatinCharacters.encode(encoding=encoding) + eol)
            file.write(b"     1    -1   1   1   1       1       0       1       0       0       1       6" + eol)
            file.write(b"     1     0   3   1   1    0.00    0.00    0.00    0.30    0.60    0.80    0.90" + eol)
        topofiles = topoReader.readToporobot(filepath, encoding = encoding)
        self.assertEqual(topofiles[filename].trips[1].speleograph, "Jürg")
        self.assertEqual(topofiles[filename].trips[1].speleometer, "François")
        self.assertEqual(topofiles[filename].series[1].name, textWithNonLatinCharacters)
        self.assertEqual(topofiles[filename].series[1].stations[0].top, 0.80)
        return topofiles

    def test_readToporobot_TextAndCoord(self):
        topofiles = topoReader.readToporobot(extraFile('CaveMerged.Text'), 
                             coordFilePath = extraFile('CaveMerged.Coord'))
        self.assertEqual(topofiles['CaveMerged.Text'].series[1].stations[0].coordZ, 1777.71)
        self.assertEqual(topofiles['CaveMerged.Text'].series[6].stations[3].coordX, 628996.66)

    def test_readToporobot_TextAndMerge(self):
        topofiles = topoReader.readToporobot(extraFile('CaveMerged.Text'), 
                             mergeFilePath = extraFile('CaveMerged-MergeInfo.csv'))
        self.assertEqual(topofiles['D10H10_03.Text'].codes[3].nrMerged, 3)
        self.assertEqual(topofiles['D10H10_03.Text'].codes[3].nrOrig, 4)

    def test_readGroundAlti_Empty(self):
        topofile = topoData.TopoFile()
        topoReader.readGroundAlti(topofile, [])
        self.assertEqual(topofile.hasGroundAlti, True)

    def test_readGroundAlti_Raster(self):
        rasterLayer = QgsRasterLayer(extraFile('dummy_dem_2.tif'), 'dummy DEM')
        self.assertEqual(rasterLayer.isValid(), True)
        demLayerBand = topoReader.LayerBand(rasterLayer, 1, 'dem_band')
        topofiles = topoReader.readToporobot(extraFile('CaveMerged.Text'), 
                             coordFilePath = extraFile('CaveMerged.Coord'),
                             demLayerBands = [demLayerBand])
        self.assertEqual(topofiles['CaveMerged.Text'].hasGroundAlti, True)
        self.assertEqual(topofiles['CaveMerged.Text'].series[6].stations[3].hasGroundAlti, True)
        self.assertEqual(topofiles['CaveMerged.Text'].series[6].stations[3].groundAlti, 1829.0)

if __name__ == '__main__':
    unittest.main()
