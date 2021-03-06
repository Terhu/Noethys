Noethys
==================
Logiciel de gestion libre et gratuit de gestion multi-activit�s pour 
les accueils de loisirs, cr�ches, garderies p�riscolaires, cantines, 
clubs sportifs et culturels...

Plus d'infos sur www.noethys.com


Proc�dure d'installation
------------------

Si vous souhaitez installer manuellement Noethys sur
Windows, Mac OS ou Linux, il vous suffit de copier
l'int�gralit� du r�pertoire sur votre disque dur et
d'installer toutes les d�pendances list�es ci-dessous.


D�pendances pour Windows
------------------
Sur Windows, vous devez aller sur les sites des auteurs pour 
rechercher et installer les biblioth�ques suivantes.

- Python 2.7 (http://www.python.org/)
- wxPython 3.0 - version unicode (http://www.wxpython.org/)
- dateutil (http://pypi.python.org/pypi/python-dateutil)
- MySQLdb (http://sourceforge.net/projects/mysql-python/)
- NumPy (http://new.scipy.org/download.html)
- PIL (http://www.pythonware.com/products/pil/)
- PyCrypto (https://www.dlitz.net/software/pycrypto/)
- PyCrypt (https://sites.google.com/site/reachmeweb/pycrypt)
- ReportLab (http://www.reportlab.com/software/opensource/rl-toolkit/download/)
- MatPlotLib (http://matplotlib.sourceforge.net/)
- ObjectListView (http://objectlistview.sourceforge.net/python/)
- pyExcelerator (http://sourceforge.net/projects/pyexcelerator/)
- videoCapture (http://videocapture.sourceforge.net/)
- Pyttsx (http://pypi.python.org/pypi/pyttsx)


D�pendances pour Linux
------------------

Biblioth�que graphique wxPython disponible sur le site de Noethys :
Menu T�l�chargements > Ressources communautaires > Divers.

- python 2.7 (install� en principe par d�faut sous ubuntu)
- python-mysqldb (Pour l'utilisation en mode r�seau)
- python-dateutil (Manipulation des dates)
- python-numpy (Calculs avanc�s)
- python-imaging (Traitement des photos)
- python-reportlab (Cr�ation des PDF)
- python-matplotlib (Cr�ation de graphes)
- python-xlrd (Traitement de fichiers Excel)
- python-crypto (pour crypter les sauvegardes)
- python-excelerator (pour les exports format excel)
- python-pyscard (pour pouvoir configurer les proc�dures de badgeage)
- python-opencv (pour la d�tection automatique des visages)
- python-pip (qui permet d'installer pyttsx et icalendar)

Ils s'installent depuis le terminal tout simplement avec la commande:

```
apt-get install python-mysqldb python-dateutil python-numpy python-imaging 
python-reportlab python-matplotlib python-xlrd python-excelerator python-pip 
python-pyscard python-opencv python-crypto
```

Et pour pyttsx et icalendar il faut avoir install� python-pip et les installer par:

- pip install pyttsx
- pip install icalendar


Pour lancer Noethys, lancez le terminal de Linux, placez-vous 
dans le r�pertoire d'installation de Noethys, puis saisissez
la commande "python Noethys.py"