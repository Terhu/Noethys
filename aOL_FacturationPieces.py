#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, Jacques Brunel
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
# Derive de OL_Prestations.py
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import aGestionDB
import aGestionInscription
import aDATA_Tables
import datetime
import copy
import UTILS_Config
import UTILS_Utilisateurs
from UTILS_Decimal import FloatToDecimal as FloatToDecimal
from ObjectListView import GroupListView, ColumnDefn, Filter, CTRL_Outils, PanelAvecFooter

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", u"€")

def DateEngFr(textDate):
    text = str(textDate[8:10]) + u"/" + str(textDate[5:7]) + u"/" + str(textDate[:4])
    return text

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    listeJours = (_(u"Lundi"), _(u"Mardi"), _(u"Mercredi"), _(u"Jeudi"), _(u"Vendredi"), _(u"Samedi"), _(u"Dimanche"))
    listeMois = (_(u"janvier"), _(u"février"), _(u"mars"), _(u"avril"), _(u"mai"), _(u"juin"), _(u"juillet"), _(u"août"), _(u"septembre"), _(u"octobre"), _(u"novembre"), _(u"décembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def ContractNom(individu,longueur):
    if len(individu) > longueur :
        decoupe = individu.split(' ')
        nb = int(longueur/len(decoupe))+1
        individu = ""
        for item in decoupe:
            if len(item) > nb:
                sep = "."
            else: sep = " "
            individu = individu + item[:nb] + sep
    return individu

def OlvToDict(self,listeChamps,track):
        # Transforme une ligne Olv (Track) en dictionnaire
        dictDonnees = {}
        for champ in listeChamps:
            dictDonnees["%s" %champ] = track.__dict__["%s" % champ]
        return dictDonnees

# ---------------------------------------- LISTVIEW DATES -----------------------------------------------------------------------

class Track(object):
    def __init__(self, track):
        self.__dict__ = copy.deepcopy(track)


class ListView(GroupListView):
    def __init__(self, parent, *args, **kwds):
        self.IDpayeur =  kwds.pop("IDpayeur", None)
        factures_parent =  kwds.pop("factures_parent", None)
        self.factures = factures_parent[0]
        self.parent = factures_parent[1]
        GroupListView.__init__(self, parent, *args, **kwds)
        self.fgest = aGestionInscription.Forfaits(self)
        self.selectionID = None
        self.selectionTrack = None
        self.listeFactures = []
        self.listeIDprestation = []
        self.total = 0.0
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.SetShowGroups(False)
        self.donnees = self.GetListePieces(IDpayeur=self.IDpayeur)
        self.InitObjectListView()
        self.CocheTout()
        self.Coherence()

    def InitObjectListView(self):
        # ImageList
        self.imgVert = self.AddNamedImages("vert", wx.Bitmap("Images/16x16/Ventilation_vert.png", wx.BITMAP_TYPE_PNG))
        self.imgRouge = self.AddNamedImages("rouge", wx.Bitmap("Images/16x16/Ventilation_rouge.png", wx.BITMAP_TYPE_PNG))
        self.imgOrange = self.AddNamedImages("orange", wx.Bitmap("Images/16x16/Ventilation_orange.png", wx.BITMAP_TYPE_PNG))

        def GetImageVentilation(track):
            if track.montant == track.mttRegle :
                return self.imgVert
            if track.mttRegle == FloatToDecimal(0.0) or track.mttRegle == None :
                return self.imgRouge
            if track.mttRegle < track.montant :
                return self.imgOrange
            return self.imgRouge

        def FormateDate(dateDD):
            return DateEngFr(str(dateDD))

        def FormateMontant(montant):
            if montant == None or montant == "" : return ""
            return u"%.2f %s" % (montant, SYMBOLE)

        # Couleur en alternance des lignes
        self.oddRowsBackColor = wx.Colour(255, 255, 255) #"#EEF4FB" # Bleu
        self.evenRowsBackColor = "#F0FBED" # Vert

        # Paramètres ListView
        self.useExpansionColumn = True
        listeColonnes = ["IDnumPiece", "dateCreation", "payeur", "famille", "activite", "label", "montant", "mttRegle", "noFacture", "utilisateurModif"]
        if self.factures:
            libNoFact = u"N° Facture"
            valNoFact = "noFacture"
        else:
            libNoFact = u"Piece"
            valNoFact = "nature"

        dictColonnes = {
            "IDnumPiece" : ColumnDefn(_(u""), "left", 0, "IDnumPiece", typeDonnee="integer", stringConverter=FormateDate),
            "dateCreation" : ColumnDefn(_(u"Date"), "left", 90, "dateCreation", typeDonnee="date", stringConverter=FormateDate),
            "payeur" : ColumnDefn(_(u"Payeur"), "left", 100, "payeur", typeDonnee="texte"),
            "famille" : ColumnDefn(_(u"Famille "), "left", 100, "famille", typeDonnee="texte"),
            "activite" : ColumnDefn(_(u"Activité"), "left", 60, "activite", typeDonnee="texte"),
            "label" : ColumnDefn(_(u"Ref. Inscription"), "left", 200, "label", typeDonnee="texte",isSpaceFilling = True),
            "montant" : ColumnDefn(_(u"Montant"), "right", 90, "montant", typeDonnee="montant", stringConverter=FormateMontant),
            "mttRegle" : ColumnDefn(_(u"Réglé"), "right", 90, "mttRegle", typeDonnee="montant", stringConverter=FormateMontant, imageGetter=GetImageVentilation),
            "noFacture" : ColumnDefn(_(libNoFact), "left", 60, valNoFact, typeDonnee="integer"),
            "utilisateurModif" : ColumnDefn(_(u"User"), "left", 50, "utilisateurModif", typeDonnee="texte"),
        }

        self.SetColumns([dictColonnes[code] for code in listeColonnes])
        self.CreateCheckStateColumn()
        self.SetShowItemCounts(False)
        #self.SetSortColumn(self.columns[6]) ne pas trier ici pour gérer ensuie le monter et descendre
        if self.factures:
            self.SetEmptyListMsg(_(u"Aucune facture"))
        else : self.SetEmptyListMsg(_(u"Aucune piece non facturée"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, face="Tekton"))
        self.SetObjects(self.donnees)

    def GetListePieces(self, IDpayeur=1):
        # Initialisation du listCtrl
        if self.factures:
            conditions = "matPieces.pieIDcompte_payeur = %s AND matPieces.pieNoFacture is not null " % IDpayeur
        else:
            conditions = "matPieces.pieIDcompte_payeur = %s AND matPieces.pieNoFacture is null " % IDpayeur

        # Composition des champs
        dicoDB = aDATA_Tables.DB_DATA
        listeChamps = []
        champsReq =""
        for descr in dicoDB["matPieces"]:
            if descr[1] != "blob" :
                nomChamp = descr[0]
                listeChamps.append(nomChamp)
                champsReq = champsReq + nomChamp + ","

        self.champsPieceReq = copy.deepcopy(champsReq)
        self.listeChampsPiece = copy.deepcopy(listeChamps)
        listeChampsAutres = ["activite","label","montant","mttPrest","mttRegle"]
        champsAutresReq = "activites.abrege AS activite,prestations.label, Sum(matPiecesLignes.ligMontant) AS mttLignes, prestations.montant AS mttPrest"
        champsReq = champsReq + champsAutresReq
        self.listeChamps = self.listeChampsPiece + listeChampsAutres
        #récupération des règlements
        req = """
        SELECT matPieces.pieIDnumPiece, Sum(ventilation.montant) AS mttRegle
        FROM matPieces LEFT JOIN ventilation ON (matPieces.pieIDcompte_payeur = ventilation.IDcompte_payeur) AND (matPieces.pieIDprestation = ventilation.IDprestation)
        WHERE %s
        GROUP BY matPieces.pieIDnumPiece
        ORDER BY matPieces.pieIDnumPiece;
        """ % (conditions)
        DB = aGestionDB.DB()
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            aGestionDB.MessageBox(self,retour)
            return None
        listeReglements = DB.ResultatReq()
        #récupération des autres éléments des pièces
        req = """
        SELECT %s
        FROM matPieces
                LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece
                LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
                LEFT JOIN prestations ON (matPieces.pieIDcompte_payeur = prestations.IDcompte_payeur) AND (matPieces.pieIDprestation = prestations.IDprestation)
        WHERE %s
        GROUP BY %s
        ORDER BY matPieces.pieIDnumPiece;
        """ % (champsReq, conditions, self.champsPieceReq[:-1])
        DB = aGestionDB.DB()
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            aGestionDB.MessageBox(self,retour)
            return None
        # ajout des règlements aux données
        listeDonnees = []
        i = 0
        for record in DB.ResultatReq():
            if listeReglements[i][1] == None:
                regle = 0.00
            else : regle = listeReglements[i][1]
            donnee = []
            for item in record:
                donnee.append(item)
            donnee.append(regle)
            listeDonnees.append(donnee)
            i+= 1
        self.nbPieces = len(listeDonnees)
        if self.nbPieces == 0 :
            return None

        # composition des tracks
        listeOLV=[]
        self.listeIDprestation=[]
        for record in listeDonnees:
            dictDonnees = self.fgest.DictTrack(self.listeChamps,record)
            ligne = Track(dictDonnees)
            if ligne.montant == None : ligne.montant = 0
            if ligne.prixTranspAller != None:
                ligne.montant += ligne.prixTranspAller
            if ligne.prixTranspRetour != None:
                ligne.montant += ligne.prixTranspRetour
            ligne.payeur= DB.GetNomIndividu(ligne.IDcompte_payeur,first = "nom")
            ligne.famille= DB.GetNomIndividu(ligne.IDfamille,first = "prenom")
            individu= ContractNom(DB.GetNomIndividu(ligne.IDindividu),16)
            activite = " - " + str(DB.GetNomActivite(ligne.IDactivite)).split('-')[0]
            groupe = (" - " + str(DB.GetNomGroupe(ligne.IDgroupe)))
            if not (ligne.IDindividu * ligne.IDactivite == 0):
                ligne.label= individu + activite + groupe
            listeOLV.append(ligne)
            if ligne.IDprestation != None:
                self.listeIDprestation.append(ligne.IDprestation)
        DB.Close()
        return listeOLV

    def Coherence(self):
        # teste la cohérence lors du passage en non facturé
        if self.factures:
            return
        fGest = aGestionInscription.Forfaits(self)
        coherent = fGest.CoherenceOrphelines(self.IDpayeur)
        if not coherent:
            self.parent.rw = False
        coherent = fGest.CoherenceVeuves(self.IDpayeur)
        if not coherent:
            self.parent.rw = False

    def MAJ(self, ID=None):
        """
        if ID != None :
            self.selectionID = ID
            self.selectionTrack = None
        else:
            self.selectionTrack = None
        # Sélection d'un item
        if self.selectionTrack != None :
            self.SelectObject(self.selectionTrack, deselectOthers=True, ensureVisible=True)
        self.selectionID = None
        self.selectionTrack = None
        if ID == None :
            self.DefileDernier()
        """
        self.Refresh()

    def OnContextMenu(self, event):
        """Ouverture du menu contextuel """
        if len(self.GetSelectedObjects()) > 0 :
            ID = self.GetSelectedObjects()[0].IDprestation
        
        # Création du menu contextuel
        menuPop = wx.Menu()

        # Item Monter
        if self.IDpayeur != None :
            item = wx.MenuItem(menuPop, 10, _(u"Monter"))
            bmp = wx.Bitmap("Images/16x16/Fleche_haut.png", wx.BITMAP_TYPE_PNG)
            item.SetBitmap(bmp)
            menuPop.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.Monter, id=10)

        # Item Descendre
        item = wx.MenuItem(menuPop, 20, _(u"Descendre"))
        bmp = wx.Bitmap("Images/16x16/Fleche_bas.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Descendre, id=20)
        if len(self.GetSelectedObjects()) == 0 : item.Enable(False)

        # Item Supprimer
        item = wx.MenuItem(menuPop, 30, _(u"Supprimer"))
        bmp = wx.Bitmap("Images/16x16/Supprimer.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=30)
        if len(self.GetSelectedObjects()) == 0 : item.Enable(False)
        
        menuPop.AppendSeparator()

        # Item Tout cocher
        item = wx.MenuItem(menuPop, 70, _(u"Tout cocher"))
        bmp = wx.Bitmap("Images/16x16/Cocher.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.CocheTout, id=70)

        # Item Tout décocher
        item = wx.MenuItem(menuPop, 80, _(u"Tout décocher"))
        bmp = wx.Bitmap("Images/16x16/Decocher.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.CocheRien, id=80)

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
        
        menuPop.AppendSeparator()
    
        # Item Export Texte
        item = wx.MenuItem(menuPop, 600, _(u"Exporter au format Texte"))
        bmp = wx.Bitmap("Images/16x16/Texte2.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportTexte, id=600)
        
        # Item Export Excel
        item = wx.MenuItem(menuPop, 700, _(u"Exporter au format Excel"))
        bmp = wx.Bitmap("Images/16x16/Excel.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.ExportExcel, id=700)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_(u"Liste des prestations"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_(u"Liste des prestations"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def ExportTexte(self, event):
        import UTILS_Export
        UTILS_Export.ExportTexte(self, titre=_(u"Liste des prestations"))
        
    def ExportExcel(self, event):
        import UTILS_Export
        UTILS_Export.ExportExcel(self, titre=_(u"Liste des pieces"))

    def OnActivated(self,event):
        self.SetCheckState(self.GetSelectedObject(),True)
        self.Refresh()

    def Monter(self, event):
        if len(self.GetSelectedObjects()) == 0 :
            dlg = wx.MessageDialog(self, _(u"Vous n'avez sélectionné aucune ligne !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.donnees = self.GetObjects()
            for obj in self.donnees:
                if self.GetSelectedObject() == obj:
                    idx = self.donnees.index(obj)
                    sel = idx
                    obj2 = obj
                    if idx >0:
                        self.donnees.insert(idx-1,self.donnees.pop(idx))
            self.SetObjects(self.donnees)
            self.SelectObject(obj2, deselectOthers=True, ensureVisible=True)
            self.Refresh()

    def Descendre(self, event):
        if len(self.GetSelectedObjects()) == 0 :
            dlg = wx.MessageDialog(self, _(u"Vous n'avez sélectionné aucune ligne !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.donnees = self.GetObjects()
            for obj in self.donnees:
                if self.GetSelectedObject() == obj:
                    idx = self.donnees.index(obj)
                    obj2 = obj
                    if idx < len(self.donnees):
                        self.donnees.insert(idx+1,self.donnees.pop(idx))
            self.SetObjects(self.donnees)
            self.SelectObject(obj2, deselectOthers=True, ensureVisible=True)
            self.Refresh()

    def Supprimer(self, event):
        if len(self.GetSelectedObjects()) == 0 :
             aGestionDB.MessageBox(self,u"Vous n'avez sélectionné aucune ligne", titre = "Traitement impossible!")
             return
        #nombre de pieces pointées par l'inscription pour la supprimer si une seule
        req = """ SELECT * FROM matPieces
                    WHERE pieIDinscription = %s ;""" % (self.GetSelectedObject().IDinscription)
        DB = aGestionDB.DB()
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            aGestionDB.MessageBox(self,retour)
            return None
        retour = DB.ResultatReq()
        DB.Close()
        nbPieces = len(retour)
        listeChamps = self.fgest.StandardiseNomsChamps(self.listeChampsPiece)
        dictDonnees = OlvToDict(self,listeChamps,self.GetSelectedObject())
        if not self.fgest.PieceSuppressible(self,dictDonnees):
            aGestionDB.MessageBox(self,u"Cette pièce n'est pas suppressible vu son état comptable !\nSupprimer directement les inscriptions, consommations associées ou faire un avoir global", titre="Traitement impossible")
        else:
            self.fgest.Suppression(self,dictDonnees,nbPieces)
        self.InitObjectListView()
        self.Refresh()

    def ComposeDictDonnees(self,track):
        listeChamps = self.fgest.StandardiseNomsChamps(self.listeChampsPiece)
        dictDonnees = OlvToDict(self,listeChamps,track)
        return dictDonnees


    def CocheTout(self, event=None):
        if self.GetFilter() != None :
            listeObjets = self.GetFilteredObjects()
        else :
            listeObjets = self.GetObjects()
        for track in listeObjets :
            self.Check(track)
            self.RefreshObject(track)

    def CocheRien(self, event=None):
        for track in self.donnees :
            self.Uncheck(track)
            self.RefreshObject(track)

    def GetTracksCoches(self):
        return self.GetCheckedObjects()

# -------------------------------------------------------------------------------------------------------------------------------------------

class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False
        
        self.SetDescriptiveText(_(u"Rechercher..."))
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

class ListviewAvecFooter(PanelAvecFooter):
    def __init__(self, parent, kwargs={}):
        dictColonnes = {
            "label" : {"mode" : "nombre", "singulier" : _(u"pièce :"), "pluriel" : _(u"pièces :"), "alignement" : wx.ALIGN_RIGHT},
            "montant" : {"mode" : "total"},
            "mttRegle" : {"mode" : "total"},
            }
        PanelAvecFooter.__init__(self, parent, ListView, kwargs, dictColonnes)

# ----------------- FRAME DE TEST ----------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, footer, factures, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)

        if footer == "sans":
            self.myOlv = ListView(panel, -1, IDpayeur = 6163, factures_parent = (factures, self), style=wx.LC_REPORT|wx.SUNKEN_BORDER,)
            self.myOlv.MAJ()
        else:
            self.myOlv = ListviewAvecFooter(self,  kwargs={"IDpayeur" : 6163, "factures_parent" : (factures,self),"parent":self})
            self.olv_piecesFiltrees = self.myOlv.GetListview()
            self.olv_piecesFiltrees.MAJ()
            self.Refresh()
        sizer_2.Add(self.myOlv, 1, wx.ALL|wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.SetSize((900, 400))
        self.Layout()


if __name__ == '__main__':
    app = wx.App(0)
    # Paramétres MyFrame (footer,factures, parent, id)
    frame_1 = MyFrame("avec", True, None, -1)
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
