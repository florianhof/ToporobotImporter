ToporobotImporter
=================

QGIS plugin to import cave galleries from Toporobot / Limelight files.   
Website: [https://github.com/florianhof/ToporobotImporter/wiki](https://github.com/florianhof/ToporobotImporter/wiki)

Development
-----------

This plugin was initated with [Qgis Plugin Builder](http://g-sherman.github.io/Qgis-Plugin-Builder/). Some of the informations there also applies, for example the structure of the build (Makefile). 

**compile**  
This goal compiles the UI and resources into python files. For this is PyQt5 required. You can install it on the command line with `pip3 install PyQt5`

**test**
This goal runs the automatic tests. Because of the dependences to Qt and QGIS, it has to be run with the python interpreter of QGIS. Define its paths in the _Makefile_ as variable `PYQGIS` and is currently set for Mac.

**deploy**  
This goal install this plugin into QGIS. The path for QGIS' plugins is again be defined in the _Makefile_ as variable `QGISDIR` and is currently set for Mac. After the run, if the plugin was already loaded, it has to be manually reloaded from QGIS. 

**zip** 
Deploys to QGIS plugins folder and make a clean zip file. This zip is suitable to install or distribute the plugin. 