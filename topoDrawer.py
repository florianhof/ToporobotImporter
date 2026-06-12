# -*- coding: utf-8 -*-

import math
import re
from qgis.core import QgsFeature, QgsGeometry, QgsPointXY
from PyQt5.QtCore import QVariant
from .topoData import *  # Assure-toi que ce module est compatible avec Python 3 et QGIS 3.x


# --- Drawers ---

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
        return QgsWkbTypes.Point  # QGis.WKBPoint est déprécié en QGIS 3.x

    def fields(self):
        return fieldsForStations

    def draw(self, topofiles, writer):
        for topofile in topofiles.values():
            for serie in topofile.series.values():
                for station in serie.stations:
                    if station.code and station.code.visible:  # Vérification supplémentaire pour éviter les erreurs
                        outFeat = QgsFeature()
                        outFeat.setGeometry(QgsGeometry.fromPointXY(toQgsPoint(station)))
                        addStationFields(outFeat, station)
                        if not writer.addFeature(outFeat):
                            #??? : Vérifie si une gestion d'erreur est nécessaire ici.
                            # Compatibilité : En QGIS 3.x, `addFeature` retourne un booléen indiquant le succès.
                            raise IOError("Impossible d'ajouter l'entité pour la station.")


class AimsDrawer(TopoDrawer):

    def wkbType(self):
        return QgsWkbTypes.LineString  # QGis.WKBLineString est déprécié en QGIS 3.x

    def fields(self):
        return fieldsForStations


def draw(self, topofiles, writer):
    """Dessine les segments entre les stations consécutives."""
    for topofile in topofiles.values():
        for serie in topofile.series.values():
            # Commence à partir de la deuxième station pour dessiner les segments
            for i in range(1, len(serie.stations)):
                station = serie.stations[i]
                if station.code and station.code.visible:  # Vérification supplémentaire
                    prevStation = serie.stations[i - 1]
                    outFeat = QgsFeature()
                    # Création d'une ligne entre la station précédente et la station actuelle
                    outFeat.setGeometry(
                        QgsGeometry.fromPolylineXY([
                            toQgsPoint(prevStation),
                            toQgsPoint(station)
                        ])
                    )
                    addStationFields(outFeat, station)
                    if not writer.addFeature(outFeat):
                        raise IOError("Impossible d'ajouter l'entité pour le segment entre stations.")


class AimsSurfaceDrawer(TopoDrawer):
    """Dessinateur pour les surfaces (polygones) basées sur les stations."""

    def wkbType(self):
        return QgsWkbTypes.Polygon  # QGis.WKBPolygon est déprécié en QGIS 3.x

    def fields(self):
        return fieldsForStations

    def draw(self, topofiles, writer):
        """Dessine les surfaces entre les stations consécutives."""
        for topofile in topofiles.values():
            for serie in topofile.series.values():
                for i in range(1, len(serie.stations)):
                    station = serie.stations[i]
                    if station.code and station.code.visible:  # Vérification supplémentaire
                        prevStation = serie.stations[i - 1]
                        (leftPrevPt, rightPrevPt) = getLeftRightPoints(prevStation)
                        (leftCurrPt, rightCurrPt) = getLeftRightPoints(station)
                        polyline = [leftPrevPt, rightPrevPt, rightCurrPt, leftCurrPt, leftPrevPt]
                        outFeat = QgsFeature()
                        # Création d'un polygone à partir de la polyligne
                        outFeat.setGeometry(QgsGeometry.fromPolygonXY([polyline]))
                        addStationFields(outFeat, station)
                        if not writer.addFeature(outFeat):
                            raise IOError("Impossible d'ajouter l'entité pour la surface entre stations.")


class SeriesDrawer(TopoDrawer):
    """Dessinateur pour les séries (trajectoires multi-lignes)."""

    def wkbType(self):
        return QgsWkbTypes.MultiLineString  # QGis.WKBMultiLineString est déprécié en QGIS 3.x

    def fields(self):
        return fieldsForSeries

    def draw(self, topofiles, writer):
        """Dessine les séries sous forme de multi-polygones."""
        for topofile in topofiles.values():
            for serie in topofile.series.values():
                multiPolygon = []
                polygon = []
                prevProcessedStationNr = -1
                for station in serie.stations[1:]:
                    if station.code and station.code.visible:  # Vérification supplémentaire
                        prevStation = serie.stations[station.nr - 1]
                        if not prevStation.nr == prevProcessedStationNr:
                            if len(polygon) > 0:
                                polygon.append(polygon)  # Ferme le polygone
                                multiPolygon.append(polygon)
                                polygon = []
                            (leftPrevPt, rightPrevPt) = getLeftRightPoints(prevStation)
                            polygon = [leftPrevPt, rightPrevPt]
                        (leftCurrPt, rightCurrPt) = getLeftRightPoints(station)
                        polygon.insert(0, leftCurrPt)
                        polygon.append(rightCurrPt)
                        prevProcessedStationNr = station.nr
                if len(polygon) > 0:
                    polygon.append(polygon)  # Ferme le polygone
                    multiPolygon.append(polygon)
                if len(multiPolygon) > 0:
                    outFeat = QgsFeature()
                    # Utilisation de fromMultiPolygonXY pour QGIS 3.x
                    outFeat.setGeometry(QgsGeometry.fromMultiPolygonXY([multiPolygon]))
                    addSerieFields(outFeat, serie)
                    if not writer.addFeature(outFeat):
                        raise IOError("Impossible d'ajouter l'entité pour la surface de la série.")


