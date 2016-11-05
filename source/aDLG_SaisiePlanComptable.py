#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, Jacques Brunel
# Licence:         Licence GNU GPL
# Gestion d'un enregistrement Compte définissant le regroupement dans le plan comptable
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import CTRL_Bouton_image
import CTRL_Bandeau

# -----------------------------------------------------------------------------------------------------------------
class Dialog(wx.Dialog):
    def __init__(self, parent,mode):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.THICK_FRAME)
        self.mode = mode
        self.parent = parent
        self.titre = (u"Gestion d'un Compte")
        intro = (u"Définit le regroupement des lignes dans la compta")
        self.SetTitle("aDLG_SaisiePlanComptable")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=self.titre, texte=intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")

        self.staticbox_nom = wx.StaticBox(self, -1, _(u"Identifiant du Compte"))
        self.staticbox_caracter = wx.StaticBox(self, -1, _(u"Caractéristiques du Compte"))
        self.staticbox_boutons = wx.StaticBox(self, -1, )

        #Elements gérés
        self.label_code = wx.StaticText(self, -1, "Code : ")
        self.ctrl_code = wx.TextCtrl(self, -1, "",size=(100, 20))
        self.label_libelle = wx.StaticText(self, -1, "Libelle : ")
        self.ctrl_libelle = wx.TextCtrl(self, -1, "")
        self.label_compta = wx.StaticText(self, -1, "Compte Comptable : ")
        self.ctrl_compta = wx.TextCtrl(self, -1, "")

        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_(u"Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.ctrl_code.Bind(wx.EVT_TEXT,self.OnCtrlCode,self.ctrl_code)

    def __set_properties(self):
        if self.mode =="modif" :
            self.label_code.Freeze()
            self.ctrl_code.Freeze()
        self.ctrl_code.SetToolTipString(_(u"16carMaxi - Saisissez ici un code de Compte qui permettra de l'appeler directement. "))
        self.ctrl_libelle.SetToolTipString(_(u"128carMax - Saisissez ici une déscription du Compte dans sa nature comptable"))
        self.ctrl_compta.SetToolTipString(_(u"8carMax - Saisissez ici le numéro de compte du plan comptable"))
        self.bouton_aide.SetToolTipString(_(u"Cliquez ici pour obtenir de l'aide"))
        self.bouton_ok.SetToolTipString(_(u"Cliquez ici pour valider et fermer"))
        self.bouton_annuler.SetToolTipString(_(u"Cliquez ici pour annuler et fermer"))
        self.SetMinSize((400, 400))

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        staticsizer_nom = wx.StaticBoxSizer(self.staticbox_nom, wx.VERTICAL)
        gridsizer_nom = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=5)
        gridsizer_nom.Add(self.label_code, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 0)
        gridsizer_nom.Add(self.ctrl_code, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 0)
        staticsizer_nom.Add(gridsizer_nom, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        gridsizer_base.Add(staticsizer_nom, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 10)

        staticsizer_caracter = wx.StaticBoxSizer(self.staticbox_caracter, wx.VERTICAL)
        gridsizer_caracter = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        gridsizer_caracter.Add(self.label_libelle, 0, wx.TOP|wx.ALIGN_RIGHT|wx.ALIGN_TOP, 23)
        gridsizer_caracter.Add(self.ctrl_libelle, 0, wx.TOP|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 20)
        gridsizer_caracter.Add(self.label_compta, 0, wx.TOP|wx.ALIGN_RIGHT|wx.ALIGN_TOP, 23)
        gridsizer_caracter.Add(self.ctrl_compta, 0, wx.TOP|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 20)
        gridsizer_caracter.AddGrowableCol(1)
        staticsizer_caracter.Add(gridsizer_caracter, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        gridsizer_base.Add(staticsizer_caracter, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 10)

        gridsizer_boutons = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        staticsizer_boutons = wx.StaticBoxSizer(self.staticbox_boutons, wx.VERTICAL)
        gridsizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        gridsizer_boutons.Add((15, 15), 0, 0, 0)
        gridsizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        gridsizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        gridsizer_boutons.AddGrowableCol(1)
        staticsizer_boutons.Add(gridsizer_boutons, 1, wx.RIGHT|wx.EXPAND, 10)
        gridsizer_base.Add(staticsizer_boutons, 1, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableRow(2)
        gridsizer_base.AddGrowableCol(0)
        self.Layout()
        self.CentreOnScreen()

    def OnBoutonAide(self, event):
        import UTILS_Aide
        UTILS_Aide.Aide("Comptes")

    def OnBoutonOk(self, event):
        # Vérification des données saisies
        textCode = self.ctrl_code.GetValue()
        if textCode == "" :
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement donner un code à ce Compte_ !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_code.SetFocus()
            return
        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)

    def OnCtrlCode(self,event) :
        event.Skip()
        selection = self.ctrl_code.GetSelection()
        value = self.ctrl_code.GetValue().upper()
        self.ctrl_code.ChangeValue(value)
        self.ctrl_code.SetSelection(*selection)

    def SetBloc(self,bloc):
        if len(bloc)==0 : return
        self.ctrl_code.SetValue(bloc[0])
        self.ctrl_libelle.SetValue(bloc[1])
        self.ctrl_compta.SetValue(bloc[2])

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None,"ajout")
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()