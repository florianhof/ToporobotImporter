# -*- coding: utf-8 -*-

import sys, os
packageFolderPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.dirname(packageFolderPath)) # one above to see it as a package
from ToporobotImporter import topoData, topoReader

import unittest
import math

quarter = math.pi / 2.0 # == 100 grades

def extraFile(filename):
    return os.path.join(packageFolderPath, 'extras', filename)

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
        self.assertEqual(topofiles['CaveMerged.Text'].series[6].name, 'MéANDRE')

    def test_readToporobot_TextAndCoord(self):
        topoReader.readToporobot(extraFile('CaveMerged.Text'), 
                                 coordFilePath = extraFile('CaveMerged.Coord'))

    def test_readToporobot_TextAndMerge(self):
        topoReader.readToporobot(extraFile('CaveMerged.Text'), 
                                 mergeFilePath = extraFile('CaveMerged-MergeInfo.csv'))

    def test_readGroundAlti_Empty(self):
        topofile = topoData.TopoFile()
        topoReader.readGroundAlti(topofile, {})
        self.assertEqual(topofile.hasGroundAlti, True)

if __name__ == '__main__':
    unittest.main()
