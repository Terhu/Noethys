#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, Jacques Brunel
# Licence:         Licence GNU GPL
# Gestion d'un enregistrement Blocs définissant le regroupement des lignes
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import CTRL_Bouton_image
import GestionDB
import aGestionArticle
import aDLG_ChoixListe
import CTRL_Bandeau

# -----------------------------------------------------------------------------------------------------------------
class Dialog(wx.Dialog):
    def __init__(self, parent,mode):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.THICK_FRAME)
        self.mode = mode
        self.parent = parent
        self.titre = (u"Gestion d'un Bloc")
        intro = (u"Définit une ligne de  appelée Bloc car regroupant des articles")
        self.SetTitle("aDLG_SaisieBlocsFacture")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=self.titre, texte=intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")
        self.liste_typeLigne = aGestionArticle.LISTEtypeLigne
        self.liste_formatLigne = aGestionArticle.LISTEformatLigne

        self.staticbox_nom = wx.StaticBox(self, -1, _(u"Nom du Bloc"))
        self.staticbox_caracter = wx.StaticBox(self, -1, _(u"Caractéristiques du bloc"))
        self.staticbox_boutons = wx.StaticBox(self, -1, )

        #Elements gérés
        #self.label_vide = wx.StaticText(self, -1, "_______________________")
        self.label_code = wx.StaticText(self, -1, "Code : ")
        self.ctrl_code = wx.TextCtrl(self, -1, "",size=(100, 20))
        self.label_libelle = wx.StaticText(self, -1, "Libelle : ")
        self.ctrl_libelle = wx.TextCtrl(self, -1, "")
        self.label_ordre = wx.StaticText(self, -1, _(u"No d'ordre :"))
        self.spin_ordre = wx.SpinCtrl(self, -1, "", min=0, max=100)

        self.liste_codesTypeLigne = [str((a)) for a,b in self.liste_typeLigne]
        self.label_typeLigne = wx.StaticText(self, -1, _(u"Type de Ligne  :"))
        self.choice_typeLigne = wx.Choice(self, -1, choices=self.liste_codesTypeLigne, )
        self.bouton_typeLigne = wx.Button(self, -1, "...", size=(20, 20))
        self.txt_typeLigne = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE)

        self.liste_codesFormatLigne = [str((a)) for a,b in self.liste_formatLigne]
        self.label_formatLigne = wx.StaticText(self, -1, _(u"Format d'édition de la Ligne :"))
        self.choice_formatLigne = wx.Choice(self, -1, choices=self.liste_codesFormatLigne, )
        self.bouton_formatLigne = wx.Button(self, -1, "...", size=(20, 20))
        self.txt_formatLigne = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE)


        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_(u"Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTypeLigne, self.bouton_typeLigne)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFormatLigne, self.bouton_formatLigne)
        self.ctrl_code.Bind(wx.EVT_TEXT,self.OnCtrlCode,self.ctrl_code)
        self.choice_typeLigne.Bind(wx.EVT_CHOICE,self.OnChoiceTypeLigne,self.choice_typeLigne)
        self.choice_formatLigne.Bind(wx.EVT_CHOICE,self.OnChoiceFormatLigne,self.choice_formatLigne)

    def __set_properties(self):
        if self.mode =="modif" :
            self.label_code.Freeze()
            self.ctrl_code.Freeze()
        self.ctrl_code.SetToolTipString(_(u"16carMaxi - Saisissez ici un code de bloc qui permettra de l'appeler directement. "))
        self.ctrl_libelle.SetToolTipString(_(u"128carMax - Saisissez ici une déscription du bloc évoquant ses options"))
        self.spin_ordre.SetMinSize((60, -1))
        self.choice_typeLigne.Select(0)
        self.txt_typeLigne.SetValue(self.liste_typeLigne[0][1])
        self.choice_typeLigne.SetToolTipString(_(u"Sélectionnez le type de Ligne  parmi la liste"))
        self.choice_formatLigne.Select(0)
        self.choice_formatLigne.SetToolTipString(_(u"Sélectionnez le format de Ligne  parmi la liste"))
        self.txt_formatLigne.SetValue(self.liste_formatLigne[0][1])
        self.bouton_aide.SetToolTipString(_(u"Cliquez ici pour obtenir de l'aide"))
        self.bouton_ok.SetToolTipString(_(u"Cliquez ici pour valider et fermer"))
        self.bouton_annuler.SetToolTipString(_(u"Cliquez ici pour annuler et fermer"))
        self.SetMinSize((400, 485))

    def __do_layout(self):
        gridsizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        staticsizer_nom = wx.StaticBoxSizer(self.staticbox_nom, wx.VERTICAL)
        gridsizer_nom = wx.FlexGridSizer(rows=2, cols=2, vgap=0, hgap=5)
        gridsizer_nom.Add(self.label_code, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 0)
        gridsizer_nom.Add(self.label_libelle, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 0)
        gridsizer_nom.Add(self.ctrl_code, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 0)
        gridsizer_nom.Add(self.ctrl_libelle, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 0)
        gridsizer_nom.AddGrowableCol(1)
        staticsizer_nom.Add(gridsizer_nom, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        gridsizer_base.Add(staticsizer_nom, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 10)

        staticsizer_caracter = wx.StaticBoxSizer(self.staticbox_caracter, wx.VERTICAL)
        gridsizer_caracter = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)

        gridsizer_car1 = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        gridsizer_car1.Add((10,10), 0,wx.ALIGN_RIGHT, 0)
        gridsizer_car1.Add(self.label_ordre, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
        gridsizer_car1.Add(self.spin_ordre, 0, wx.RIGHT|wx.ALIGN_RIGHT|wx.EXPAND, 10)
        gridsizer_car1.AddGrowableCol(0)
        gridsizer_caracter.Add(gridsizer_car1, 1, wx.RIGHT|wx.BOTTOM|wx.EXPAND, 20)

        gridsizer_car2 = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        gridsizer_car2.Add(self.label_typeLigne, 0, wx.ALIGN_RIGHT|wx.ALIGN_TOP, 0)
        gridsizer_car2.Add(self.choice_typeLigne, 0,wx.EXPAND, 0)
        gridsizer_car2.Add(self.bouton_typeLigne, 0,wx.LEFT, 0)
        gridsizer_car2.AddGrowableCol(0)
        gridsizer_car2.AddGrowableRow(0)
        gridsizer_caracter.Add(gridsizer_car2, 1, wx.LEFT|wx.TOP|wx.EXPAND, 10)
        gridsizer_caracter.Add(self.txt_typeLigne, 1, wx.LEFT|wx.BOTTOM|wx.EXPAND, 20)

        gridsizer_car3 = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        gridsizer_car3.Add(self.label_formatLigne, 0, wx.ALIGN_RIGHT|wx.ALIGN_TOP, 0)
        gridsizer_car3.Add(self.choice_formatLigne, 0,wx.EXPAND, 0)
        gridsizer_car3.Add(self.bouton_formatLigne, 0,wx.LEFT, 0)
        gridsizer_car3.AddGrowableCol(0)
        gridsizer_caracter.Add(gridsizer_car3, 1, wx.LEFT|wx.TOP|wx.EXPAND, 10)
        gridsizer_caracter.Add(self.txt_formatLigne, 1, wx.LEFT|wx.EXPAND, 20)

        staticsizer_caracter.Add(gridsizer_caracter, 1, wx.RIGHT|wx.EXPAND,10)
        gridsizer_caracter.AddGrowableCol(0)
        gridsizer_base.Add(staticsizer_caracter, 1,wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

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
        UTILS_Aide.Aide("Blocs")

    def OnBoutonOk(self, event):
        # Vérification des données saisies
        textCode = self.ctrl_code.GetValue()
        if textCode == "" :
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement donner un code à ce bloc_ !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_code.SetFocus()
            return
        ordre = int(self.spin_ordre.GetValue())
        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)

    def OnBoutonTypeLigne(self, event):
        intro = u"Le type de ligne détermine le comportement du regroupement des articles de la tarification"
        dlg = aDLG_ChoixListe.Dialog(self,LargeurCode= 120,LargeurLib= 300,minSize = (500,300), listeOriginale=self.liste_typeLigne, titre = self.titre, intro = intro)
        interroChoix = dlg.ShowModal()
        dlg.Destroy()
        if interroChoix == wx.ID_OK :
            ixChoix = self.liste_codesTypeLigne.index(dlg.choix[0])
            self.choice_typeLigne.SetSelection(ixChoix)
            self.txt_typeLigne.SetValue(self.liste_typeLigne[ixChoix][1])
            self.Show

    def OnChoiceTypeLigne(self,event):
        ixChoix = self.choice_typeLigne.GetSelection()
        self.txt_typeLigne.SetValue(self.liste_typeLigne[ixChoix][1])
        self.Show

    def OnBoutonFormatLigne(self, event):
        dlg2 = aDLG_ChoixListe.Dialog(self,LargeurCode= 100,LargeurLib= 200,minSize = (500,300), listeOriginale=self.liste_formatLigne, titre = u"Choisissez un Format de bloc ", intro = u"Ce format s'applique à la ligne sur la  ")
        interroChoix = dlg2.ShowModal()
        dlg2.Destroy()
        if interroChoix == wx.ID_OK :
            ixChoix = self.liste_codesFormatLigne.index(dlg2.choix[0])
            self.choice_formatLigne.SetSelection(ixChoix)
            self.txt_formatLigne.SetValue(self.liste_formatLigne[ixChoix][1])
            self.Show

    def OnChoiceFormatLigne(self,event):
        ixChoix = self.choice_formatLigne.GetSelection()
        self.txt_formatLigne.SetValue(self.liste_formatLigne[ixChoix][1])
        self.Show

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
        self.spin_ordre.SetValue(bloc[2])
        self.choice_typeLigne.SetStringSelection(bloc[3])
        self.choice_formatLigne.SetStringSelection(bloc[4])

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None,"ajout")
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()