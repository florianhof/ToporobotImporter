# -*- coding: utf-8 -*-

import math
import re
from PyQt4.QtCore import *
from qgis.core import *
from topoData import *;


# drawers

class TopoDrawer:


  def wkbType(self): 
    """Gives the geometry type."""
    raise NotImplementedError()

  def fields(self): 
    """Gives all the fields."""
    raise NotImplementedError()

  def draw(self, topofiles, writer):
    """Draws some Toporobot files. The writer only needs an addFeature(QgsFeature) method. """
    raise NotImplementedError()


class StationsDrawer(TopoDrawer):

  def wkbType(self): 
    return QGis.WKBPoint

  def fields(self): 
    return fieldsForStations

  def draw(self, topofiles, writer):
    for topofile in topofiles.values():
      for serie in topofile.series.values():
        for station in serie.stations:
          if station.code.visible:
            outFeat = QgsFeature()
            outFeat.setGeometry(QgsGeometry.fromPoint(toQgsPoint(station)))
            addStationFields(outFeat, station)
            writer.addFeature(outFeat)


class AimsDrawer(TopoDrawer):

  def wkbType(self): 
    return QGis.WKBLineString

  def fields(self): 
    return fieldsForStations

  def draw(self, topofiles, writer):
    for topofile in topofiles.values():
      for serie in topofile.series.values():
        for station in serie.stations[1:]:
          if station.code.visible:
            prevStation = serie.stations[station.nr-1]
            outFeat = QgsFeature()
            outFeat.setGeometry(QgsGeometry.fromPolyline([toQgsPoint(prevStation), toQgsPoint(station)]))
            addStationFields(outFeat, station)
            writer.addFeature(outFeat)


class AimsSurfaceDrawer(TopoDrawer):

  def wkbType(self): 
    return QGis.WKBPolygon

  def fields(self): 
    return fieldsForStations

  def draw(self, topofiles, writer):
    for topofile in topofiles.values():
      for serie in topofile.series.values():
        for station in serie.stations[1:]:
          if station.code.visible:
            prevStation = serie.stations[station.nr-1]
            (leftPrevPt, rightPrevPt) = getLeftRightPoints(prevStation)
            (leftCurrPt, rightCurrPt) = getLeftRightPoints(station)
            polyline = [leftPrevPt, rightPrevPt, rightCurrPt, leftCurrPt, leftPrevPt]
            outFeat = QgsFeature()
            outFeat.setGeometry(QgsGeometry.fromPolygon([polyline]))
            addStationFields(outFeat, station)
            writer.addFeature(outFeat)


class SeriesDrawer(TopoDrawer):

  def wkbType(self): 
    return QGis.WKBMultiLineString

  def fields(self): 
    return fieldsForSeries

  def draw(self, topofiles, writer):
    for topofile in topofiles.values():
      for serie in topofile.series.values():
        multiPolyLine = []
        polyLine = []
        prevProcessedStationNr = -1
        for station in serie.stations[1:]:
          if station.code.visible:
            prevStation = serie.stations[station.nr-1]
            if not prevStation.nr == prevProcessedStationNr:
              if len(polyLine) > 0:
                multiPolyLine.append(polyLine)
                polyLine = []
              polyLine.append(toQgsPoint(prevStation))
            polyLine.append(toQgsPoint(station))
            prevProcessedStationNr = station.nr
        if len(polyLine) > 0:
          multiPolyLine.append(polyLine)
        if len(multiPolyLine) > 0:
          outFeat = QgsFeature()
          outFeat.setGeometry(QgsGeometry.fromMultiPolyline(multiPolyLine))
          addSerieFields(outFeat, serie)
          writer.addFeature(outFeat)


class SeriesSurfaceDrawer(TopoDrawer):

  def wkbType(self):
    return QGis.WKBMultiPolygon

  def fields(self):
    return fieldsForSeries

  def draw(self, topofiles, writer):
    for topofile in topofiles.values():
      for serie in topofile.series.values():
        multiPolygon = []
        polygon = []
        prevProcessedStationNr = -1
        for station in serie.stations[1:]:
          if station.code.visible:
            prevStation = serie.stations[station.nr-1]
            if not prevStation.nr == prevProcessedStationNr:
              if len(polygon) > 0:
                polygon.append(polygon[0]) # close the polygon
                multiPolygon.append([polygon])
                polygon = []
              (leftPrevPt, rightPrevPt) = getLeftRightPoints(prevStation)
              polygon = [leftPrevPt, rightPrevPt]
            (leftCurrPt, rightCurrPt) = getLeftRightPoints(station)
            polygon.insert(0, leftCurrPt)
            polygon.append(rightCurrPt)
            prevProcessedStationNr = station.nr
        if len(polygon) > 0:
          multiPolygon.append([polygon]) # outer ring without any inner rings
        if len(multiPolygon) > 0:
          outFeat = QgsFeature()
          outFeat.setGeometry(QgsGeometry.fromMultiPolygon(multiPolygon))
          addSerieFields(outFeat, serie)
          writer.addFeature(outFeat)


# helpers

