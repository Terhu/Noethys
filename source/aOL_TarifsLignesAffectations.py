#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, Jacques Brunel
# Gestion de la table matTarifs définissant les affectation des tarifs aux camps
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import aGestionDB
import aDATA_Tables
from ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils
import UTILS_Utilisateurs

class Track(object):
    def __init__(self, donnees):
        # "IDactivite", "IDgroupe", "IDcategorie_tarif","activite", "groupe", "categorie", "classeAge","dateFin"
        self.IDactivite = donnees["IDactivite"]
        self.IDgroupe = donnees["IDgroupe"]
        self.IDcategorie_tarif = donnees["IDcategorie_tarif"]
        self.activite = donnees["activite"]
        self.groupe = donnees["groupe"]
        self.categorie = donnees["categorie"]
        self.classeAge = donnees["classeAge"]
        self.dateFin = donnees["dateFin"]
        self.code = (self.IDactivite,self.IDgroupe,self.IDcategorie_tarif)
        self.tarif = donnees["tarif"]
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
        #self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.nomTable = "matTarifs"
        self.listeChampsTrack = ["IDactivite", "IDgroupe", "IDcategorie_tarif","activite", "groupe", "categorie", "classeAge","dateFin","tarif"]
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
            ColumnDefn(_(u"Activité"), "left", 200, "activite", typeDonnee="texte"),
            ColumnDefn(_(u"Groupe"), 'left', 150,"groupe", typeDonnee="texte"),
            ColumnDefn(_(u"Catégorie"), 'left', 100,"categorie", typeDonnee="texte"),
            ColumnDefn(_(u"ClasseAge"), 'left', 80,"classeAge", typeDonnee="texte"),
            ColumnDefn(_(u"DateFinCamp"), 'left', 80,"dateFin", typeDonnee="texte"),
            ColumnDefn(_(u"TarifAffecté"), 'left', 100, "tarif", typeDonnee="texte",isSpaceFilling = True),
            ]
        self.SetColumns(definitionColonnes)
        self.SetEmptyListMsg(_(u"Aucune affectation à définir"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, face="Tekton"))
        self.SetSortColumn(self.columns[0])
        self.CreateCheckStateColumn()
        #coche les camps dans Tarifs
        objects = self.listeOLV
        for track in objects :
            self.SetCheckState(track, False)
            if track.tarif == self.parent.ctrl_code.GetValue():
                    self.SetCheckState(track, True)
        self.SetObjects(self.listeOLV)
        self.SortBy(0, ascending=False)
        #fin InitObjectListView

    def AppelDonnees(self):
        """ Récupération des données sous forme liste de dictionnaires"""
        donnees= []
        DB = aGestionDB.DB()
        retour = DB.GetAnnee()
        debut = str(retour[1])
        fin = str(retour[2])
        if len(debut + fin) <> 20 :
            debut = "2016-01-01"
            fin = "2016-12_31"
        req = """SELECT activites.IDactivite, groupes.IDgroupe, categories_tarifs.IDcategorie_tarif, activites.nom, groupes.nom, categories_tarifs.nom, groupes.abrege, activites.date_fin
                FROM (activites INNER JOIN groupes ON activites.IDactivite = groupes.IDactivite)
                INNER JOIN categories_tarifs ON activites.IDactivite = categories_tarifs.IDactivite
                WHERE ((activites.date_fin) > '""" + debut +"""' ) AND ((activites.date_fin) <= '""" + fin +"""')
                ORDER BY activites.date_fin DESC;
                """
        retour = DB.ExecuterReq(req)
        if retour <> "ok" : DB.AfficheErr(self,retour)
        recordset = DB.ResultatReq()

        # Transposition des données SQL avec les noms de champs utilisés en track et complement
        for item in recordset :
            #ajout du tarif s'il existe dans matTarifs
            condition = "trfIDActivite = %d AND trfIDGroupe = %d AND trfIDCategorieTarif = %d ;" % (item[0],item[1],item[2])
            DB.ReqSelect("matTarifs",condition,MsgBox=True)
            recordsetTarif = DB.ResultatReq()
            if len(recordsetTarif)>0:
                item += (recordsetTarif[0][3],)
            else : item += ("-",)
            i = 0
            record = {}
            for champ in self.listeChampsTrack :
                record[champ] = item[i]
                i=i+1
            donnees.append(record)
        #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        listeListeView = []
        for item in donnees:
            track = Track(item)
            listeListeView.append(track)
        DB.Close()
        return listeListeView
        #fin AppelDonnees
    
    def SauveDonnees(self,listeCoches):
        tarif = str(self.parent.ctrl_code.GetValue())
        if len(tarif) > 0 :
            DB = aGestionDB.DB()
            req =  "DELETE FROM matTarifs WHERE (matTarifs.trfCodeTarif= '"+ tarif +"');"
            retour = DB.ExecuterReq(req)
            if retour == "ok" : DB.Commit()
            else : DB.AfficheErr(self,retour)
            if len(listeCoches) <> 0 :
                i=0
                for activite, groupe, categorie in listeCoches :
                    i=i+1
                    conditions= "trfIDactivite = %s AND trfIDgroupe = %s AND trfIDcategorieTarif= %s;" % (activite, groupe, categorie)
                    retour = DB.ReqSelect("matTarifs",conditions)
                    listeDonnees = []
                    if retour == "ok" :
                        DB.Commit()
                        listeDonnees = DB.ResultatReq()
                    else: DB.AfficheErr(self,retour)
                    if len(listeDonnees)>0:
                        camp = "Activite: "+ DB.GetNomActivite(activite)+ " - Groupe: "+ DB.GetNomGroupe(groupe)+ " - Categorie: "+ DB.GetNomCategorieTarif(categorie)
                        aGestionDB.MessageBox(self,u"Un seul tarif possible, par item activité_groupe_categorie !\n %s ! \nClé présente dans le tarif %s " % (camp, listeDonnees[0][3]), titre = u"Conflit de paramétres" )
                    else:
                        listeDonnees=[("trfIDactivite",activite),("trfIDgroupe",groupe),("trfIDcategorieTarif",categorie),("trfCodeTarif", tarif) ]
                        retour = DB.ReqInsert("matTarifs",listeDonnees)
                        if retour == "ok" : DB.Commit()
                        else : DB.AfficheErr(self,retour + u"\n" + str(listeDonnees))
            DB.Close()

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
