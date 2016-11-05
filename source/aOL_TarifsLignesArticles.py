#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, Jacques Brunel
# Gestion de la table Articles définissant le regroupement des lignes
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import aGestionDB
import aDLG_Articles
import aDLG_SaisieArticles
import aDATA_Tables
from ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
import UTILS_Utilisateurs
import UTILS_Config
from UTILS_Decimal import FloatToDecimal
#SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", u"€")

class Track(object):
    def __init__(self, donnees):
        self.code = donnees["code"]
        self.libelle = donnees["libelle"]
        self.conditions = donnees["conditions"]
        self.calcul = donnees["calcul"]
        self.prix1 = donnees["prix1"]
        self.prix2 = donnees["prix2"]
        self.facture = donnees["facture"]
        self.compta = donnees["compta"]
        if donnees["nivActivite"]== None:
            self.nivActivite = 1
        else: self.nivActivite = donnees["nivActivite"]
        if donnees["nivFamille"]== None:
            self.nivFamille = 1
        else: self.nivFamille = donnees["nivFamille"]
        self.preCoche = False
        self.len = len(donnees)

class ListView(FastObjectListView):
    def __init__(self,parent,*args, **kwds):
        self.parent = parent
        self.popupIndex = -1
        self.listeFiltres = []
        # Initialisation du listCtrl
        self.selectionID = None
        self.selectionTrack = None
        FastObjectListView.__init__(self,parent, *args, **kwds)
        self.listeOLV = []
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.nomTable = "matArticles"
        self.champCle = "artCodeArticle"
        self.condition = " WHERE artNiveauActivite = 1 OR artNiveauActivite ISNULL "
        self.listeChampsSQL = [str((a)) for a, b, c in aDATA_Tables.DB_DATA[self.nomTable]]
        self.listeChampsTrack = ["code", "libelle", "conditions", "calcul", "prix1", "prix2", "facture", "compta","nivFamille","nivActivite",]
        if len(self.listeChampsSQL) <> len(self.listeChampsTrack) :
            aGestionDB.MessageBox(self, u"Problème programmation des champs : " + self.nomTable)
            self.Destroy()
        self.InitObjectListView()
        #fin _init

    def InitObjectListView(self):
        self.listeOLV = self.AppelDonnees()
        def FormateMontant(montant):
            if montant == None or montant == "": return ""
            return u"%.2f " % (montant)
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        definitionColonnes = [
            ColumnDefn(u"pré Coché", 'left',20, "preCoche", checkStateGetter="preCoche"),
            ColumnDefn(_(u"Code"), "left", 80, "code", typeDonnee="texte"),
            ColumnDefn(_(u"Libelle"), 'left', 150,"libelle", typeDonnee="texte",isSpaceFilling = True),
            ColumnDefn(_(u"Conditions"), 'left', 60,"conditions", typeDonnee="texte"),
            ColumnDefn(_(u"Calcul"), 'left', 60, "calcul", typeDonnee="texte"),
            ColumnDefn(_(u"Prix_1"), 'right', 60, "prix1", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_(u"Prix_2"), 'right', 60, "prix2", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_(u"Facture"), 'left',50, "facture", typeDonnee="texte"),
            ColumnDefn(_(u"Compta"), 'left',50, "compta", typeDonnee="texte"),
            ColumnDefn(_(u"Act"), 'left',30, "nivActivite",typeDonnee="integer"),
            ColumnDefn(_(u"Fam"), 'left',40, "nivFamille", typeDonnee="integer"),
            ]
        self.SetColumns(definitionColonnes)
        self.SetEmptyListMsg(_(u"Aucun article défini"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, face="Tekton"))
        self.SetSortColumn(self.columns[0])
        #self.CreateCheckStateColumn(3)
        self.CreateCheckStateColumn(0)

        #coche les articles dans TarifLignes
        objects = self.listeOLV
        for track in objects :
            self.SetCheckState(track, False)
            for ligne,preCoche in self.listeTarifLignes:
                if ligne == track.code :
                    self.SetCheckState(track, True)
                    if preCoche == "1": track.preCoche = True
        self.SetObjects(self.listeOLV)
        self.SortBy(0, ascending=False)
        #fin InitObjectListView

    def AppelDonnees(self):
        """ Récupération des données sous forme liste de dictionnaires"""
        donnees= []
        champsSQL = ""
        for item in self.listeChampsSQL :
            champsSQL = champsSQL  + item + ", "
        self.champsSQL = champsSQL[:-2]
        DB = aGestionDB.DB()
        #+ " WHERE (Left([artCodeArticle],1)<>'*') "
        req =  "SELECT " + self.champsSQL + " FROM " + self.nomTable + self.condition +" ORDER BY " + self.champCle+ "; "
        retour = DB.ExecuterReq(req)
        if retour <> "ok" : DB.AfficheErr(self,retour)

        recordset = DB.ResultatReq()
        DB.Close()
        # Transposition des données SQL avec les noms de champs utilisés en track
        for item in recordset :
            i = 0
            if item[i][0] <> "*" :
                record = {}
                for champ in self.listeChampsTrack :
                    record[champ] = item[i]
                    i= i +1
                donnees.append(record)
        #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        listeListeView = []
        for item in donnees:
            track = Track(item)
            listeListeView.append(track)
            if self.selectionID == item["code"]:
                self.selectionTrack = track
        #Recherche des lignes articles retenues dans le tarif pour les cocher
        self.listeTarifLignes = []
        req =  "SELECT matTarifsLignes.trlCodeArticle,matTarifsLignes.trlPreCoche FROM matTarifsLignes WHERE (matTarifsLignes.trlCodeTarif= '"+ self.parent.ctrl_code.GetValue() +"');"
        DB = aGestionDB.DB()
        DB.ExecuterReq(req)
        if retour <> "ok" : DB.AfficheErr(self,retour)

        recordsetLignes = DB.ResultatReq()
        DB.Close()
        for item in recordsetLignes :
            self.listeTarifLignes.append((str(item[0]),str(item[1])))
        return listeListeView
        #fin AppelDonnees
    
    def SauveDonnees(self,listeCoches):
        tarif = str(self.parent.ctrl_code.GetValue())
        if len(tarif) > 0 :
            DB = aGestionDB.DB()
            req =  "DELETE FROM matTarifsLignes WHERE (matTarifsLignes.trlCodeTarif= '"+ tarif +"');"
            retour = DB.ExecuterReq(req)
            if retour == "ok" : DB.Commit()
            else : DB.AfficheErr(self,retour)
            if len(listeCoches) <> 0 :
                i=0
                for code in listeCoches :
                    objects = self.GetObjects()
                    preCoche=0
                    for obj in objects:
                        if obj.code == code:
                            if obj.preCoche == True:
                                preCoche = 1
                    i=i+1
                    listeDonnees=[("trlCodeTarif", tarif), ("trlNoLigne", i), ("trlCodeArticle", code),("trlPreCoche",preCoche)]
                    retour = DB.ReqInsert("matTarifsLignes",listeDonnees)
                    if retour == "ok" : DB.Commit()
                    else : DB.AfficheErr(self,retour)
            DB.Close()

    def OnItemActivated(self,event):
        self.Modifier(None)

    def MAJ(self, ID=None):
         self.InitObjectListView()

    #Menu contextuel
    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            #ID = self.Selection()[0].Code
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Ajouter
        item = wx.MenuItem(menuPop, 10, _(u"Ajouter"))
        bmp = wx.Bitmap("Images/16x16/Ajouter.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)
        
        menuPop.AppendSeparator()

        # Item Modifier
        item = wx.MenuItem(menuPop, 20, _(u"Modifier"))
        bmp = wx.Bitmap("Images/16x16/Modifier.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Modifier, id=20)
        if noSelection == True : item.Enable(False)
        
        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _(u"Supprimer"))
        bmp = wx.Bitmap("Images/16x16/Supprimer.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if noSelection == True : item.Enable(False)
                
        menuPop.AppendSeparator()
    
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 40, _(u"Aperçu avant impression"))
        bmp = wx.Bitmap("Images/16x16/Apercu.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=40)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 50, _(u"Imprimer"))
        bmp = wx.Bitmap("Images/16x16/Imprimante.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=50)
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_(u"Liste des articles"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_(u"Liste des articles"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    #Gestion des lignes
    def SaisieArticle(self, selection, mode):
        articleNomsSQL = []
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "creer") == False :
            aGestionDB.MessageBox(self,u"Vous n'avez pas les droits de paramétrage des  activités")
        else :
            dlg = aDLG_SaisieArticles.Dialog(self,mode)
            if mode == "ajout" :
                dlg.CreeArticle()
            else :
                dlg.SetArticle(selection[0])
            if dlg.ShowModal() == wx.ID_OK:
                articleTrack = dlg.GetArticle()
                for i in range(len(articleTrack)) :
                    articleNomsSQL.append((self.listeChampsSQL[self.listeChampsTrack.index(articleTrack[i][0])],articleTrack[i][1]))
            dlg.Destroy()
        return articleNomsSQL

    def Ajouter(self, event):
        article = self.SaisieArticle(None,"ajout")
        if len(article) == 0 :return
        DB = aGestionDB.DB()
        retour = DB.ReqInsert(self.nomTable, article)
        DB.Close()
        if retour == "ok" :
            self.MAJ()
        else :
            aGestionDB.MessageBox(self,retour)

    def Modifier(self, event):
        if len(self.Selection()) == 0 :
            aGestionDB.MessageBox(self, u"Vous n'avez sélectionné aucun article dans la liste")
            return
        index = self.SelectedItemCount
        article = self.SaisieArticle(self.Selection(),"modif")
        if len(article) == 0 :return
        DB = aGestionDB.DB()
        retour = DB.ReqMAJ( self.nomTable, article, self.champCle, article[0][1],IDestChaine=True)
        DB.Close()
        #self.SetSelection(index)
        if retour == "ok" :
            self.MAJ()
        else :
            aGestionDB.MessageBox(self,retour)

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _(u"Vous n'avez sélectionné aucun article dans la liste"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        # Vérifie que ce type de article n'a pas déjà été utilisé
        DB = aGestionDB.DB()
        req ="""SELECT COUNT (trlCodeArticle)
                FROM matTarifsLignes
                WHERE trlCodeArticle = %s
              """  %track.code
        DB.ExecuterReq(req)
        resultat = DB.ResultatReq()
        if resultat <> [] :
            nbreArticles = len(resultat)
            dlg = wx.MessageDialog(self, _(u"Ce Bloc a déjà été attribué %d fois.\n\nVous ne pouvez donc pas le supprimer !") % nbreArticles, _(u"Suppression impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        DB.Close()
        # Confirmation de suppression
        dlg = wx.MessageDialog(self, _(u"Souhaitez-vous vraiment supprimer cet article ?"), _(u"Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            DB = aGestionDB.DB()
            retour = DB.ReqDEL(self.nomTable, self.champCle, track.code )
            DB.Close()
            if retour == "ok" :
                self.MAJ()
            else :
                dlgErr = wx.MessageDialog(self,retour)
                dlgErr.ShowModal()
                dlgErr.Destroy()
            self.MAJ()
        dlg.Destroy()
    #fin ListView

# -------------------------------------------------------------------------------------------------------------------------------------------
class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_(u"Rechercher un Bloc..."))
        self.ShowSearchButton(True)
        
        self.listView = self.parent.ctrl_listview
        nbreColonnes = self.listView.GetColumnCount()
        self.listView.SetFilter(Filter.TextSearch(self.listView, self.listView.columns[0:nbreColonnes]))
        
        self.SetCancelBitmap(wx.Bitmap("Images/16x16/Interdit.png", wx.BITMAP_TYPE_PNG))
        self.SetSearchBitmap(wx.Bitmap("Images/16x16/Loupe.png", wx.BITMAP_TYPE_PNG))
        
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, evt):
        self.Recherche()
            
    def OnCancel(self, evt):
        self.SetValue("")
        self.Recherche()

    def OnDoSearch(self, evt):
        self.Recherche()
        
    def Recherche(self):
        txtSearch = self.GetValue()
        self.ShowCancelButton(len(txtSearch))
        self.listView.GetFilter().SetText(txtSearch)
        self.listView.RepopulateList()
        self.Refresh() 


# -------------------------------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        panel.ctrl_code = wx.TextCtrl(self, -1, "Param Main",size=(200,20))
        panel.ctrl_code.SetValue("P1;11-13")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(panel.ctrl_code, 0, wx.ALL,4)
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
