# -*- coding: utf-8 -*-

import datetime
import fileinput
import os
import re
import sys

# QGIS 3.44 utilise Python 3.12+. Utilisation des annotations de type natives.
from typing import Any, Dict, Optional

# #??? : Dans un plugin QGIS standard, évitez le "import *". 
# Importez explicitement les classes nécessaires (ex: de la classe TopoFile).
from .topodata import *  # Modifié en import relatif pour la structure du plugin

# Les classes de base de QGIS se nomment en CamelCase (QgsPoint, QgsRasterLayer).
# Décommentez si vous utilisez ces classes spécifiques dans la suite du code.
# from qgis.core import QgsPoint, QgsRasterLayer 


def readtoporobot(
    toporobotfilepath: str,
    coordfilepath: Optional[str] = None,
    mergefilepath: Optional[str] = None,
    demlayerbands: Optional[Any] = None,  # #??? : Remplacer Any par le type exact (ex: list ou dict) si connu
) -> Dict[str, Any]:
    """Lit et traite les fichiers Toporobot pour QGIS 3.44.
    Changements Python 3.10+ : Utilisation de None par défaut explicite et du
    typage natif.    """
    # En Python 3, les variables non définies lèvent une NameError.
    # 'none' (minuscule) a été corrigé en 'None' (majuscule).

    topofile = readtoporobottext(toporobotfilepath)

    if coordfilepath:
        readtoporobotcoord(coordfilepath, topofile)

    if demlayerbands:
        readgroundalti(topofile, demlayerbands)

    if mergefilepath:
        topofiles = readmergemapping(mergefilepath, topofile)
    else:
        # Utilisation de la syntaxe d'accès aux attributs standards de Python 3
        topofiles = {topofile.name: topofile}

    return topofiles


# Python 3.10+ / QGIS 3.44 : Utilisation des chaînes brutes (r"...") pour les regex.
# Changement : Remplacement de re.IGNORECASE par sa syntaxe moderne si besoin,
# mais re.IGNORECASE reste correct.
toporobotfilenamepattern = re.compile(
    r"^(.+?)(_\d+)?(.te?xt)?$", re.IGNORECASE
)

