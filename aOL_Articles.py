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
import aDLG_SaisieArticles
import aDATA_Tables
from ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
import UTILS_Utilisateurs
import UTILS_Config
from UTILS_Decimal import FloatToDecimal
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", u"€")

class Track(object):
    def __init__(self, donnees):
        self.code = donnees["code"]
        self.libelle = donnees["libelle"]
        self.conditions = donnees["conditions"]
        self.calcul = donnees["calcul"]
        if donnees["prix1"]== None:
            self.prix1=0
        else: self.prix1 = donnees["prix1"]
        if donnees["prix2"]== None:
            self.prix2=0
        else: self.prix2 = donnees["prix2"]
        self.facture = donnees["facture"]
        self.compta = donnees["compta"]
        if donnees["nivActivite"]== None:
            self.nivActivite = 1
        else: self.nivActivite = donnees["nivActivite"]
        if donnees["nivFamille"]== None:
            self.nivFamille = 1
        else: self.nivFamille = donnees["nivFamille"]
        self.len = len(donnees)

class ListView(FastObjectListView):
    def __init__(self, *args, **kwds):
        self.popupIndex = -1
        self.listeFiltres = []
        # Initialisation du listCtrl
        self.selectionID = None
        self.selectionTrack = None
        FastObjectListView.__init__(self, *args, **kwds)
        self.listeOLV = []
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.nomTable = "matArticles"
        self.champCle = "artCodeArticle"
        self.listeChampsSQL = [str((a)) for a, b, c in aDATA_Tables.DB_DATA[self.nomTable]]
        self.listeChampsTrack = ["code", "libelle", "conditions", "calcul", "prix1", "prix2", "facture", "compta","nivFamille","nivActivite",]
        if len(self.listeChampsSQL) <> len(self.listeChampsTrack) :
            aGestionDB.MessageBox(self, u"Problème programmation des champs : " + self.nomTable)
            self.Destroy()

    def GetDonnees(self):
        """ Récupération des données sous forme liste de dictionnaires"""
        donnees= []
        champsSQL = ""
        for item in self.listeChampsSQL :
            champsSQL = champsSQL  + item + ", "
        self.champsSQL = champsSQL[:-2]
        DB = aGestionDB.DB()
        req =  "SELECT " + self.champsSQL + " FROM " + self.nomTable +" ORDER BY " + self.champCle+ "; "
        DB.ExecuterReq(req)
        recordset = DB.ResultatReq()
        DB.Close()
        # Transposition des données SQL avec les noms de champs utilisés en track
        for item in recordset :
            i = 0
            record = {}
            for champ in self.listeChampsTrack :
                record[champ] = item[i]
                i= i +1
            donnees.append(record)
        return donnees

    def GetTracks(self):
        #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        donnees = self.GetDonnees()
        listeListeView = []
        for item in donnees:
            track = Track(item)
            listeListeView.append(track)
            if self.selectionID == item["code"]:
                self.selectionTrack = track
        return listeListeView

    def InitObjectListView(self):
        self.listeOLV = self.GetTracks()
        def FormateMontant(montant):
            if montant == None or montant == "": return ""
            return u"%.2f %s" % (montant, SYMBOLE)
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        definitionColonnes = [
            ColumnDefn(_(u"Null"), "left", 0, 0, typeDonnee="texte"),
            ColumnDefn(_(u"Code"), "left", 80, "code", typeDonnee="texte"),
            ColumnDefn(_(u"Libelle"), 'left', 150,"libelle", typeDonnee="texte",isSpaceFilling = True),
            ColumnDefn(_(u"Conditions"), 'left', 60,"conditions", typeDonnee="texte"),
            ColumnDefn(_(u"Calcul"), 'left', 60, "calcul", typeDonnee="texte"),
            ColumnDefn(_(u"Prix_1"), 'right', 60, "prix1", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_(u"Prix_2"), 'right', 60, "prix2", typeDonnee="montant", stringConverter=FormateMontant),
            ColumnDefn(_(u"Facture"), 'left',60, "facture", typeDonnee="texte"),
            ColumnDefn(_(u"Compta"), 'left',60, "compta", typeDonnee="texte"),
            ColumnDefn(_(u"Fam"), 'left',40, "nivFamille", typeDonnee="integer"),
            ColumnDefn(_(u"Act"), 'left',30, "nivActivite", typeDonnee="integer"),
            ]
        self.SetColumns(definitionColonnes)
        self.SetEmptyListMsg(_(u"Aucun article défini"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, face="Tekton"))
        self.SetSortColumn(self.columns[0])
        self.SetObjects(self.listeOLV)

    def OnItemActivated(self,event):
        self.Modifier(None)

    def MAJ(self, ID=None):
         self.InitObjectListView()

    def Selection(self):
        return self.GetSelectedObjects()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.Selection()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.Selection()[0].Code
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

    def SaisieArticle(self, selection, mode):
        articleNomsSQL = []
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "creer") == False :
            aGestionDB.MessageBox(self,u"Vous n'avez pas les droits de paramétrage des  activités")
        else :
            dlg = aDLG_SaisieArticles.Dialog(self,mode)
            if mode <> "ajout" :
                dlg.SetArticle(selection[0])
            else: dlg.CreeArticle()
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
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = ListView(panel, id=-1, name="OL_test", style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.myOlv.MAJ() 
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
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
