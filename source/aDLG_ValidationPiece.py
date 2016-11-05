#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, Jacques Brunel
# Licence:         Licence GNU GPL
# Gestion de la validation de la pièce liée à l'inscription
# Adapté à partir de aDLG_SaisieArticles
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import CTRL_Bouton_image
import aGestionArticle
from ObjectListView import FastObjectListView, ColumnDefn
import copy
import aGestionDB
import CTRL_Bandeau

# -----------------------------------------------------------------------------------------------------------------
class Dialog(wx.Dialog):
    def __init__(self, parent, mode):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.THICK_FRAME)
        self.mode = mode
        self.parent = parent
        self.titre = (u"Gestion de l'état de la pièce")
        intro = (u"L'état de la pièce conditionne l'étape dans le processus de l'inscription")
        self.SetTitle("aDLG_ValidationPiece")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=self.titre, texte=intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")
        self.liste_naturePiece = copy.deepcopy(aGestionArticle.LISTEnaturesPieces)
        self.staticbox_CARACTER = wx.StaticBox(self, -1, _(u"Choix de l'état de la pièce"))
        self.staticbox_BOUTONS= wx.StaticBox(self, -1, )

        #Elements gérés
        self.liste_codesNaturesPiece = [str((a)) for a,b,c in self.liste_naturePiece]
        self.liste_commentNaturesPiece = [c for a,b,c in self.liste_naturePiece]
        self.resultsOlv = FastObjectListView(self)
        self.txt_naturesPiece = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE)

        self.ctrl_nature = wx.TextCtrl(self, -1, "",size=(100, 20))
        self.ctrl_nature.Label = "Choisir"
        self.codeNature = " "
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Valider"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.resultsOlv.SetToolTipString(_(u"Cliquez pour choisir"))
        self.resultsOlv.useExpansionColumn = True
        self.resultsOlv.SetColumns([
            ColumnDefn("Code", "left", 0, 0),
            ColumnDefn("Code", "left", 50, 0),
            ColumnDefn("Libelle", "left", 100, 1,isSpaceFilling = True),
            ])
        self.resultsOlv.SetObjects(self.liste_naturePiece)

        self.ctrl_nature.SetToolTipString(_(u"Faites le choix dans la liste ci-dessus"))
        self.bouton_ok.SetToolTipString(_(u"Cliquez ici pour valider et fermer"))
        self.bouton_annuler.SetToolTipString(_(u"Cliquez ici pour annuler et fermer"))
        self.SetMinSize((300, 350))
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.resultsOlv.Bind(wx.EVT_COMMAND_LEFT_CLICK, self.OnResultsOLV)
        self.resultsOlv.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnResultsOLV)

    def __do_layout(self):
        gridsizer_BASE = wx.FlexGridSizer(rows=3, cols=1, vgap=0, hgap=0)
        gridsizer_BASE.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        staticsizer_CARACTER = wx.StaticBoxSizer(self.staticbox_CARACTER, wx.VERTICAL)
        gridsizer_CARACTER = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        gridsizer_CARACTER.Add(self.resultsOlv, 1, wx.LEFT, 10)
        gridsizer_CARACTER.Add(self.txt_naturesPiece, 1, wx.LEFT|wx.EXPAND, 0)
        staticsizer_CARACTER.Add(gridsizer_CARACTER, 1, wx.RIGHT|wx.EXPAND,10)
        gridsizer_CARACTER.AddGrowableCol(1)
        gridsizer_BASE.Add(staticsizer_CARACTER, 1,wx.TOP|wx.EXPAND, 10)

        gridsizer_BOUTONS = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        staticsizer_BOUTONS = wx.StaticBoxSizer(self.staticbox_BOUTONS, wx.VERTICAL)
        gridsizer_BOUTONS.Add(self.ctrl_nature, 0, 0, 0)
        gridsizer_BOUTONS.Add((15, 15), 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_ok, 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_annuler, 0, 0, 0)
        gridsizer_BOUTONS.AddGrowableCol(1)
        staticsizer_BOUTONS.Add(gridsizer_BOUTONS, 1, wx.RIGHT|wx.EXPAND, 10)
        gridsizer_BASE.Add(staticsizer_BOUTONS, 1, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        self.SetSizer(gridsizer_BASE)
        gridsizer_BASE.Fit(self)
        gridsizer_BASE.AddGrowableRow(1)
        gridsizer_BASE.AddGrowableCol(0)
        self.Layout()
        self.CentreOnScreen()

    def OnResultsOLV(self, event):
        self.ctrl_nature.SetValue( str(self.resultsOlv.GetSelectedObject()[1]))
        self.txt_naturesPiece.SetValue( self.resultsOlv.GetSelectedObject()[2])
        self.codeNature = self.resultsOlv.GetSelectedObject()[0]

    def OnBoutonOk(self, event):
        # Vérification des données saisies
        textCode = self.ctrl_nature.GetValue()
        if textCode == "Choisir" :
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement choisir l'état de cette pièce !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None,"ajout")
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()