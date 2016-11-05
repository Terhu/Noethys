#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, Jacques Brunel
# Licence:         Licence GNU GPL
# Gestion des Noms et des lignes d'articles des tarifs
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
from ObjectListView import FastObjectListView
import CTRL_Bouton_image
import CTRL_Bandeau
import aGestionDB
import aOL_TarifsLignesArticles
import aOL_TarifsLignesAffectations
#import aOL_BlocsFacture
# -----------------------------------------------------------------------------------------------------------------
class Notebook(wx.Notebook):
    def __init__(self, parent, id=-1):
        wx.Notebook.__init__(self, parent, id, style= wx.BK_DEFAULT)
        self.ctrl_code = parent.ctrl_code

        self.dictPages = {}
        #      codePage,       labelPage,         ctrlPage,              imgPage
        self.listePages = [
            ("affectations", _(u"Affectations_Camps"), u"PanelAffectations(self)", "Composition.png"),
            ("articles", _(u"Lignes_Articles"), u"PanelArticles(self)", "Cocher.png"),
            ]

        # ImageList pour le NoteBook
        il = wx.ImageList(16, 16)
        index = 0
        for codePage, labelPage, ctrlPage, imgPage in self.listePages :
            exec("self.img%d = il.Add(wx.Bitmap('Images/16x16/%s', wx.BITMAP_TYPE_PNG))" % (index, imgPage))
            index += 1
        self.AssignImageList(il)

        # Création des pages
        index = 0
        for codePage, labelPage, ctrlPage, imgPage in self.listePages :
            exec("self.page%d = %s" % (index, ctrlPage))
            exec("self.AddPage(self.page%d, u'%s')" % (index, labelPage))
            exec("self.SetPageImage(%d, self.img%d)" % (index, index))
            exec("self.dictPages['%s'] = {'ctrl' : self.page%d, 'index' : %d}" % (codePage, index, index))
            index += 1
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def GetPageAvecCode(self, codePage=""):
        return self.dictPages[codePage]["ctrl"]

    def AffichePage(self, codePage=""):
        indexPage = self.dictPages[codePage]["index"]
        self.SetSelection(indexPage)

    def OnPageChanged(self, event):
        """ Quand une page du notebook est sélectionnée """
        indexAnciennePage = event.GetOldSelection()
        indexPage = event.GetSelection()
        codePage = self.listePages[indexAnciennePage][0]
        # Sauvegarde ancienne page si besoin
        if indexAnciennePage!=wx.NOT_FOUND:
            anciennePage = self.GetPage(indexAnciennePage)
        indexPage = event.GetSelection()
        page = self.GetPage(indexPage)
        self.Freeze()
        wx.CallLater(1, page.MAJ)
        self.Thaw()
        event.Skip()

    def MAJpageActive(self):
        """ MAJ la page active du notebook """
        indexPage = self.GetSelection()
        page = self.GetPage(indexPage)
        wx.CallLater(1, page.MAJ)

    def MAJpage(self, codePage=""):
        page = self.dictPages[codePage]["ctrl"]
        wx.CallLater(1, page.MAJ)

