#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, Jacques Brunel
# Gestion de la table TarifsNoms définissant les noms des différents tarifs
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import aGestionDB
import aDLG_TarifsLignes
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
        self.nbLignes = donnees["nbLignes"]
        self.nbActivites = donnees["nbActivites"]
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
        self.nomTable = "matTarifsNoms"
        self.champCle = "trnCodeTarif"
        self.listeChampsSQL = [str((a)) for a, b, c in aDATA_Tables.DB_DATA[self.nomTable]]
        self.listeChampsTrack = ["code", "libelle","nbLignes"]
        if len(self.listeChampsSQL) <> len(self.listeChampsSQL) :
            aGestionDB.MessageBox(self, u"Problème programmation des champs : " + self.nomTable)
            self.Destroy()

    def GetDonnees(self):
        """ Récupération des données sous forme liste de dictionnaires"""
        donnees= []
        champsSQL = ""
        for item in self.listeChampsSQL :
            champsSQL = champsSQL  + item + ", "
        champsSQL = champsSQL + ""
        self.champsSQL = champsSQL[:-2]
        DB = aGestionDB.DB()
        req =   """
                SELECT matTarifsNoms.trnCodeTarif, matTarifsNoms.trnLibelle, Count(matTarifsLignes.trlNoLigne) AS CompteDetrlNoLigne
                FROM matTarifsNoms LEFT JOIN matTarifsLignes ON matTarifsNoms.trnCodeTarif = matTarifsLignes.trlCodeTarif
                GROUP BY matTarifsNoms.trnCodeTarif, matTarifsNoms.trnLibelle;
                """
        retour = DB.ExecuterReq(req)
        if retour <> "ok" : DB.AfficheErr(self,retour)
        recordset = DB.ResultatReq()
        req =   """
                SELECT matTarifsNoms.trnCodeTarif, matTarifsNoms.trnLibelle, Count(matTarifs.trfIDcategorieTarif) AS CompteDetrfIDcategorieTarif
                FROM matTarifsNoms LEFT JOIN matTarifs ON matTarifsNoms.trnCodeTarif = matTarifs.trfCodeTarif
                GROUP BY matTarifsNoms.trnCodeTarif, matTarifsNoms.trnLibelle;
                """
        retour = DB.ExecuterReq(req)
        if retour <> "ok" : DB.AfficheErr(self,retour)
        recordset2 = DB.ResultatReq()
        DB.Close()
        # Transposition des données SQL avec les noms de champs utilisés en track
        for item in recordset :
            i = 0
            record = {}
            for champ in self.listeChampsTrack :
                record[champ] = item[i]
                i= i +1
            for item2 in recordset2 :
                if item2[0] == item[0]:
                    record["nbActivites"] = item2[2]
            donnees.append(record)
        #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        listeListeView = []
        for item in donnees:
            track = Track(item)
            listeListeView.append(track)
            if self.selectionID == item["code"]:
                self.selectionTrack = track
        return listeListeView

    def InitObjectListView(self):
        self.listeOLV = self.GetDonnees()
        def FormateEntier(entier):
            if entier == None or entier == "": return ""
            return u"%.2f" % (entier)
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        definitionColonnes = [
            ColumnDefn(_(u"Null"), "left", 0, 0, typeDonnee="texte"),
            ColumnDefn(_(u"Code"), "left", 80, "code", typeDonnee="texte"),
            ColumnDefn(_(u"Libelle"), 'left', 350,"libelle", typeDonnee="texte",isSpaceFilling = True),
            ColumnDefn(_(u"NbActivites"), 'right', 70, "nbActivites", typeDonnee="entier", stringConverter=FormateEntier),
            ColumnDefn(_(u"NbLignes"), 'right', 70, "nbLignes", typeDonnee="entier", stringConverter=FormateEntier),
            ]
        self.SetColumns(definitionColonnes)
        self.SetEmptyListMsg(_(u"Aucun nom défini"))
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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_(u"Liste des noms de tarifs"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_(u"Liste des noms de tarifs"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def SaisieNom(self, selection, mode):
        nomNomsSQL = []
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "creer") == False :
            aGestionDB.MessageBox(self,u"Vous n'avez pas les droits de paramétrage des  activités")
        else :
            dlg = aDLG_TarifsLignes.Dialog(self,mode)
            if mode == "modif" :
                dlg.SetNomTarif(selection[0])
            if dlg.ShowModal() == wx.ID_OK:
                nomTrack = dlg.GetNomTarif()
                for i in range(len(nomTrack)) :
                    nomNomsSQL.append((self.listeChampsSQL[self.listeChampsTrack.index(nomTrack[i][0])],nomTrack[i][1]))
            dlg.Destroy()
        return nomNomsSQL

    def Ajouter(self, event):
        nom = self.SaisieNom(None,"ajout")
        if len(nom) == 0 :return
        DB = aGestionDB.DB()
        retour = DB.ReqInsert(self.nomTable, nom)
        DB.Close()
        if retour == "ok" :
            self.MAJ()
        else :
            aGestionDB.MessageBox(self,retour)

    def Modifier(self, event):
        if len(self.Selection()) == 0 :
            aGestionDB.MessageBox(self, u"Vous n'avez sélectionné aucun tarif dans la liste")
            return
        index = self.SelectedItemCount
        nom = self.SaisieNom(self.Selection(),"modif")
        if len(nom) == 0 :return
        DB = aGestionDB.DB()
        retour = DB.ReqMAJ( self.nomTable, nom, self.champCle, nom[0][1],True)
        DB.Close()
        #self.SetSelection(index)
        if retour == "ok" :
            self.MAJ()
        else :
            aGestionDB.MessageBox(self,retour)

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _(u"Vous n'avez sélectionné aucun tarif dans la liste"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        track = self.Selection()[0]
        # Vérifie que ce type de nom de tarif n'a pas déjà été utilisé
        DB = aGestionDB.DB()
        req ="""SELECT COUNT (trlCodeTarif)
                FROM matTarifsLignes
                WHERE trlCodeTarif = '%s'
              """  %track.code
        DB.ExecuterReq(req,MsgBox = True)
        resultat = DB.ResultatReq()

        if resultat <> [] :
            nbreNoms = resultat[0][0]
            dlg = wx.MessageDialog(self, _(u"Ce Tarif a %d ligne(s) attribuée(s).\n\nIl faut d'abord supprimer les lignes associées !") % nbreNoms, _(u"Suppression impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        DB.Close()
        # Confirmation de suppression
        dlg = wx.MessageDialog(self, _(u"Souhaitez-vous vraiment supprimer ce Tarif ?"), _(u"Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
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
#fin listview

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
