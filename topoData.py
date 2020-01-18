# -*- coding: utf-8 -*-

from builtins import object
import math


class TopoFile (object):

  def __init__(self):
    self.name = None
    self.caveName = None
    self.path = None
    self.hasCoord = False
    self.unmerged = None # 0:unprocessed, 1: was unmerged, 2: new from unmerge
    self.hasGroundAlti = False
    self.entries = {} # do not modify, managed by TopoEntry
    self.trips = {} # do not modify, managed by TopoTrip
    self.codes = {} # do not modify, managed by TopoCode
    self.series = {} # do not modify, managed by TopoSerie


class TopoEntry (object):

  def __init__(self, nrMerged):
    self._nrMerged = nrMerged
    self.nrOrig = nrMerged
    self._topofile = None
    self.name = None
    self.coordX = None
    self.coordY = None
    self.coordZ = None
    self.station = None

  def setTopofile(self, value):
    if self._topofile and self._nrMerged in self._topofile.entries:
      del self._topofile.entries[self._nrMerged]
    self._topofile = value
    self._topofile.entries[self._nrMerged] = self

  nrMerged = property((lambda self: self._nrMerged))
  nr = property((lambda self: self.nrOrig))
  topofile = property((lambda self: self._topofile), setTopofile)


class TopoTrip (object):

  def __init__(self, nrMerged):
    self._nrMerged = nrMerged
    self.nrOrig = nrMerged
    self._topofile = None
    self.date = None
    self.speleometer = None
    self.speleograph = None

  def setTopofile(self, value):
    if self._topofile and self._nrMerged in self._topofile.trips:
      del self._topofile.trips[self._nrMerged]
    self._topofile = value
    self._topofile.trips[self._nrMerged] = self

  nrMerged = property((lambda self: self._nrMerged))
  nr = property((lambda self: self.nrOrig))
  topofile = property((lambda self: self._topofile), setTopofile)


class TopoCode (object):

  def __init__(self, nrMerged):
    self._nrMerged = nrMerged
    self.nrOrig = nrMerged
    self._topofile = None
    self.visible = None
    self.directionUnit = None
    self.slopeUnit = None
    self.computeLengthInMeter = None
    self.computeDirectionInRadian = None

  def setTopofile(self, value):
    if self._topofile and self._nrMerged in self._topofile.codes:
      del self._topofile.codes[self._nrMerged]
    self._topofile = value
    self._topofile.codes[self._nrMerged] = self

  nrMerged = property((lambda self: self._nrMerged))
  nr = property((lambda self: self.nrOrig))
  topofile = property((lambda self: self._topofile), setTopofile)


class TopoSerie (object):

  def __init__(self, nrMerged):
    self._nrMerged = nrMerged
    self.nrOrig = nrMerged
    self._topofile = None
    self.name = None
    self.stations = [] # do not modify, managed by TopoStation

  def setTopofile(self, value):
    if self._topofile and self._nrMerged in self._topofile.series:
      del self._topofile.series[self._nrMerged]
    self._topofile = value
    self._topofile.series[self._nrMerged] = self

  nrMerged = property((lambda self: self._nrMerged))
  nr = property((lambda self: self.nrOrig))
  topofile = property((lambda self: self._topofile), setTopofile)


class TopoStation (object):

  def __init__(self, serie):
    self._nr = len(serie.stations)
    self._serie = serie
    self.distance = None
    self.direction = None
    self.slope = None
    self.left = None
    self.right = None
    self.top = None
    self.bottom = None
    self.trip = None
    self.code = None
    self.hasCoord = False
    self.coordX = None
    self.coordY = None
    self.coordZ = None
    self.hasGroundAlti = False
    self.groundAlti = None

    serie.stations.append(self)

  nr = property((lambda self: self._nr))
  serie = property((lambda self: self._serie))
  directionInRadian = property((lambda self: self.code.computeDirectionInRadian(self.direction)))
  lengthInMeter = property((lambda self: self.code.computeLengthInMeter(self.length)))
  leftInMeter = property((lambda self: self.code.computeLengthInMeter(self.left)))
  rightInMeter = property((lambda self: self.code.computeLengthInMeter(self.right)))
  depth = property((lambda self: (self.coordZ - self.groundAlti) if self.groundAlti else None))
  topAlti = property((lambda self: self.coordZ + self.top))
  bottomAlti = property((lambda self: self.coordZ - self.bottom))
  topDepth = property((lambda self: (self.topAlti - self.groundAlti) if self.groundAlti else None))
  bottomDepth = property((lambda self: (self.bottomAlti - self.groundAlti) if self.groundAlti else None))

