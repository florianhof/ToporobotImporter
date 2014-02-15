# -*- coding: utf-8 -*-

import fileinput
import os
import datetime
#from qgis.core import QgsPoint, QgsRaster # only for importGroundAlti
from topoData import *;

def readToporobot(toporobotFilePath, 
                    coordFilePath = None, 
                    mergeFilePath = None, 
                    demLayerBands = None):

    topofile = readToporobotText(toporobotFilePath)
    if coordFilePath:
      readToporobotCoord(coordFilePath, topofile)
    if groundLayer:
      readGroundAlti(topofile, demLayerBands)
    if mergeFilePath:
      topofiles = readMergeMapping(mergeFilePath, topofile)
    else:
      topofiles = {topofile.name: topofile}
    return topofiles

def readToporobotText(filepath):
    
    topofile = TopoFile()
    topofile.path = filepath
    topofile.name = os.path.basename(filepath)
    
    #with open(filepath, 'rU') as file:
    file = open(filepath, 'rU')
    try:
      for line in file:
        line = unicode(line, 'mac_roman') # Toporobot comes from Mac
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
          trip.speleometer = line[35:47]
          trip.speleograph = line[49:61]
        elif serieNb == -1: # code
          code = TopoCode(stationNb)
          code.topofile = topofile
          code.visible = (float(line[73:80]) != -100.00)
          code.directionUnit = float(line[25:32])
          code.slopeUnit = float(line[33:40])
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
        
    finally:
      file.close()
    return topofile


def readToporobotCoord(filepath, topofile):

    #with open(filepath, 'rU') as file:
    file = open(filepath, 'rU')
    try:
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
    finally:
      file.close()
    return topofile


def readMergeMapping(filepathMerged, topofileMerged):

    topofiles = {}
    #with open(filepathMerged, 'rU') as file:
    file = open(filepathMerged, 'rU')
    try:
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
    finally:
      file.close()
    return topofiles


def readGroundAlti(topofile, demLayerBands):

    # code inspired from "Point Sampling Tool" by Borys Jurgiel
    from qgis.core import QgsPoint, QgsRaster
    for serie in topofile.series.values():
      for station in serie.stations:
        if not station.hasCoord: continue
        for demLayerBand in demLayerBands:
          value = demLayerBand.getValueAt(QgsPoint(station.coordX, station.coordY))
          try:
            station.groundAlti = float(value)
            station.hasGroundAlti = True
            continue # use the first value found
          except (ValueError, TypeError):
            pass # point is out of raster extent or with an undefined value
    topofile.hasGroundAlti = True


class LayerBand:
    def __init__(self, layer, bandnr, bandname):
      self.layer = layer
      self.bandnr = bandnr
      self.bandname = bandname
    def getValueAt(self, point):
      from qgis.core import QgsRaster
      values = self.layer.dataProvider().identify(
                 point,
                 QgsRaster.IdentifyFormatValue)
      value = values.results()[self.bandnr]
      return value # type is layer-specific


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

