#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, Jacques Brunel
# Licence:         Licence GNU GPL
# Permet un choix dans une liste et retourne l'indice
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import CTRL_Bouton_image
from ObjectListView import FastObjectListView, ColumnDefn
import CTRL_Bandeau


class Dialog(wx.Dialog):
    def __init__(self, parent, listeOriginale=[("Choix1","Texte1"),],LargeurCode = 80,LargeurLib = 100, minSize=(600, 350),titre=_(u"Faites un choix !"), intro=_(u"Double Clic sur la réponse souhaitée...")):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.THICK_FRAME)
        self.SetTitle("aDLG_ChoixListe")
        self.choix= None
        self.parent = parent
        self.minSize = minSize
        self.wCode = LargeurCode
        self.wLib = LargeurLib
        self.liste = []
        for item in listeOriginale :
                self.liste.append((item[0],item[1]))
        # Bandeau
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")
        # conteneur des données
        self.resultsOlv = FastObjectListView(self)
        # Boutons
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Valider"), cheminImage="Images/32x32/Valider.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, texte=_(u"Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnDblClicOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnDblClicFermer, self.bouton_fermer)
        self.resultsOlv.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.OnDblClic)

    def __set_properties(self):
        self.SetMinSize(self.minSize)
        self.bouton_fermer.SetToolTipString(_(u"Cliquez ici pour fermer"))
        self.resultsOlv.SetToolTipString(_(u"Double Cliquez pour choisir"))
        # Couleur en alternance des lignes
        self.resultsOlv.oddRowsBackColor = "#F0FBED"
        self.resultsOlv.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.resultsOlv.useExpansionColumn = True
        self.resultsOlv.SetColumns([
            ColumnDefn("Code", "left", 0, 0),
            ColumnDefn("Code", "left", self.wCode, 0),
            ColumnDefn("Libelle (non modifiables)", "left", self.wLib, 1,isSpaceFilling = True),
            ])
        self.resultsOlv.SetSortColumn(self.resultsOlv.columns[0])
        self.resultsOlv.SetObjects(self.liste)

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=6, cols=1, vgap=0, hgap=0)

        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)
        gridsizer_base.Add(self.resultsOlv, 5, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)
        gridsizer_base.Add((5, 5), 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 0)

        # Boutons
        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=3, vgap=0, hgap=0)
        gridsizer_boutons.Add((20, 20), 1, wx.ALIGN_BOTTOM, 0)
        gridsizer_boutons.Add(self.bouton_ok, 1, wx.EXPAND, 0)
        gridsizer_boutons.Add(self.bouton_fermer, 1, wx.EXPAND, 0)
        gridsizer_boutons.AddGrowableCol(0)
        gridsizer_base.Add(gridsizer_boutons, 1, wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnDblClicFermer(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnDblClicOk(self, event):
        self.choix = self.resultsOlv.GetSelectedObject()
        if self.choix == None:
            dlg = wx.MessageDialog(self, _(u"Pas de sélection faite !\nIl faut choisir ou cliquer sur annuler"), _(u"Accord Impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.EndModal(wx.ID_OK)

    def OnDblClic(self, event):
        self.choix = self.resultsOlv.GetSelectedObject()
        self.EndModal(wx.ID_OK)

    def GetChoix(self):
        self.choix = self.resultsOlv.GetSelectedObject()
        return self.choix


if __name__ == u"__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    print dialog_1.ShowModal()
    app.MainLoop()
