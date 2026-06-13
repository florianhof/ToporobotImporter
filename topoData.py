# -*- coding: utf-8 -*-

import math

class TopoFile:
    """Classe représentant un fichier TopoFile."""

    def __init__(self):
        self.name = None
        self.caveName = None
        self.path = None
        self.hasCoord = False
        # 0: non traité, 1: a été démergé, 2: nouveau depuis le démerge
        self.unmerged = None
        self.hasGroundAlti = False
        # Dictionnaires gérés par TopoEntry, TopoTrip et TopoCode
        self.entries = {}
        self.trips = {}
        self.codes = {}
        self.series = {}

class TopoEntry:
    """Classe représentant une entrée TopoEntry."""

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
        """Définit le TopoFile associé à cette entrée."""
        if self._topofile and self._nrMerged in self._topofile.entries:
            del self._topofile.entries[self._nrMerged]
        self._topofile = value
        self._topofile.entries[self._nrMerged] = self

    @property
    def nrMerged(self):
        """Retourne le numéro merged."""
        return self._nrMerged

    @property
    def nr(self):
        """Retourne le numéro original."""
        return self.nrOrig

    @property
    def topofile(self):
        """Retourne le TopoFile associé."""
        return self._topofile

    @topofile.setter
    def topofile(self, value):
        """Définit le TopoFile associé."""
        self.setTopofile(value)

class TopoTrip:
    """Classe représentant une expédition (Trip) TopoTrip."""
    
    def __init__(self, nrMerged):
        self._nrMerged = nrMerged
        self.nrOrig = nrMerged
        self._topofile = None
        self.date = None
        self.speleometer = None
        self.speleograph = None

    def setTopofile(self, value):
        """Définit le TopoFile associé à cette expédition."""
        if self._topofile and self._nrMerged in self._topofile.trips:
            del self._topofile.trips[self._nrMerged]
        self._topofile = value
        self._topofile.trips[self._nrMerged] = self

    @property
    def nrMerged(self):
        """Retourne le numéro merged."""
        return self._nrMerged

    @property
    def nr(self):
        """Retourne le numéro original."""
        return self.nrOrig

    @property
    def topofile(self):
        """Retourne le TopoFile associé."""
        return self._topofile

    @topofile.setter
    def topofile(self, value):
        """Définit le TopoFile associé."""
        self.setTopofile(value)

class TopoCode:
    """Classe représentant un code TopoCode."""

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
        """Définit le TopoFile associé à ce code."""
        if self._topofile and self._nrMerged in self._topofile.codes:
            del self._topofile.codes[self._nrMerged]
        self._topofile = value
        self._topofile.codes[self._nrMerged] = self

    @property
    def nrMerged(self):
        """Retourne le numéro merged."""
        return self._nrMerged

    @property
    def nr(self):
        """Retourne le numéro original."""
        return self.nrOrig

    @property
    def topofile(self):
        """Retourne le TopoFile associé."""
        return self._topofile

    @topofile.setter
    def topofile(self, value):
        """Définit le TopoFile associé."""
        self.setTopofile(value)

class TopoSerie:
    """Classe représentant une série TopoSerie."""

    def __init__(self, nrMerged):
        self._nrMerged = nrMerged
        self.nrOrig = nrMerged
        self._topofile = None
        self.name = None
        # Liste gérée par TopoStation
        self.stations = []

    def setTopofile(self, value):
        """Définit le TopoFile associé à cette série."""
        if self._topofile and self._nrMerged in self._topofile.series:
            del self._topofile.series[self._nrMerged]
        self._topofile = value
        self._topofile.series[self._nrMerged] = self

    @property
    def nrMerged(self):
        """Retourne le numéro merged."""
        return self._nrMerged

    @property
    def nr(self):
        """Retourne le numéro original."""
        return self.nrOrig

    @property
    def topofile(self):
        """Retourne le TopoFile associé."""
        return self._topofile

    @topofile.setter
    def topofile(self, value):
        """Définit le TopoFile associé."""
        self.setTopofile(value)


class TopoStation:
    """Classe représentant une station TopoStation."""

    def __init__(self, serie):
        """ Initialise une nouvelle station.
        Args: serie (TopoSerie): La série à laquelle cette station appartient. """
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

    @property
    def nr(self):
        """Retourne le numéro de la station."""
        return self._nr

    @property
    def serie(self):
        """Retourne la série à laquelle cette station appartient."""
        return self._serie

    @property
    def directionInRadian(self):
        """Retourne la direction en radians."""
        #??? : Vérifie si `self.code` et `self.direction` sont toujours définis avant d'accéder à `computeDirectionInRadian`.
        # Compatibilité : Si `self.code` ou `self.direction` peut être `None`, ajoute une vérification.
        if self.code and self.direction is not None:
            return self.code.computeDirectionInRadian(self.direction)
        return None

@property
    def lengthInMeter(self):
        """Retourne la longueur en mètres."""
        #??? : Vérifie si `self.code` et `self.distance` sont toujours définis avant d'accéder à `computeLengthInMeter`.
        # Compatibilité : Si `self.code` ou `self.distance` peut être `None`, ajoute une vérification.
        if self.code and self.distance is not None:
            return self.code.computeLengthInMeter(self.distance)
        return None

    @property
    def leftInMeter(self):
        """Retourne la valeur 'left' en mètres."""
        if self.code and self.left is not None:
            return self.code.computeLengthInMeter(self.left)
        return None

    @property
    def rightInMeter(self):
        """Retourne la valeur 'right' en mètres."""
        if self.code and self.right is not None:
            return self.code.computeLengthInMeter(self.right)
        return None

    @property
    def depth(self):
        """Retourne la profondeur (coordZ - groundAlti)."""
        if self.groundAlti is not None and self.coordZ is not None:
            return self.coordZ - self.groundAlti
        return None

    @property
    def topAlti(self):
        """Retourne l'altitude du haut (coordZ + top)."""
        if self.coordZ is not None and self.top is not None:
            return self.coordZ + self.top
        return None

    @property
    def bottomAlti(self):
        """Retourne l'altitude du bas (coordZ - bottom)."""
        if self.coordZ is not None and self.bottom is not None:
            return self.coordZ - self.bottom
        return None

    @property
    def topDepth(self):
        """Retourne la profondeur du haut (topAlti - groundAlti)."""
        if self.topAlti is not None and self.groundAlti is not None:
            return self.topAlti - self.groundAlti
        return None

    @property
    def bottomDepth(self):
        """Retourne la profondeur du bas (bottomAlti - groundAlti)."""
        if self.bottomAlti is not None and self.groundAlti is not None:
            return self.bottomAlti - self.groundAlti
        return None