class PanelArticles(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="panel_articles", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.staticbox_articles = wx.StaticBox(self, -1, _(u"Lignes d'articles"))
        self.ctrl_code = parent.ctrl_code
        self.ctrl_listview = aOL_TarifsLignesArticles.ListView(self, id=-1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.ctrl_listview.cellEditMode = FastObjectListView.CELLEDIT_SINGLECLICK
        #self.ctrl_listview.MAJ()
        self.ctrl_recherche = aOL_TarifsLignesArticles.CTRL_Outils(self, listview=self.ctrl_listview)

        self.bouton_ajouter = wx.BitmapButton(self, -1, wx.Bitmap("Images/16x16/Ajouter.png", wx.BITMAP_TYPE_ANY))
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap("Images/16x16/Modifier.png", wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap("Images/16x16/Supprimer.png", wx.BITMAP_TYPE_ANY))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.Ajouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.Modifier, self.bouton_modifier)

    def __set_properties(self):
        self.ctrl_listview.SetToolTipString(_(u"Un clic sur les coches pour ajouter l'article au tarif ou le précocher. Un double clic est pour modifier l'article"))
        self.bouton_ajouter.SetToolTipString(_(u"Créer un nouvel article inexistant"))
        self.bouton_modifier.SetToolTipString(_(u"Modifier les caractéristiques de l'article sélectionné dans la liste"))
        self.bouton_supprimer.SetToolTipString(_(u"Supprimer définitivement un article inutilisé"))
        self.SetMinSize((800, 600))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        staticbox_articles = wx.StaticBoxSizer(self.staticbox_articles, wx.VERTICAL)
        grid_sizer_articles = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)

        grid_sizer_articles.Add(self.ctrl_listview, 1, wx.EXPAND, 0)

        grid_sizer_boutons = wx.FlexGridSizer(rows=6, cols=1, vgap=5, hgap=5)
        grid_sizer_boutons.Add(self.bouton_ajouter, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_modifier, 0, wx.ALL, 0)
        grid_sizer_boutons.Add(self.bouton_supprimer, 0, wx.ALL, 0)
        grid_sizer_articles.Add(grid_sizer_boutons, 1, wx.ALL, 0)

        grid_sizer_articles.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)

        grid_sizer_articles.AddGrowableCol(0)
        grid_sizer_articles.AddGrowableRow(0)
        staticbox_articles.Add(grid_sizer_articles, 1, wx.EXPAND|wx.ALL, 5)

        grid_sizer_base.Add(staticbox_articles, 1, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)

    def Ajouter(self, event):
        self.ctrl_listview.Ajouter(None)

    def Modifier(self, event):
        self.ctrl_listview.Modifier(None)

    def Supprimer(self, event):
        self.ctrl_listview.Supprimer(None)

    def MAJ(self):
        self.ctrl_listview.MAJ()
    #fin de PanelArticles

class PanelAffectations(wx.Panel):
    def __init__(self, parent, IDfamille=None):
        wx.Panel.__init__(self, parent, id=-1, name="panel_quotients", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.staticbox_Affectations = wx.StaticBox(self, -1, _(u"Lignes d'Affectations"))
        self.ctrl_code = parent.ctrl_code
        self.ctrl_listview = aOL_TarifsLignesAffectations.ListView(self, id=-1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.ctrl_listview.cellEditMode = FastObjectListView.CELLEDIT_SINGLECLICK
        self.ctrl_recherche = aOL_TarifsLignesAffectations.CTRL_Outils(self, listview=self.ctrl_listview)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.ctrl_listview.SetToolTipString(_(u"Un clic sur la coche pour ajouter l'Affectation au tarif."))
        self.SetMinSize((800, 600))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        staticbox_Affectations = wx.StaticBoxSizer(self.staticbox_Affectations, wx.VERTICAL)
        grid_sizer_Affectations = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)

        grid_sizer_Affectations.Add(self.ctrl_listview, 1, wx.EXPAND, 0)
        grid_sizer_Affectations.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)

        grid_sizer_Affectations.AddGrowableCol(0)
        grid_sizer_Affectations.AddGrowableRow(0)
        staticbox_Affectations.Add(grid_sizer_Affectations, 1, wx.EXPAND|wx.ALL, 5)

        grid_sizer_base.Add(staticbox_Affectations, 1, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)

    def MAJ(self):
        self.ctrl_listview.MAJ()
    #fin de PanelAffectations

