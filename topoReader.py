# -*- coding: utf-8 -*-

from builtins import str
from builtins import object
import os
import re
import sys
import math
#from qgis.core import QgsPoint, QgsRaster # only for importGroundAlti
from .topoData import TopoFile, TopoEntry, TopoTrip, TopoCode, TopoSerie, TopoStation

def readToporobot(toporobotFilePath, 
                  coordFilePath = None, 
                  mergeFilePath = None, 
                  demLayerBands = None,
                  encoding = 'mac_roman'):

    topofile = readToporobotText(toporobotFilePath, encoding)
    if coordFilePath:
      readToporobotCoord(coordFilePath, topofile)
    if demLayerBands:
      readGroundAlti(topofile, demLayerBands)
    if mergeFilePath:
      topofiles = readMergeMapping(mergeFilePath, topofile)
    else:
      topofiles = {topofile.name: topofile}
    return topofiles

toporobotFilenamePattern = re.compile(r"^(.+?)(_\d+)?(.Te?xt)?$", re.IGNORECASE);

def readToporobotText(filepath, encoding):
    
    topofile = TopoFile()
    topofile.path = filepath
    topofile.name = os.path.basename(filepath)
    topofile.caveName = toporobotFilenamePattern.match(topofile.name).group(1)
    if not encoding or encoding == '':
        encoding =  'mac_roman' # Toporobot comes from Mac

    with open(filepath, 'r', encoding=encoding) as file: 
      for line in file:
        if len(line) < 13:
          continue
        elif line[0] != ' ':
          continue
        else:
          serieNb = int(line[1:6])
          stationNb = int(line[7:12])
        
        if   serieNb == -6: # entrie's name
          entry = TopoEntry(stationNb)
          entry.topofile = topofile
          entry.name = line[25:].rstrip("\r\n")
        elif serieNb == -5: # entrie's coordinates
          entry = topofile.entries[stationNb]
          entry.coordX = float(line[25:36])
          entry.coordY = float(line[37:48])
          entry.coordZ = float(line[49:60])
        elif serieNb == -4: # misc (blabla)
          pass
        elif serieNb == -3: # unused?
          pass
        elif serieNb == -2: # trip
          trip = TopoTrip(stationNb)
          trip.topofile = topofile
          trip.date = convDateFromTopo(line[25:33])
          trip.speleometer = line[35:47].strip()
          trip.speleograph = line[49:61].strip()
        elif serieNb == -1: # code
          code = TopoCode(stationNb)
          code.topofile = topofile
          code.visible = (float(line[73:80]) != -100.00)
          code.directionUnit = float(line[25:32])
          code.slopeUnit = float(line[33:40])
          code.computeLengthInMeter = getComputeLengthInMeter(code)
          code.computeDirectionInRadian = getComputeDirectionInRadian(code)
        elif serieNb <= 0:  # unused, skip
          pass
        elif stationNb == -2: # serie's name
          serie = TopoSerie(serieNb)
          serie.topofile = topofile
          serie.name = line[25:].rstrip("\r\n")
        elif stationNb == -1: # serie's data
          pass
        else:                 # stations
          serie = topofile.series[serieNb]
          station = TopoStation(serie)
          assert(station.nr == stationNb)
          station.distance = float(line[25:32])
          station.direction = float(line[33:40])
          station.slope = float(line[41:48])
          station.left = float(line[49:56])
          station.right = float(line[57:64])
          station.top = float(line[65:72])
          station.bottom = float(line[73:80])
          station.trip = topofile.trips[int(line[20:24])]
          station.code = topofile.codes[int(line[12:16])]
        
    return topofile

def getComputeLengthInMeter(code):
    lengthUnit = code.directionUnit % 10
    if   lengthUnit == 0 or lengthUnit == 9:
        return (lambda length: length)
    elif lengthUnit == 8 or lengthUnit == 7:
        return (lambda length: length * 0.3048)
    else:
        raise ValueError("unknown length unit '"+str(code.directionUnit)+"' for code "+str(code.nr))

revolution = 2.0 * math.pi
half = math.pi

def getComputeDirectionInRadian(code):
    directionUnit = code.directionUnit
    if   directionUnit > 390 and directionUnit <= 400:
        return (lambda direction: revolution * direction / 400)
    elif directionUnit > 380 and directionUnit <= 390:
        return (lambda direction: (revolution * direction / 400 + half) % revolution)
    elif directionUnit > 350 and directionUnit <= 360:
        return (lambda direction: revolution * direction / 360)
    elif directionUnit > 340 and directionUnit <= 350:
        return (lambda direction: (revolution * direction / 360 + half) % revolution)
    else:
        raise ValueError("unknown direction unit '"+str(code.directionUnit)+"' for code "+str(code.nr))


