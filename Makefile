#/***************************************************************************
# ToporobotImporter
# 
# Imports Cave galleries from Toporobot 
#                             -------------------
#        begin                : 2014-01-04
#        copyright            : (C) 2014 by Florian Hof
#        email                : florian@speleo.ch
# ***************************************************************************/
# 
#/***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# ***************************************************************************/

# CONFIGURATION
PLUGIN_UPLOAD = $(CURDIR)/plugin_upload.py

# Chemin pour QGIS 3.x (remplace .qgis2 par .local/share/QGIS/QGIS3)
QGISDIR = .local/share/QGIS/QGIS3

# Makefile pour un plugin PyQGIS moderne

# Traductions (désactivées par défaut, à activer si nécessaire)
SOURCES = __init__.py topoimpPlugin.py topoimpDialog.py topoimpProcess.py
TRANSLATIONS =  # i18n/toporobotimporter_en.ts

# Nom du plugin
PLUGINNAME = ToporobotImporter

# Fichiers Python
PY_FILES = __init__.py topoimpPlugin.py topoimpDialog.py topoimpProcess.py topoData.py topoReader.py topoDrawer.py

# Fichiers supplémentaires (icônes, métadonnées, etc.)
EXTRAS = images/icon.png images/toporobot.png metadata.txt
#IMAGES = images
# Fichiers UI et ressources
UI_FILES = ui_toporobotimporter.py
RESOURCE_FILES = resources_rc.py

# Répertoire d'aide
HELP = help

# Cible par défaut : compilation
default: compile

# Compilation des fichiers UI et ressources
compile: $(UI_FILES) $(RESOURCE_FILES)

# Génération du fichier .py à partir d'un fichier .qrc (pour les ressources)
%_rc.py : %.qrc
	pyrcc5 -o $*_rc.py $<  #??? Vérifier que pyrcc5 est installé (paquet python3-pyqt5)

# Génération du fichier .py à partir d'un fichier .ui (pour l'interface)
%.py : %.ui
	pyuic5 -o $@ $<  #??? Vérifier que pyuic5 est installé (paquet python3-pyqt5)

# Compilation des fichiers de traduction (.ts vers .qm)
%.qm : %.ts
	lrelease $<  #??? Vérifier que lrelease est installé (paquet qttools5-dev ou qtchooser)

# Déploiement du plugin (pour les systèmes Unix-like)
deploy: compile
	mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(UI_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(RESOURCE_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
#		mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/extras
#		mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/images
		mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/help
	cp -vfr $(EXTRAS) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/extras
	cp -vfr i18n $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vfr $(HELP)/* $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/help

# Nettoyage des fichiers compilés dans le répertoire de déploiement
dclean:
	find $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) -iname "*.pyc" -delete
	find $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) -iname ".svn" -prune -exec rm -Rf {} \;

# Suppression complète du plugin déployé
derase:
	rm -Rf $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

# Création d'une archive zip du plugin déployé (pour upload sur plugins.qgis.org)
zip: deploy dclean
	rm -f $(PLUGINNAME).zip
	cd $(HOME)/$(QGISDIR)/python/plugins && zip -9r "$(CURDIR)"/$(PLUGINNAME).zip $(PLUGINNAME)

# Création d'une archive zip du plugin depuis un commit git (si le dépôt est versionné)
package: compile
	rm -f $(PLUGINNAME).zip
	git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip $(VERSION)
	echo "Archive créée : $(PLUGINNAME).zip"

# Upload du plugin (nécessite le script plugin_upload.py)
upload: zip
	$(PLUGIN_UPLOAD) $(PLUGINNAME).zip

# Mise à jour des fichiers de traduction (.ts)
transup:
	pylupdate5 Makefile  #??? Vérifier que pylupdate5 est installé (paquet python3-pyqt5)

# Compilation des fichiers de traduction (.ts vers .qm)
transcompile: $(TRANSLATIONS:.ts=.qm)

# Nettoyage des fichiers de traduction compilés (.qm)
transclean:
	rm -f images/*.qm

# Nettoyage des fichiers générés (UI et ressources)
clean:
	rm -f $(UI_FILES) $(RESOURCE_FILES)

# Génération de la documentation (si Sphinx est installé)
doc:
	#cd help; make html