def toQgsPoint(point):
    if isinstance(point, TopoStation):
      return QgsPoint(point.coordX, point.coordY)
    elif isinstance(point, QVector2D):
      return QgsPoint(point.x(), point.y())
    elif isinstance(point, QVector3D):
      return QgsPoint(point.x(), point.y())
    else:
      raise TypeError("cannot convert from type "+str(type(point))+" to QgsPoint")

def getLeftRightPoints(station):
    prevDir = None
    if station.nr > 0:
      prevDir = station.directionInRadian
    nextDir = None
    if station.nr < len(station.serie.stations) - 1:
      nextDir = station.serie.stations[station.nr+1].directionInRadian
    meanDir = getMeanDir(prevDir, nextDir)
    if meanDir is None:
      return None
    leftDir = meanDir - (math.pi / 2.0)
    if leftDir < 0.0:
      leftDir += (2.0 * math.pi)
    leftVect = (math.sin(leftDir), math.cos(leftDir))
    leftPt = QgsPoint(station.coordX + (leftVect[0] * station.leftInMeter),
                      station.coordY + (leftVect[1] * station.leftInMeter))
    rightPt = QgsPoint(station.coordX - (leftVect[0] * station.rightInMeter),
                       station.coordY - (leftVect[1] * station.rightInMeter))
    return (leftPt, rightPt)

def getMeanDir(prevDir, nextDir):
    if prevDir is None:
      if nextDir is None:
        return None
      else:
        meanDir = nextDir
    else:
      if nextDir is None:
        meanDir = prevDir
      elif abs(nextDir - prevDir) <= math.pi:
        meanDir = (nextDir + prevDir) / 2.0
      else:
        meanDir = (nextDir + prevDir) / 2.0 + math.pi
        if meanDir >= (2.0 * math.pi):
          meanDir -= (2.0 * math.pi)
    return meanDir


# Fields and their content

fieldsForSeries = QgsFields()
fieldsForSeries.append(  QgsField('FILE_NAME' , QVariant.String, 'varchar', 254, 0, "name of the Toporobot file"))
fieldsForSeries.append(  QgsField('CAVE_NAME' , QVariant.String, 'varchar', 254, 0, "name of the cave (from the filename)"))
fieldsForSeries.append(  QgsField('SERIE_NR'  , QVariant.Int   , 'int'    ,   6, 0, "number of the serie"))
fieldsForSeries.append(  QgsField('SERIE_NAME', QVariant.String, 'varchar',  80, 0, "name of the serie"))

fieldsForStations = QgsFields()
fieldsForStations.extend(fieldsForSeries)
fieldsForStations.append(QgsField('STN_NR'    , QVariant.Int   , 'int'    ,   6, 0, "number of the station"))
fieldsForStations.append(QgsField('STN_X'     , QVariant.Double, 'double' ,  10, 2, "station's X coordinate"))
fieldsForStations.append(QgsField('STN_Y'     , QVariant.Double, 'double' ,  10, 2, "station's Y coordinate"))
fieldsForStations.append(QgsField('STN_Z'     , QVariant.Double, 'double' ,   7, 2, "station's Z coordinate"))
fieldsForStations.append(QgsField('STN_TOP'   , QVariant.Double, 'double' ,   7, 2, "altitude of the galery's roof above the station"))
fieldsForStations.append(QgsField('STN_BOTTOM', QVariant.Double, 'double' ,   7, 2, "altitude of the galery's ground under the station"))
fieldsForStations.append(QgsField('STN_GROUND', QVariant.Double, 'double' ,   7, 2, "altitude of the surface's ground above the station"))
fieldsForStations.append(QgsField('STN_DEPTH' , QVariant.Double, 'double' ,   8, 2, "depth of the cave's station compared to the ground"))
fieldsForStations.append(QgsField('STN_DEP_TO', QVariant.Double, 'double' ,   8, 2, "depth of the cave's ceiling compared to the ground"))
fieldsForStations.append(QgsField('STN_DEP_BO', QVariant.Double, 'double' ,   8, 2, "depth of the cave's floor compared to the ground"))
fieldsForStations.append(QgsField('TRIP_DATE' , QVariant.String, 'varchar',   8, 0, "trip's date"))
fieldsForStations.append(QgsField('TRIP_SPMET', QVariant.String, 'varchar',  12, 0, "trip's speleometer"))
fieldsForStations.append(QgsField('TRIP_SPGRA', QVariant.String, 'varchar',  12, 0, "trip's speleograph"))

def addSerieFields(feature, serie):
    feature.setAttributes(getSerieFields(serie))

def getSerieFields(serie):
    return [
      serie.topofile.name,
      serie.topofile.caveName,
      serie.nr,
      serie.name,
    ]

def addStationFields(feature, station):
    feature.setAttributes(getStationFields(station))

def getStationFields(station):
    fields = getSerieFields(station.serie)
    fields.extend([
      station.nr,
      station.coordX,
      station.coordY,
      station.coordZ,
      station.topAlti,
      station.bottomAlti,
      station.groundAlti,
      station.depth,
      station.topDepth,
      station.bottomDepth,
      station.trip.date,
      station.trip.speleometer,
      station.trip.speleograph,
    ])
    return fields