class SeriesSurfaceDrawer(TopoDrawer):
    """Dessinateur pour les surfaces des séries (multi-polygones)."""

    def wkbType(self):
        return QgsWkbTypes.MultiPolygon  # QGis.WKBMultiPolygon est déprécié en QGIS 3.x

    def fields(self):
        return fieldsForSeries

    def draw(self, topofiles, writer):
        """Dessine les séries sous forme de multi-polygones."""
        for topofile in topofiles.values():
            for serie in topofile.series.values():
                multiPolygon = []
                polygon = []
                prevProcessedStationNr = -1
                for station in serie.stations[1:]:
                    if station.code and station.code.visible:  # Vérification supplémentaire
                        prevStation = serie.stations[station.nr - 1]
                        if not prevStation.nr == prevProcessedStationNr:
                            if len(polygon) > 0:
                                polygon.append(polygon)  # Ferme le polygone
                                multiPolygon.append(polygon)
                                polygon = []
                            (leftPrevPt, rightPrevPt) = getLeftRightPoints(prevStation)
                            polygon = [leftPrevPt, rightPrevPt]
                        (leftCurrPt, rightCurrPt) = getLeftRightPoints(station)
                        polygon.insert(0, leftCurrPt)
                        polygon.append(rightCurrPt)
                        prevProcessedStationNr = station.nr
                if len(polygon) > 0:
                    polygon.append(polygon)  # Ferme le polygone
                    multiPolygon.append(polygon)
                if len(multiPolygon) > 0:
                    outFeat = QgsFeature()
                    # Utilisation de fromMultiPolygonXY pour QGIS 3.x
                    outFeat.setGeometry(QgsGeometry.fromMultiPolygonXY([multiPolygon]))
                    addSerieFields(outFeat, serie)
                    if not writer.addFeature(outFeat):
                        raise IOError("Impossible d'ajouter l'entité pour la surface de la série.")


# helpers

from qgis.core import QgsPointXY  # Utilisation de QgsPointXY au lieu de QgsPoint

def toQgsPoint(point):
    """Convertit un objet TopoStation, QVector2D ou QVector3D en QgsPointXY.
    Args:
        point: Un objet de type TopoStation, QVector2D ou QVector3D.

    Returns:
        QgsPointXY: Le point converti.

    Raises:
        TypeError: Si le type de l'objet n'est pas supporté.   """
    if isinstance(point, TopoStation):
        #??? : Vérifie si `point.coordX` et `point.coordY` sont toujours définis.
        # Compatibilité : Utilisation de QgsPointXY pour QGIS 3.x.
        return QgsPointXY(point.coordX, point.coordY)
    elif isinstance(point, QVector2D):
        return QgsPointXY(point.x(), point.y())
    elif isinstance(point, QVector3D):
        return QgsPointXY(point.x(), point.y())
    else:
        raise TypeError(f"Cannot convert from type {type(point)} to QgsPointXY")

def getLeftRightPoints(station):
    """Calcule les points gauche et droite d'une station en fonction de sa direction.
    Args:
        station (TopoStation): La station pour laquelle calculer les points.

    Returns:
        tuple: (leftPt, rightPt) ou None si la direction moyenne est indéfinie.    """
    prevDir = None
    if station.nr > 0:
        prevDir = station.directionInRadian
    nextDir = None
    if station.nr < len(station.serie.stations) - 1:
        nextDir = station.serie.stations[station.nr + 1].directionInRadian
    meanDir = getMeanDir(prevDir, nextDir)
    if meanDir is None:
        return None
    leftDir = meanDir - (math.pi / 2.0)
    if leftDir < 0.0:
        leftDir += (2.0 * math.pi)
    leftVect = (math.sin(leftDir), math.cos(leftDir))
    #??? : Vérifie si `station.leftInMeter` et `station.rightInMeter` sont toujours définis.
    # Compatibilité : Utilisation de QgsPointXY pour QGIS 3.x.
    leftPt = QgsPointXY(
        station.coordX + (leftVect * station.leftInMeter),
        station.coordY + (leftVect * station.leftInMeter)
    )
    rightPt = QgsPointXY(
        station.coordX - (leftVect * station.rightInMeter),
        station.coordY - (leftVect * station.rightInMeter)
    )
    return (leftPt, rightPt)

