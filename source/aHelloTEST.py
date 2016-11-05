#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#
import os, sys

frozen = getattr(sys, 'frozen', '')
if not frozen:
    REP_COURANT = os.path.dirname(os.path.abspath(__file__))
else :
    REP_COURANT = os.path.dirname(sys.executable)

if REP_COURANT not in sys.path :
    sys.path.insert(1, REP_COURANT)

for rep in os.listdir(REP_COURANT) :
    chemin = os.path.join(REP_COURANT, rep)
    if os.path.isdir(chemin) and chemin not in sys.path :
        sys.path.insert(2, chemin)

def GetStaticPath(fichier=""):
    """ Retourne le chemin du répertoire Static """
    chemin = os.path.join(REP_COURANT, "Static")
    return os.path.join(chemin, fichier)



if __name__ == '__main__':

    print REP_COURANT