class Dialog(wx.Dialog):
    def __init__(self, parent,mode):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.THICK_FRAME)
        self.mode = mode
        self.parent = parent
        self.titre = (u"Gestion d'un Tarif")
        intro = (u"Crée ou modifie un tarif par la table matTarifsNoms et matTarifsLignes. Seuls les articles cochés seront proposés dans le tarif en plus de ceux préfixés '*'")
        self.SetTitle("aDLG_TarifsLignes")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=self.titre, texte=intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")
        self.staticbox_NOM = wx.StaticBox(self, -1, _(u"Nom du Tarif"))
        self.staticbox_BOUTONS= wx.StaticBox(self, -1, )

        #Elements gérés
        self.label_code = wx.StaticText(self, -1, "Code : ")
        self.ctrl_code = wx.TextCtrl(self, -1, "",size=(100, 20))
        self.label_libelle = wx.StaticText(self, -1, "Libelle : ")
        self.ctrl_libelle = wx.TextCtrl(self, -1, "")
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_(u"Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Ok"), cheminImage="Images/32x32/Valider.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"), cheminImage="Images/32x32/Annuler.png")
        self.label_annee = wx.StaticText(self, -1, u"Année pour affectations : ")
        self.ctrl_annee = wx.TextCtrl(self, -1, "",size=(100, 20))
        self.GetAnnee()

        self.notebook = Notebook(self)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_TEXT,self.OnCtrlCode,self.ctrl_code)
        self.ctrl_code.Bind(wx.EVT_KILL_FOCUS,self.OnCtrlCodeModif)
        self.ctrl_annee.Bind(wx.EVT_KILL_FOCUS,self.OnCtrlAnneeModif)
        self.notebook.SetFocus()

    def __set_properties(self):
        if self.mode =="modif" :
            self.label_code.Enable(False)
            self.ctrl_code.Enable(False)
        self.ctrl_code.SetToolTipString(_(u"16carMaxi - Saisissez ici un code de tarif qui permettra de l'appeler directement. "))
        self.ctrl_libelle.SetToolTipString(_(u"128carMax - Saisissez ici une déscription du tarif"))
        self.bouton_aide.SetToolTipString(_(u"Cliquez ici pour obtenir de l'aide"))
        self.bouton_ok.SetToolTipString(_(u"Cliquez ici pour valider et fermer"))
        self.bouton_annuler.SetToolTipString(_(u"Cliquez ici pour annuler et fermer"))
        self.label_annee.SetToolTipString(_(u"Saisissez l'année des activités affectées aux tarifs"))
        self.ctrl_annee.SetToolTipString(_(u"Saisissez l'année des activités affectées aux tarifs"))
        self.notebook.SetMinSize((-1, 260))
        self.SetMinSize((800, 600))

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

        gridsizer_BASE.Add(self.notebook, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        gridsizer_BOUTONS = wx.FlexGridSizer(rows=1, cols=6, vgap=10, hgap=10)
        staticsizer_BOUTONS = wx.StaticBoxSizer(self.staticbox_BOUTONS, wx.VERTICAL)
        gridsizer_BOUTONS.Add(self.bouton_aide, 0, wx.ALIGN_BOTTOM, 0)
        gridsizer_BOUTONS.Add(self.label_annee, 0, wx.ALIGN_CENTER, 0)
        gridsizer_BOUTONS.Add(self.ctrl_annee, 0, wx.ALIGN_CENTER, 0)
        gridsizer_BOUTONS.Add((15, 15), 0, wx.ALIGN_BOTTOM, 0)
        gridsizer_BOUTONS.Add(self.bouton_ok, 0, wx.ALIGN_BOTTOM, 0)
        gridsizer_BOUTONS.Add(self.bouton_annuler, 0, wx.ALIGN_BOTTOM, 0)
        gridsizer_BOUTONS.AddGrowableCol(3)
        gridsizer_BOUTONS.AddGrowableRow(0)
        staticsizer_BOUTONS.Add(gridsizer_BOUTONS, 1,wx.BOTTOM| wx.RIGHT|wx.EXPAND, 10)
        gridsizer_BASE.Add(staticsizer_BOUTONS, 1,wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        self.SetSizer(gridsizer_BASE)
        gridsizer_BASE.Fit(self)
        gridsizer_BASE.AddGrowableRow(2)
        gridsizer_BASE.AddGrowableCol(0)
        self.Layout()
        self.CentreOnScreen()

    def Ajouter(self, event):
        self.panel_articles.Ajouter(None)

    def Modifier(self, event):
        self.panel_articles.Modifier(None)

    def Supprimer(self, event):
        self.panel_articles.Supprimer(None)

    def OnBoutonAide(self, event):
        import UTILS_Aide
        UTILS_Aide.Aide("Noms")

    def OnBoutonOk(self, event):
        # Vérification des données saisies
        textCode = self.ctrl_code.GetValue()
        if textCode == "" :
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement donner un code à ce nom_ !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_code.SetFocus()
            return
        # Fermeture de la fenêtre
        self.SauveDonnees()
        self.EndModal(wx.ID_OK)

    def SauveDonnees(self):
        for page in ("page0","page1"):
            listeCoches = []
            exec("objects = self.notebook.%s.ctrl_listview.GetObjects()" % (page))
            nbCoches = 0
            for obj in objects:
                exec("st = self.notebook.%s.ctrl_listview.GetCheckState(obj)" % (page))
                if st == True:
                    nbCoches= nbCoches + 1
                    listeCoches.append(obj.code)
            if nbCoches == 0:
                dlg = wx.MessageDialog(self, _(u"Souhaitez-vous supprimer toutes les coches de ce Tarif"), _(u"Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
                if dlg.ShowModal() == wx.ID_YES :
                   exec("self.notebook.%s.ctrl_listview.SauveDonnees(listeCoches)" % (page))
            else : exec("self.notebook.%s.ctrl_listview.SauveDonnees(listeCoches)" % (page))
            exec("self.notebook.%s.ctrl_listview.RefreshObjects(objects)" % (page))
        #fin SauveDonnees

    def OnCtrlCode(self,event) :
        #event.Skip()
        selection = self.ctrl_code.GetSelection()
        value = self.ctrl_code.GetValue().upper()
        self.ctrl_code.ChangeValue(value)
        self.ctrl_code.SetSelection(*selection)
        """
        event.Skip()
        self.notebook.AffichePage(codePage="articles")
        selection = self.ctrl_code.GetSelection()
        value = self.ctrl_code.GetValue().upper()
        self.ctrl_code.ChangeValue(value)
        self.ctrl_code.SetSelection(*selection)
        """

    def OnCtrlCodeModif(self,event) :
        self.notebook.AffichePage(codePage="articles")
        self.notebook.page1.ctrl_listview.MAJ()
        self.notebook.Refresh()
        #.ctrl_listview.InitObjectListView()

    def OnCtrlAnneeModif(self,event):
        DB = aGestionDB.DB()
        annee = str(self.ctrl_annee.Value)
        retour = DB.SetAnnee(annee)
        self.notebook.page0.ctrl_listview.MAJ()
        self.notebook.Refresh()

    def GetAnnee(self):
        DB = aGestionDB.DB()
        annee,debut,fin = DB.GetAnnee()
        self.ctrl_annee.SetValue(annee)

    def SetNomTarif(self,record):
        if record.len ==0 : return
        self.ctrl_code.SetValue(record.code)
        self.ctrl_libelle.SetValue(record.libelle)
        self.notebook.page0.MAJ()
        self.notebook.page1.MAJ()

    def GetNomTarif(self):
        record = [
            ("code", self.ctrl_code.GetValue()),
            ("libelle", self.ctrl_libelle.GetValue()),
            ]
        return record

    #fin de Dialog

# Pour lancement main
class Record(object) :
    def __init__(self, donnees):
        self.code = donnees[0]
        self.libelle = donnees[0]
        self.len  = len(donnees)

if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None,"ajout")
    record = Record(["CORSE",])
    dialog_1.SetNomTarif(record)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()