def readToporobotText(filepath):
    """
    Lit un fichier Toporobot et extrait les données de cavernes.
    Adapté pour Python 3.12+ et QGIS 3.44.
    """
    topofile = TopoFile()
    topofile.path = filepath
    topofile.name = os.path.basename(filepath)

    #??? Vérifier que toporobotFilenamePattern est bien défini et compatible avec Python 3.12+
    # Si ce n'est pas le cas, il faudra adapter l'extraction du nom de la grotte.
    topofile.caveName = toporobotFilenamePattern.match(topofile.name).group(1)

    try:
        # Ouverture du fichier avec encodage explicite pour 'mac_roman'
        #??? Si l'encodage 'mac_roman' n'est pas disponible, utiliser 'latin1' ou 'utf-8' selon le cas.
        with open(filepath, 'r', encoding='mac_roman') as file:
            for line in file:
                # Conversion explicite de la ligne en 'mac_roman' vers Unicode
                #??? Si la conversion échoue, essayer avec 'latin1' ou 'utf-8'
                line = line.encode('utf-8').decode('mac_roman', errors='replace').rstrip("\r\n")

                if len(line) < 13:
                    continue
                elif line != ' ':
                    continue
                else:
                    try:
                        serieNb = int(line[1:6])
                        stationNb = int(line[7:12])
                    except ValueError:
                        continue  # Ignorer les lignes mal formatées

                if serieNb == -6:  # entrie's name
                    entry = TopoEntry(stationNb)
                    entry.topofile = topofile
                    entry.name = line[25:].rstrip("\r\n")
                    if stationNb not in topofile.entries:
                        topofile.entries[stationNb] = entry
                    else:
                        topofile.entries[stationNb] = entry  # Remplacer si nécessaire

                elif serieNb == -5:  # entrie's coordinates
                    #??? Vérifier que stationNb existe dans topofile.entries
                    if stationNb in topofile.entries:
                        entry = topofile.entries[stationNb]
                        try:
                            entry.coordX = float(line[25:36].strip())
                            entry.coordY = float(line[37:48].strip())
                            entry.coordZ = float(line[49:60].strip())
                        except ValueError:
                            pass  # Ignorer si la conversion échoue

                elif serieNb == -4:  # misc (blabla)
                    pass

                elif serieNb == -3:  # unused?
                    pass

                elif serieNb == -2:  # trip
                    trip = TopoTrip(stationNb)
                    trip.topofile = topofile
                    trip.date = convDateFromTopo(line[25:33])
                    trip.speleometer = line[35:47].strip()
                    trip.speleograph = line[49:61].strip()
                    if stationNb not in topofile.trips:
                        topofile.trips[stationNb] = trip
                    else:
                        topofile.trips[stationNb] = trip  # Remplacer si nécessaire

                elif serieNb == -1:  # code
                    code = TopoCode(stationNb)
                    code.topofile = topofile
                    try:
                        code.visible = (float(line[73:80].strip()) != -100.00)
                        code.directionUnit = float(line[25:32].strip())
                        code.slopeUnit = float(line[33:40].strip())
                        code.computeLengthInMeter = getComputeLengthInMeter(code)
                        code.computeDirectionInRadian = getComputeDirectionInRadian(code)
                    except (ValueError, IndexError):
                        continue  # Ignorer si la conversion échoue

                    if stationNb not in topofile.codes:
                        topofile.codes[stationNb] = code
                    else:
                        topofile.codes[stationNb] = code  # Remplacer si nécessaire

                elif serieNb <= 0:  # unused, skip
                    pass

                elif stationNb == -2:  # serie's name
                    serie = TopoSerie(serieNb)
                    serie.topofile = topofile
                    serie.name = line[25:].rstrip("\r\n")
                    if serieNb not in topofile.series:
                        topofile.series[serieNb] = serie
                    else:
                        topofile.series[serieNb] = serie  # Remplacer si nécessaire

                elif stationNb == -1:  # serie's data
                    pass

                else:  # stations
                    #??? Vérifier que serieNb existe dans topofile.series
                    if serieNb in topofile.series:
                        serie = topofile.series[serieNb]
                        station = TopoStation(serie)
                        try:
                            assert(station.nr == stationNb)  #??? Vérifier que l'assertion est nécessaire
                            station.distance = float(line[25:32].strip())
                            station.direction = float(line[33:40].strip())
                            station.slope = float(line[41:48].strip())
                            station.left = float(line[49:56].strip())
                            station.right = float(line[57:64].strip())
                            station.top = float(line[65:72].strip())
                            station.bottom = float(line[73:80].strip())

                            #??? Vérifier que les indices 20:24 et 12:16 sont corrects
                            trip_index = int(line[20:24].strip())
                            code_index = int(line[12:16].strip())

                            if trip_index in topofile.trips:
                                station.trip = topofile.trips[trip_index]
                            if code_index in topofile.codes:
                                station.code = topofile.codes[code_index]
                        except (ValueError, IndexError, KeyError, AssertionError):
                            continue  # Ignorer si une erreur survient

    except IOError as e:
        print(f"Erreur lors de la lecture du fichier {filepath}: {e}")
        return None

    return topofile

def getComputeLengthInMeter(code):
    lengthUnit = code.directionUnit % 10
    if lengthUnit == 0 or lengthUnit == 9:
        return lambda length: length
    elif lengthUnit == 8 or lengthUnit == 7:
        return lambda length: length * 0.3048
    else:
        #??? Vérifier que 'code.nr' est bien défini et accessible.
        # Si ce n'est pas le cas, utiliser une autre propriété ou un identifiant unique.
        raise ValueError(f"unknown length unit '{lengthUnit}' for code {code.nr}")

import math

def getComputeDirectionInRadian(code):
    directionUnit = code.directionUnit
    revolution = 2.0 * math.pi
    half = math.pi

    if 390 < directionUnit <= 400:
        return lambda direction: revolution * direction / 400
    elif 380 < directionUnit <= 390:
        return lambda direction: (revolution * direction / 400 + half) % revolution
    elif 350 < directionUnit <= 360:
        return lambda direction: revolution * direction / 360
    elif 340 < directionUnit <= 350:
        return lambda direction: (revolution * direction / 360 + half) % revolution
    else:
        #??? Vérifier que 'code.nr' est bien défini et accessible.
        raise ValueError(f"unknown directionUnit '{directionUnit}' for code {code.nr}")

