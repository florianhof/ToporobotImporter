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

QGISDIR=Library/Application\ Support/QGIS/QGIS3/profiles/default

PYQGIS=/Applications/QGIS3.10.app/Contents/Frameworks/Python.framework/Versions/3.7/bin/python3.7

# Makefile for a PyQGIS plugin 

# translation
SOURCES = __init__.py topoimpPlugin.py topoimpDialog.py topoimpProcess.py
#TRANSLATIONS = i18n/toporobotimporter_en.ts
TRANSLATIONS = 

# global

PLUGINNAME = ToporobotImporter

PY_FILES = __init__.py topoimpPlugin.py topoimpDialog.py topoimpProcess.py topoData.py topoReader.py topoDrawer.py

EXTRAS = images/icon.png images/toporobot.png metadata.txt extras

UI_FILES = toporobotimporter_ui.py

RESOURCE_FILES = resources_rc.py

HELP = help

default: compile

compile: $(UI_FILES) $(RESOURCE_FILES)
	mkdir -p i18n

%_rc.py : %.qrc
	pyrcc5 -o $*_rc.py  $<

%_ui.py : %.ui
	pyuic5 -o $@ $<

%.qm : %.ts
	lrelease $<

test: compile
	$(PYQGIS) -m unittest discover -s tests/ -p "*test.py" -v

# The deploy  target only works on unix like operating system where
# the Python plugin directory is located at:
# $HOME/$(QGISDIR)/python/plugins
deploy: compile doc transcompile
	mkdir -p $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(UI_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vf $(RESOURCE_FILES) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vfr $(EXTRAS) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vfr i18n $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)
	cp -vfr $(HELP) $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)/

# The dclean target removes compiled python files from plugin directory
# also delets any .svn entry
dclean:
	find $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) -iname "*.pyc" -delete
	find $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) -iname "__pycache__" -delete
	find $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME) -iname ".svn" -prune -exec rm -Rf {} \;

# The derase deletes deployed plugin
derase:
	rm -Rf $(HOME)/$(QGISDIR)/python/plugins/$(PLUGINNAME)

# The zip target deploys the plugin and creates a zip file with the deployed
# content. You can then upload the zip file on http://plugins.qgis.org
zip: deploy dclean 
	rm -f $(PLUGINNAME).zip
	cd $(HOME)/$(QGISDIR)/python/plugins; zip -9r "$(CURDIR)"/$(PLUGINNAME).zip $(PLUGINNAME)

# Create a zip package of the plugin named $(PLUGINNAME).zip. 
# This requires use of git (your plugin development directory must be a 
# git repository).
# To use, pass a valid commit or tag as follows:
#   make package VERSION=Version_0.3.2
package: compile
		rm -f $(PLUGINNAME).zip
		git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip $(VERSION)
		echo "Created package: $(PLUGINNAME).zip"

upload: zip
	$(PLUGIN_UPLOAD) $(PLUGINNAME).zip

# transup
# update .ts translation files
transup:
	pylupdate4 Makefile

# transcompile
# compile translation files into .qm binary format
transcompile: $(TRANSLATIONS:.ts=.qm)

# transclean
# deletes all .qm files
transclean:
	rm -f i18n/*.qm

clean:
	rm $(UI_FILES) $(RESOURCE_FILES)

# build documentation with sphinx
doc: 
	#cd help; make html
