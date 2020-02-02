# -*- coding: utf-8 -*-

import unittest
import topoDrawer
import math

quarter = math.pi / 2.0 # == 100 grad

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


if __name__ == '__main__':
    unittest.main()