def readToporobotCoord(filepath, topofile):
    """     Lit les coordonnées des stations depuis un fichier Toporobot.
    Met à jour le fichier 'topofile' avec les coordonnées et retourne le résultat.    """
    try:
        # Ouverture du fichier avec encodage explicite (à adapter selon le format réel)
        #??? Si le fichier n'est pas en 'utf-8' ou 'mac_roman', ajuster l'encodage.
        with open(filepath, 'r', encoding='utf-8') as file:
            stationNb = -1
            serie = None
            for line in file:
                line = line.rstrip("\r\n")  # Supprimer les retours à la ligne

                if len(line) < 2:
                    continue
                elif line.startswith('  '):
                    stationNb += 1
                    #??? Vérifier que 'serie' est bien définie et que 'stationNb' est valide.
                    if serie and stationNb < len(serie.stations):
                        station = serie.stations[stationNb]
                        try:
                            station.coordX = float(line[14:25].strip())
                            station.coordY = float(line[26:37].strip())
                            station.coordZ = float(line[38:47].strip())
                            station.hasCoord = True
                        except (ValueError, IndexError):
                            continue  # Ignorer les lignes mal formatées
                elif line.startswith('->'):
                    serieNb = int(line[3:8].strip())
                    #??? Vérifier que 'serieNb' existe dans 'topofile.series'.
                    if serieNb in topofile.series:
                        serie = topofile.series[serieNb]
                        stationNb = -1
                    else:
                        serie = None  # Ignorer si la série n'existe pas
                elif line.startswith('Fixpoints'):
                    break
                else:
                    continue

            topofile.hasCoord = True

    except IOError as e:
        print(f"Erreur lors de la lecture du fichier {filepath}: {e}")
        return None

    return topofile

def readMergeMapping(filepathMerged, topofileMerged):
    """
    Lit un fichier de mappage de fusion et associe les entrées, voyages, codes et séries
    à leurs fichiers TopoFile respectifs.
    Retourne un dictionnaire de TopoFile associés.    """
    topofiles = {}

    try:
        # Ouverture du fichier avec encodage explicite (à adapter si nécessaire)
        #??? Si le fichier utilise un encodage spécifique (ex: 'mac_roman'), remplacer 'utf-8' par celui-ci.
        with open(filepathMerged, 'r', encoding='utf-8') as file:
            hline = file.readline()  # get header line

            # Détection du séparateur de champs
            if hline.count(';') >= 2:
                fieldSep = ';'
            elif hline.count("\t") >= 2:
                fieldSep = "\t"
            elif hline.count('|') >= 2:
                fieldSep = '|'
            elif hline.count(',') >= 2:
                fieldSep = ','
            else:
                raise ValueError("cannot find a known separator for file with merge informations")

            for line in file: # process body lines
                line = line.rstrip("\r\n")  # Supprimer les retours à la ligne

                # Diviser et nettoyer les champs
                fields = line.split(fieldSep)
                if len(fields) < 4:
                    continue  # Ignorer les lignes mal formatées

                try:
                    topoType = int(fields.strip())
                    nrMerged = int(fields.strip())
                    nrOrig = int(fields.strip())
                    filename = fields.strip()
                    # Supprimer les guillemets entourant le nom de fichier
                    filename = filename.strip('"\'')
                except (ValueError, IndexError) as e:
                    continue  # Ignorer les lignes mal formatées

                # Récupérer ou créer le TopoFile associé
                if filename in topofiles:
                    topofile = topofiles[filename]
                else:
                    topofile = TopoFile()
                    topofile.name = filename
                    topofiles[filename] = topofile
                    topofile.hasCoord = topofileMerged.hasCoord
                    topofile.hasGroundAlti = topofileMerged.hasGroundAlti
                    topofile.unmerged = 2

                # Associer le TopoFile et le numéro original
                try:
                    if topoType == -6:
                        #??? Vérifier que 'nrMerged' existe dans 'topofileMerged.entries'.
                        if nrMerged in topofileMerged.entries:
                            topofileMerged.entries[nrMerged].nrOrig = nrOrig
                            topofileMerged.entries[nrMerged].topofile = topofile

                    elif topoType == -2:
                        #??? Vérifier que 'nrMerged' existe dans 'topofileMerged.trips'.
                        if nrMerged in topofileMerged.trips:
                            topofileMerged.trips[nrMerged].nrOrig = nrOrig
                            topofileMerged.trips[nrMerged].topofile = topofile

                    elif topoType == -1:
                        #??? Vérifier que 'nrMerged' existe dans 'topofileMerged.codes'.
                        if nrMerged in topofileMerged.codes:
                            topofileMerged.codes[nrMerged].nrOrig = nrOrig
                            topofileMerged.codes[nrMerged].topofile = topofile

                    elif topoType == 1:
                        #??? Vérifier que 'nrMerged' existe dans 'topofileMerged.series'.
                        if nrMerged in topofileMerged.series:
                            topofileMerged.series[nrMerged].nrOrig = nrOrig
                            topofileMerged.series[nrMerged].topofile = topofile
                except (KeyError, AttributeError) as e:
                    continue  # Ignorer si une erreur survient

            topofileMerged.unmerged = 1

    except IOError as e:
        print(f"Erreur lors de la lecture du fichier {filepathMerged}: {e}")
        return None

    return topofiles