def getMeanDir(prevDir, nextDir):
    """Calcule la direction moyenne entre deux directions.
    Args:
        prevDir (float): La direction précédente en radians.
        nextDir (float): La direction suivante en radians.
    Returns:
        float: La direction moyenne en radians, ou None si les deux directions sont None.   """
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

from qgis.core import QgsFields, QgsField, QgsFeature, QVariant

# Fields and their content

fieldsForSeries = QgsFields()
fieldsForSeries.append(QgsField('FILE_NAME', QVariant.String, 'varchar', 254, 0, "name of the Toporobot file"))
fieldsForSeries.append(QgsField('CAVE_NAME', QVariant.String, 'varchar', 254, 0, "name of the cave (from the filename)"))
fieldsForSeries.append(QgsField('SERIE_NR', QVariant.Int, 'int', 6, 0, "number of the serie"))
fieldsForSeries.append(QgsField('SERIE_NAME', QVariant.String, 'varchar', 80, 0, "name of the serie"))

# Definition of fields for stations
fieldsForStations = QgsFields()
fieldsForStations.extend(fieldsForSeries)  # Ajoute les champs des séries
fieldsForStations.append(QgsField('STN_NR', QVariant.Int, 'int', 6, 0, "number of the station"))
fieldsForStations.append(QgsField('STN_X', QVariant.Double, 'double', 10, 2, "station's X coordinate"))
fieldsForStations.append(QgsField('STN_Y', QVariant.Double, 'double', 10, 2, "station's Y coordinate"))
fieldsForStations.append(QgsField('STN_Z', QVariant.Double, 'double', 7, 2, "station's Z coordinate"))
fieldsForStations.append(QgsField('STN_TOP', QVariant.Double, 'double', 7, 2, "altitude of the galery's roof above the station"))
fieldsForStations.append(QgsField('STN_BOTTOM', QVariant.Double, 'double', 7, 2, "altitude of the galery's ground under the station"))
fieldsForStations.append(QgsField('STN_GROUND', QVariant.Double, 'double', 7, 2, "altitude of the surface's ground above the station"))
fieldsForStations.append(QgsField('STN_DEPTH', QVariant.Double, 'double', 8, 2, "depth of the cave's station compared to the ground"))
fieldsForStations.append(QgsField('STN_DEP_TO', QVariant.Double, 'double', 8, 2, "depth of the cave's ceiling compared to the ground"))
fieldsForStations.append(QgsField('STN_DEP_BO', QVariant.Double, 'double', 8, 2, "depth of the cave's floor compared to the ground"))
fieldsForStations.append(QgsField('TRIP_DATE', QVariant.String, 'varchar', 8, 0, "trip's date"))
fieldsForStations.append(QgsField('TRIP_SPMET', QVariant.String, 'varchar', 12, 0, "trip's speleometer"))
fieldsForStations.append(QgsField('TRIP_SPGRA', QVariant.String, 'varchar', 12, 0, "trip's speleograph"))

def addSerieFields(feature, serie):
    """Ajoute les attributs de la série à une entité (feature).
    Args:
        feature (QgsFeature): L'entité à laquelle ajouter les attributs.
        serie (TopoSerie): La série contenant les données.   """
    feature.setAttributes(getSerieFields(serie))

def getSerieFields(serie):
    """Retourne les attributs de la série sous forme de liste.
    Args:
        serie (TopoSerie): La série contenant les données.
    Returns:
        list: Les attributs de la série.    """
    return [
        serie.topofile.name,
        serie.topofile.caveName,
        serie.nr,
        serie.name,
    ]

def addStationFields(feature, station):
    """Ajoute les attributs de la station à une entité (feature).
    Args:
        feature (QgsFeature): L'entité à laquelle ajouter les attributs.
        station (TopoStation): La station contenant les données.    """
    feature.setAttributes(getStationFields(station))

def getStationFields(station):
    """Retourne les attributs de la station sous forme de liste.
    Args:
        station (TopoStation): La station contenant les données.
    Returns:
        list: Les attributs de la station, incluant ceux de la série.    """
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
        station.trip.date if station.trip else None,
        station.trip.speleometer if station.trip else None,
        station.trip.speleograph if station.trip else None,
    ])
    return fields