def readToporobotCoord(filepath, topofile):

    with open(filepath, 'r') as file:
      stationNb = -1
      serie = None
      for line in file:
        if len(line) < 2:
          continue
        elif line.startswith('  '):
          stationNb = stationNb + 1
          station = serie.stations[stationNb]
          station.coordX = float(line[14:25])
          station.coordY = float(line[26:37])
          station.coordZ = float(line[38:47])
          station.hasCoord = True
        elif line.startswith('->'):
          serieNb = int(line[3:8])
          serie = topofile.series[serieNb]
          stationNb = -1
        elif line.startswith('Fixpoints'):
          break
        else:
          continue
      topofile.hasCoord = True
    return topofile


def readMergeMapping(filepathMerged, topofileMerged):

    topofiles = {}
    with open(filepathMerged, 'r') as file:
      hline = file.readline() # get header line
      if   hline.count(';') >= 2: fieldSep = ';'
      elif hline.count("\t") >= 2: fieldSep = "\t"
      elif hline.count('|') >= 2: fieldSep = '|'
      elif hline.count(',') >= 2: fieldSep = ','
      else: raise ValueError("cannot find a known separator for file with merge informations")

      for line in file: # process body lines
        # split and clean fields
        topoType, nrMerged, nrOrig, filename = line.split(fieldSep)
        topoType = int(topoType)
        nrMerged = int(nrMerged)
        nrOrig = int(nrOrig)
        filename = filename.rstrip("\r\n")
        filename = filename.strip(' ')
        if (filename[0] == '"') and (filename[-1] == '"'):
          filename = filename[1:-1]
        elif (filename[0] == "'") and (filename[-1] == "'"):
          filename = filename[1:-1]
        # retrieve or create the associated topofile
        if filename in topofiles:
          topofile = topofiles[filename]
        else:
          topofile = TopoFile()
          topofile.name = filename
          topofiles[filename] = topofile
          topofile.hasCoord = topofileMerged.hasCoord
          topofile.hasGroundAlti = topofileMerged.hasGroundAlti
          topofile.unmerged = 2
        # change the associated topofile and original number
        if   topoType == -6:
          topofileMerged.entries[nrMerged].nrOrig = nrOrig
          topofileMerged.entries[nrMerged].topofile = topofile
        elif topoType == -2:
          topofileMerged.trips[nrMerged].nrOrig = nrOrig
          topofileMerged.trips[nrMerged].topofile = topofile
        elif topoType == -1:
          topofileMerged.codes[nrMerged].nrOrig = nrOrig
          topofileMerged.codes[nrMerged].topofile = topofile
        elif topoType == 1:
          topofileMerged.series[nrMerged].nrOrig = nrOrig
          topofileMerged.series[nrMerged].topofile = topofile
      topofileMerged.unmerged = 1
    return topofiles


def readGroundAlti(topofile, demLayerBands):

    # code inspired from "Point Sampling Tool" by Borys Jurgiel
    from qgis.core import QgsPointXY, QgsRaster
    for serie in list(topofile.series.values()):
      for station in serie.stations:
        if not station.hasCoord: continue
        for demLayerBand in demLayerBands:
          value, hasResult = demLayerBand.getValueAt(QgsPointXY(station.coordX, station.coordY))
          station.hasGroundAlti = hasResult
          station.groundAlti = float(value)
    topofile.hasGroundAlti = True


class LayerBand(object):
    def __init__(self, layer, bandnr, bandname):
      self.layer = layer
      self.bandnr = bandnr
      self.bandname = bandname
    def __eq__(self, other):
      return ((type(self) is type(other))
          and (self.layer == other.layer)
          and (self.bandnr == other.bandnr)
          and (self.bandname == other.bandname))
    def __ne__(self, other):
      return not self.__eq__(other)
    def __hash__(self):
      return hash(self.layer) + (self.bandnr * 31)
    def __repr__(self):
      return 'LayerBand(' + repr(self.layer) + ', ' + repr(self.bandnr) + ', \'' + self.bandname+ '\')'
    def getValueAt(self, point):
      """Return (value, hasResult) at the given point of this layer."""
      from qgis.core import QgsRaster
      value, hasResult = self.layer.dataProvider().sample(point, self.bandnr)
      return value, hasResult


def convDateFromTopo(string):
    if len(string) == 8 and string.count('/') == 0:
      year = int(string[4:8])
      month = int(string[2:4])
      day = int(string[0:2])
    elif (len(string) == 8 and string.count('/') == 2
           and string[2] == '/' and string[5] == '/'):
      year = int(string[6:8])
      month = int(string[3:5])
      day = int(string[0:2])
      if year < 60: year += 2000
      elif year < 100: year += 1900
    elif len(string) == 0:
      return ''
    else:
      raise ValueError("unknown date format '"+string+"'")
    return '%04d-%02d-%02d' % (year, month, day)


if __name__ == '__main__':
    topofiles = readToporobot(sys.argv[1])
    print(topofiles)