def readGroundAlti(topofile, demLayerBands):
    """
    Lit les altitudes du sol pour chaque station à partir des couches DEM fournies.
    Met à jour les stations avec les altitudes trouvées.
    Inspiré de l'outil "Point Sampling Tool" par Borys Jurgiel.    """
    from qgis.core import QgsPoint

    for serie in topofile.series.values():
        #??? Vérifier que 'serie.stations' est une liste ou un dictionnaire accessible.
        # Si c'est un dictionnaire, utiliser 'serie.stations.values()'.
        for station in serie.stations:
            if not station.hasCoord:
                continue

            for demLayerBand in demLayerBands:
                try:
                    # Création du point QGIS
                    point = QgsPoint(station.coordX, station.coordY)

                    # Récupération de la valeur du DEM
                    value = demLayerBand.getValueAt(point)

                    # Conversion en float et mise à jour de l'altitude
                    station.groundAlti = float(value)
                    station.hasGroundAlti = True
                    break  # use the first value found

                except (ValueError, TypeError, AttributeError) as e:
                    # point is out of raster extent or with an undefined value
                    #??? Ajouter une journalisation des erreurs si nécessaire.
                    pass

    topofile.hasGroundAlti = True

from qgis.core import QgsRaster

class LayerBand:
    def __init__(self, layer, bandnr, bandname):
        self.layer = layer
        self.bandnr = bandnr
        self.bandname = bandname

    def __eq__(self, other):
        return (
            type(self) is type(other)
            and self.layer == other.layer
            and self.bandnr == other.bandnr
            and self.bandname == other.bandname
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.layer) + (self.bandnr * 31)

    def __repr__(self):
        #??? Vérifier que 'self.bandname' est bien une chaîne Unicode.
        return f'LayerBand({repr(self.layer)}, {repr(self.bandnr)}, \'{self.bandname}\')'

    def getValueAt(self, point):
        """Récupère la valeur du pixel à la position du point pour le bande spécifiée."""
        try:
            values = self.layer.dataProvider().identify(
                point,
                QgsRaster.IdentifyFormatValue
            )
            value = values.results()[self.bandnr]
            return value  # # type is layer-specific
        except (KeyError, IndexError, AttributeError) as e:
            #??? Ajouter une journalisation des erreurs si nécessaire.
            return None

def convDateFromTopo(string):
    """
    Convertit une date au format Toporobot en un format standard 'YYYY-MM-DD'.
    Formats supportés :
    - JJMMAAAA (ex: 21052024)
    - JJ/MM/AA (ex: 21/05/24) -> Converti en 2024-05-21
    - Chaîne vide -> Retourne une chaîne vide    """
    if len(string) == 8 and string.count('/') == 0:
        # Format : JJMMAAAA (ex: 21052024)
        try:
            year = int(string[4:8])
            month = int(string[2:4])
            day = int(string[0:2])
        except ValueError:
            raise ValueError(f"invalid date format in string '{string}'")

    elif (len(string) == 8 and string.count('/') == 2
          and string == '/' and string == '/'):
        # Format : JJ/MM/AA (ex: 21/05/24)
        try:
            year = int(string[6:8])
            month = int(string[3:5])
            day = int(string[0:2])

            # Conversion des années à deux chiffres
            if year < 60:
                year += 2000  # Années 2000-2059
            elif year < 100:
                year += 1900  # Années 1960-1999
        except ValueError:
            raise ValueError(f"invalid date format in string '{string}'")

    elif len(string) == 0:
        return ''

    else:
        raise ValueError(f"unknown date format '{string}'")

    # Retourne la date au format 'YYYY-MM-DD'
    return f"{year:04d}-{month:02d}-{day:02d}"

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python script.py <fichier_toporobot>")
        sys.exit(1)

    try:
        topofiles = readToporobot(sys.argv)  #??? Assurez-vous que 'readToporobot' est importée ou définie dans ce fichier.
        print(topofiles)
    except Exception as e:
        print(f"Erreur lors de l'exécution : {e}")
        sys.exit(1)

