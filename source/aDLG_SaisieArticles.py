#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, Jacques Brunel
# Licence:         Licence GNU GPL
# Gestion des Articles composant les lignes de tarification
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import CTRL_Bouton_image
import aGestionArticle
import aDLG_ChoixListe
import aDLG_BlocsFacture
import aDLG_PlanComptable
import CTRL_Saisie_euros
import copy
import aGestionDB
import CTRL_Bandeau

# -----------------------------------------------------------------------------------------------------------------
class Dialog(wx.Dialog):
    def __init__(self, parent, mode):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.THICK_FRAME)
        self.mode = mode
        self.parent = parent
        self.titre = (u"Gestion d'un Article")
        intro = (u"Définit une ligne de  tarification appelée Article")
        self.SetTitle("aDLG_SaisieArticles")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=self.titre, texte=intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")
        self.liste_conditions = aGestionArticle.LISTEconditions
        self.liste_modeCalcul = aGestionArticle.LISTEmodeCalcul
        self.liste_blocFacture = self.InitBlocFacture()
        self.liste_codesBlocFacture = [str((a)) for a,b in self.liste_blocFacture]
        self.liste_comptable =   self.InitComptable()
        self.liste_codesComptable = [str((a)) for a,b in self.liste_comptable]
        self.staticbox_NOM = wx.StaticBox(self, -1, _(u"Nom de l'article"))
        self.staticbox_CARACTER = wx.StaticBox(self, -1, _(u"Caractéristiques de l'article"))
        self.staticbox_BOUTONS= wx.StaticBox(self, -1, )

        #Elements gérés
        self.label_code = wx.StaticText(self, -1, "Code : ")
        self.ctrl_code = wx.TextCtrl(self, -1, "",size=(100, 20))
        self.label_libelle = wx.StaticText(self, -1, "Libelle : ")
        self.ctrl_libelle = wx.TextCtrl(self, -1, "")

        self.liste_codesConditions = [str((a)) for a,b,c,d in self.liste_conditions]
        self.label_conditions = wx.StaticText(self, -1, _(u"Conditions  :"))
        self.choice_conditions = wx.Choice(self, -1, choices=self.liste_codesConditions, )
        self.bouton_conditions = wx.Button(self, -1, "...", size=(20, 20))
        self.txt_conditions = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE)

        self.liste_codesModeCalcul = [str((a)) for a,b, c in self.liste_modeCalcul]
        self.label_modeCalcul = wx.StaticText(self, -1, _(u"Calcul du prix :"))
        self.choice_modeCalcul = wx.Choice(self, -1, choices=self.liste_codesModeCalcul, )
        self.bouton_modeCalcul = wx.Button(self, -1, "...", size=(20, 20))
        self.txt_modeCalcul = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE)

        self.label_prix1 = wx.StaticText(self, -1, _(u"Prix de base :"))
        self.ctrl_prix1 =  CTRL_Saisie_euros.CTRL(self)
        self.label_prix2 = wx.StaticText(self, -1, _(u"Prix alternatif :"))
        self.ctrl_prix2 =  CTRL_Saisie_euros.CTRL(self)

        self.label_blocFacture = wx.StaticText(self, -1, _(u"Bloc facture :"))
        self.choice_blocFacture = wx.Choice(self, -1, choices=self.liste_codesBlocFacture, )
        self.bouton_blocFacture = wx.Button(self, -1, "...", size=(20, 20))
        self.txt_blocFacture = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE)

        self.label_comptable = wx.StaticText(self, -1, _(u"Compte comptablité :"))
        self.choice_comptable = wx.Choice(self, -1, choices=self.liste_codesComptable, )
        self.bouton_comptable = wx.Button(self, -1, "...", size=(20, 20))
        self.txt_comptable = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE)

        self.check_NiveauActivite = wx.CheckBox(self, 0, _(u"Proposé au niveau de l'activité"))
        self.check_NiveauFamille = wx.CheckBox(self, -1, _(u"Proposé au niveau de la famille"))

        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_(u"Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonConditions, self.bouton_conditions)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModeCalcul, self.bouton_modeCalcul)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonBlocFacture, self.bouton_blocFacture)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonComptable, self.bouton_comptable)
        self.ctrl_code.Bind(wx.EVT_TEXT,self.OnCtrlCode,self.ctrl_code)
        self.choice_conditions.Bind(wx.EVT_CHOICE,self.OnChoiceConditions,self.choice_conditions)
        self.choice_modeCalcul.Bind(wx.EVT_CHOICE,self.OnChoiceModeCalcul,self.choice_modeCalcul)
        self.choice_blocFacture.Bind(wx.EVT_CHOICE,self.OnChoiceBlocFacture,self.choice_blocFacture)
        self.choice_comptable.Bind(wx.EVT_CHOICE,self.OnChoiceComptable,self.choice_comptable)

    def __set_properties(self):
        if self.mode =="modif" :
            self.label_code.Enable(False)
            self.ctrl_code.Enable(False)
        self.ctrl_code.SetToolTipString(_(u"16carMaxi - Saisissez ici un code article qui permettra de l'appeler directement. "))
        self.ctrl_libelle.SetToolTipString(_(u"128carMax - Saisissez ici une déscription de l'article évoquant ses options"))
        self.choice_conditions.SetToolTipString(_(u"Sélectionnez les conditions  parmi la liste"))
        self.choice_modeCalcul.SetToolTipString(_(u"Sélectionnez le format de Ligne  parmi la liste"))
        self.choice_blocFacture.SetToolTipString(_(u"Sélectionnez le regroupement facture parmi la liste"))
        self.choice_comptable.SetToolTipString(_(u"Sélectionnez le regroupement comptable parmi la liste"))
        self.check_NiveauActivite.SetToolTipString(_(u"L'article est proposé au Niveau Activité"))
        self.check_NiveauFamille.SetToolTipString(_(u"L'article est proposé au Niveau Famille"))
        self.bouton_aide.SetToolTipString(_(u"Cliquez ici pour obtenir de l'aide"))
        self.bouton_ok.SetToolTipString(_(u"Cliquez ici pour valider et fermer"))
        self.bouton_annuler.SetToolTipString(_(u"Cliquez ici pour annuler et fermer"))
        self.SetMinSize((400, 600))

    def __do_layout(self):
        gridsizer_BASE = wx.FlexGridSizer(rows=4, cols=1, vgap=0, hgap=0)
        gridsizer_BASE.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        staticsizer_NOM = wx.StaticBoxSizer(self.staticbox_NOM, wx.VERTICAL)
        gridsizer_NOM = wx.FlexGridSizer(rows=2, cols=2, vgap=0, hgap=5)
        gridsizer_NOM.Add(self.label_code, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 0)
        gridsizer_NOM.Add(self.label_libelle, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 0)
        gridsizer_NOM.Add(self.ctrl_code, 0, wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL, 0)
        gridsizer_NOM.Add(self.ctrl_libelle, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 0)
        gridsizer_NOM.AddGrowableCol(1)
        staticsizer_NOM.Add(gridsizer_NOM, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        gridsizer_BASE.Add(staticsizer_NOM, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)

        staticsizer_CARACTER = wx.StaticBoxSizer(self.staticbox_CARACTER, wx.VERTICAL)
        gridsizer_CARACTER = wx.FlexGridSizer(rows=11, cols=1, vgap=5, hgap=5)

        gridsizer_COND = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        gridsizer_COND.Add(self.label_conditions, 0, wx.ALIGN_RIGHT|wx.ALIGN_TOP, 0)
        gridsizer_COND.Add(self.choice_conditions, 0,wx.EXPAND, 0)
        gridsizer_COND.Add(self.bouton_conditions, 0,wx.LEFT, 0)
        gridsizer_COND.AddGrowableCol(0)
        gridsizer_COND.AddGrowableRow(0)
        gridsizer_CARACTER.Add(gridsizer_COND, 1, wx.LEFT|wx.TOP|wx.EXPAND, 10)
        gridsizer_CARACTER.Add(self.txt_conditions, 1, wx.LEFT|wx.EXPAND, 20)

        gridsizer_CALC = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        gridsizer_CALC.Add(self.label_modeCalcul, 0, wx.ALIGN_RIGHT|wx.ALIGN_TOP, 0)
        gridsizer_CALC.Add(self.choice_modeCalcul, 0,wx.EXPAND, 0)
        gridsizer_CALC.Add(self.bouton_modeCalcul, 0,wx.LEFT, 0)
        gridsizer_CALC.AddGrowableCol(0)
        gridsizer_CARACTER.Add(gridsizer_CALC, 1, wx.LEFT|wx.TOP|wx.EXPAND, 10)
        gridsizer_CARACTER.Add(self.txt_modeCalcul, 1, wx.LEFT|wx.EXPAND, 20)

        gridsizer_PRIX = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        gridsizer_PRIX.Add(self.label_prix1, 0, wx.ALIGN_RIGHT|wx.ALIGN_TOP, 0)
        gridsizer_PRIX.Add(self.ctrl_prix1, 1,wx.EXPAND, 0)
        gridsizer_PRIX.Add(self.label_prix2, 0, wx.ALIGN_RIGHT|wx.ALIGN_TOP, 0)
        gridsizer_PRIX.Add(self.ctrl_prix2, 1,wx.EXPAND, 0)
        gridsizer_CARACTER.Add(gridsizer_PRIX, 1, wx.LEFT|wx.TOP|wx.EXPAND, 10)

        gridsizer_FACT = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        gridsizer_FACT.Add(self.label_blocFacture, 0, wx.ALIGN_RIGHT|wx.ALIGN_TOP, 0)
        gridsizer_FACT.Add(self.choice_blocFacture, 0,wx.EXPAND, 0)
        gridsizer_FACT.Add(self.bouton_blocFacture, 0,wx.LEFT, 0)
        gridsizer_FACT.AddGrowableCol(1)
        gridsizer_CARACTER.Add(gridsizer_FACT, 1, wx.LEFT|wx.TOP|wx.EXPAND, 10)
        gridsizer_CARACTER.Add(self.txt_blocFacture, 1, wx.LEFT|wx.EXPAND, 20)

        gridsizer_COMPTE = wx.FlexGridSizer(rows=1, cols=3, vgap=10, hgap=10)
        gridsizer_COMPTE.Add(self.label_comptable, 0, wx.ALIGN_RIGHT|wx.ALIGN_TOP, 0)
        gridsizer_COMPTE.Add(self.choice_comptable, 0,wx.EXPAND, 0)
        gridsizer_COMPTE.Add(self.bouton_comptable, 0,wx.LEFT, 0)
        gridsizer_COMPTE.AddGrowableCol(0)
        gridsizer_CARACTER.Add(gridsizer_COMPTE, 1, wx.LEFT|wx.TOP|wx.EXPAND, 10)
        gridsizer_CARACTER.Add(self.txt_comptable, 1, wx.LEFT|wx.EXPAND, 20)

        gridsizer_OPTIONS = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        gridsizer_OPTIONS.Add(self.check_NiveauActivite, 0,wx.EXPAND, 0)
        gridsizer_OPTIONS.Add(self.check_NiveauFamille, 0,wx.EXPAND, 0)
        gridsizer_OPTIONS.AddGrowableCol(0)
        gridsizer_CARACTER.Add(gridsizer_OPTIONS, 1, wx.LEFT|wx.TOP|wx.EXPAND, 10)

        staticsizer_CARACTER.Add(gridsizer_CARACTER, 1, wx.RIGHT|wx.EXPAND,10)
        gridsizer_CARACTER.AddGrowableCol(0)
        gridsizer_BASE.Add(staticsizer_CARACTER, 1,wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        gridsizer_BOUTONS = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        staticsizer_BOUTONS = wx.StaticBoxSizer(self.staticbox_BOUTONS, wx.VERTICAL)
        gridsizer_BOUTONS.Add(self.bouton_aide, 0, 0, 0)
        gridsizer_BOUTONS.Add((15, 15), 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_ok, 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_annuler, 0, 0, 0)
        gridsizer_BOUTONS.AddGrowableCol(1)
        staticsizer_BOUTONS.Add(gridsizer_BOUTONS, 1, wx.RIGHT|wx.EXPAND, 10)
        gridsizer_BASE.Add(staticsizer_BOUTONS, 1, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        self.SetSizer(gridsizer_BASE)
        gridsizer_BASE.Fit(self)
        gridsizer_BASE.AddGrowableRow(2)
        gridsizer_BASE.AddGrowableCol(0)
        self.Layout()
        self.CentreOnScreen()

    def Requete(self,req):
        db = aGestionDB.DB()
        liste = []
        retour = db.ExecuterReq(req)
        if retour == "ok" :
            liste = copy.deepcopy(db.ResultatReq())
        else :
            aGestionDB.MessageBox(self,retour)
        db.Close()
        return liste

    def InitBlocFacture(self):
        req = """SELECT lfaCodeBlocFacture,lfaLibelle
        FROM matBlocsFactures ORDER BY lfaCodeBlocFacture; """
        liste = self.Requete(req)
        return liste

    def InitComptable(self):
        req = """SELECT pctCodeComptable,pctLibelle
        FROM matPlanComptable ORDER BY pctCodeComptable; """
        liste = self.Requete(req)
        return liste

    def OnBoutonAide(self, event):
        import UTILS_Aide
        UTILS_Aide.Aide("Articles")

    def OnBoutonOk(self, event):
        # Vérification des données saisies
        textCode = self.ctrl_code.GetValue()
        if textCode == "" :
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement donner un code à cet article_ !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_code.SetFocus()
            return
        # Fermeture de la fenêtre
        self.EndModal(wx.ID_OK)

    def OnBoutonConditions(self, event):
        intro = u"Les conditions sont évaluées pour l'apparition de l'article au moment de la tarification"
        dlg = aDLG_ChoixListe.Dialog(self,LargeurCode= 120,LargeurLib= 300,minSize = (500,300), listeOriginale=self.liste_conditions, titre = "Choix des conditions tarifaires", intro = intro)
        interroChoix = dlg.ShowModal()
        dlg.Destroy()
        if interroChoix == wx.ID_OK :
            ixChoix = self.liste_codesConditions.index(dlg.choix[0])
            self.choice_conditions.SetSelection(ixChoix)
            self.txt_conditions.SetValue(self.liste_conditions[ixChoix][1])
            self.Show()

    def OnChoiceConditions(self,event):
        ixChoix = self.choice_conditions.GetSelection()
        self.txt_conditions.SetValue(self.liste_conditions[ixChoix][1])
        self.Show()

    def OnBoutonModeCalcul(self, event):
        dlg2 = aDLG_ChoixListe.Dialog(self,LargeurCode= 100,LargeurLib= 200,minSize = (500,300), listeOriginale=self.liste_modeCalcul, titre = u"Choisissez un mode de calcul", intro = u"Ce calcul détermira le prix en fonction des circonstances  ")
        interroChoix = dlg2.ShowModal()
        dlg2.Destroy()
        if interroChoix == wx.ID_OK :
            ixChoix = self.liste_codesModeCalcul.index(dlg2.choix[0])
            self.choice_modeCalcul.SetSelection(ixChoix)
            self.txt_modeCalcul.SetValue(self.liste_modeCalcul[ixChoix][1])
            self.Show()

    def OnChoiceModeCalcul(self,event):
        ixChoix = self.choice_modeCalcul.GetSelection()
        self.txt_modeCalcul.SetValue(self.liste_modeCalcul[ixChoix][1])
        self.Show()

    def OnBoutonBlocFacture(self, event):
        intro = u"Le type de ligne détermine le comportement du regroupement des articles de la tarification"
        dlg = aDLG_BlocsFacture.Dialog(self)
        interroChoix = dlg.ShowModal()
        dlg.Destroy()
        if interroChoix == wx.ID_OK :
            self.liste_blocFacture =   self.InitBlocFacture()
            self.liste_codesBlocFacture = [str((a)) for a,b in self.liste_blocFacture]
            self.choice_blocFacture.Clear() # Clear the current user list
            self.choice_blocFacture.AppendItems(self.liste_codesBlocFacture) # Repopulate the list
            ixChoix = self.liste_codesBlocFacture.index(dlg.choix[0])
            self.choice_blocFacture.SetSelection(ixChoix)
            self.liste_blocFacture = self.InitBlocFacture()
            self.txt_blocFacture.SetValue(self.liste_blocFacture[ixChoix][1])
            self.Show()

    def OnChoiceBlocFacture(self,event):
        ixChoix = self.choice_blocFacture.GetSelection()
        self.txt_blocFacture.SetValue(self.liste_blocFacture[ixChoix][1])
        self.Show()

    def OnBoutonComptable(self, event):
        dlg = aDLG_PlanComptable.Dialog(self)
        interroChoix = dlg.ShowModal()
        dlg.Destroy()
        if interroChoix == wx.ID_OK :
            self.liste_comptable =   self.InitComptable()
            self.liste_codesComptable = [str((a)) for a,b in self.liste_comptable]
            self.choice_comptable.Clear() # Clear the current user list
            self.choice_comptable.AppendItems(self.liste_codesComptable) # Repopulate the list
            ixChoix = self.liste_codesComptable.index(dlg.choix[0])
            self.choice_comptable.SetSelection(ixChoix)
            self.txt_comptable.SetValue(self.liste_comptable[ixChoix][1])
            self.Show()

    def OnChoiceComptable(self,event):
        ixChoix = self.choice_comptable.GetSelection()
        self.txt_comptable.SetValue(self.liste_comptable[ixChoix][1])
        self.Show()

    def OnCtrlCode(self,event) :
        event.Skip()
        selection = self.ctrl_code.GetSelection()
        value = self.ctrl_code.GetValue().upper()
        self.ctrl_code.ChangeValue(value)
        self.ctrl_code.SetSelection(*selection)

    def CreeArticle(self):
        self.choice_conditions.SetStringSelection("sans")
        self.choice_modeCalcul.SetStringSelection("simple")
        self.ctrl_prix1.SetValue(str("{:10.2f}".format(0)))
        self.ctrl_prix2.SetValue(str("{:10.2f}".format(0)))
        self.check_NiveauActivite.SetValue(1)
        self.check_NiveauFamille.SetValue(1)

    def SetArticle(self,track):
        if track.len ==0 : return
        self.ctrl_code.SetValue(track.code)
        self.ctrl_libelle.SetValue(track.libelle)
        self.choice_conditions.SetStringSelection(track.conditions)
        self.choice_modeCalcul.SetStringSelection(track.calcul)
        self.ctrl_prix1.SetValue(str("{:10.2f}".format((track.prix1))))
        self.ctrl_prix2.SetValue(str("{:10.2f}".format((track.prix2))))
        if track.facture == None: track.facture = " "
        self.choice_blocFacture.SetStringSelection(track.facture)
        if track.compta == None: track.compta = " "
        self.choice_comptable.SetStringSelection(track.compta)
        if track.nivActivite == None: track.nivActivite = True
        self.check_NiveauActivite.SetValue(track.nivActivite)
        if track.nivFamille == None: track.nivFamille = True
        self.check_NiveauFamille.SetValue(track.nivFamille)
        if self.mode == "modif" :
            self.txt_conditions.SetValue(self.liste_conditions[self.choice_conditions.GetSelection()][1])
            self.txt_modeCalcul.SetValue(self.liste_modeCalcul[self.choice_modeCalcul.GetSelection()][1])
            self.txt_blocFacture.SetValue(self.liste_blocFacture[self.choice_blocFacture.GetSelection()][1])
            self.txt_comptable.SetValue(self.liste_comptable[self.choice_comptable.GetSelection()][1])

    def GetArticle(self):
        record = [
            ("code", self.ctrl_code.GetValue()),
            ("libelle", self.ctrl_libelle.GetValue()),
            ("conditions", self.choice_conditions.GetStringSelection()),
            ("calcul", self.choice_modeCalcul.GetStringSelection()),
            ("prix1", float(self.ctrl_prix1.GetValue())),
            ("prix2", float(self.ctrl_prix2.GetValue())),
            ("facture", self.choice_blocFacture.GetStringSelection()),
            ("compta", self.choice_comptable.GetStringSelection()),
            ("nivFamille", self.check_NiveauFamille.GetValue()),
            ("nivActivite", self.check_NiveauActivite.GetValue()),
            ]
        return record

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None,"ajout")
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()