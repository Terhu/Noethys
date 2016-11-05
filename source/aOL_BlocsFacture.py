#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, Jacques Brunel
# Gestion de la table BlocsFacture définissant le regroupement des lignes
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import copy
import aGestionDB
from ObjectListView import FastObjectListView, ColumnDefn, Filter, CTRL_Outils

import UTILS_Utilisateurs

class ListView(FastObjectListView):
    def __init__(self,parent, *args, **kwds):
        self.parent = parent
        self.popupIndex = -1
        self.listeFiltres = []
        # Initialisation du listCtrl
        FastObjectListView.__init__(self, *args, **kwds)
        # Binds perso
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        
    def OnItemActivated(self,event):
        self.parent.choix = self.GetSelectedObject()
        self.parent.EndModal(wx.ID_OK)

    def InitModel(self):
        """ Récupération des données """
        DB = aGestionDB.DB()
        req = """SELECT lfaCodeBlocFacture,lfaLibelle,lfaOrdre,lfaTypeLigne,lfaFormat
        FROM matBlocsFactures ORDER BY lfaCodeBlocFacture; """
        DB.ExecuterReq(req)
        self.donnees = copy.deepcopy(DB.ResultatReq())
        DB.Close()
        return

    def InitObjectListView(self):            
        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED" 
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True
        liste_Colonnes = [
            ColumnDefn(_(u"Code"), "left", 0, 0, typeDonnee="texte"),
            ColumnDefn(_(u"Code"), "left", 80, 0, typeDonnee="texte"),
            ColumnDefn(_(u"Libelle"), 'left', 150, 1, typeDonnee="texte",isSpaceFilling = True),
            ColumnDefn(_(u"Rang"), 'left', 40, 2, typeDonnee="entier"),
            ColumnDefn(_(u"Type"), 'left', 120, 3, typeDonnee="texte"),
            ColumnDefn(_(u"Format"), 'left',80, 4, typeDonnee="texte"),
            ]
        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_(u"Aucun bloc défini"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, face="Tekton"))
        self.SetSortColumn(self.columns[0])
        self.SetObjects(self.donnees)

    def MAJ(self, ID=None):
        self.InitModel()
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
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_(u"Liste des blocs lignes facture"), format="A", orientation=wx.PORTRAIT)
        prt.Preview()

    def Imprimer(self, event):
        import UTILS_Printer
        prt = UTILS_Printer.ObjectListViewPrinter(self, titre=_(u"Liste des blocs lignes facture"), format="A", orientation=wx.PORTRAIT)
        prt.Print()

    def PrepareEnreg(self, listeDonnees, mode):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "creer") == False :
            aGestionDB.MessageBox(self,u"Vous n'avez pas les droits de paramétrage activité")
        else :
            import aDLG_SaisieBlocsFacture
            dlg = aDLG_SaisieBlocsFacture.Dialog(self,mode)
            if listeDonnees <> None :
                dlg.SetBloc(listeDonnees)
            listeDonnees = []
            if dlg.ShowModal() == wx.ID_OK:
                code = dlg.ctrl_code.GetValue()
                libelle = dlg.ctrl_libelle.GetValue()
                ordre = dlg.spin_ordre.GetValue()
                type = dlg.choice_typeLigne.GetStringSelection()
                format = dlg.choice_formatLigne.GetStringSelection()
                listeDonnees = [("lfaCodeBlocFacture", code ), ("lfaLibelle", libelle),("lfaOrdre", ordre),("lfaTypeLigne", type),("lfaFormat", format),]
            dlg.Destroy()
        return listeDonnees

    def Ajouter(self, event):
        listeDonnees = self.PrepareEnreg(None,"ajout")
        if len(listeDonnees)== 0 :return
        DB = aGestionDB.DB()
        retour = DB.ReqInsert("matBlocsFactures", listeDonnees)
        DB.Close()
        if retour == "ok" :
            self.MAJ()
        else :
            aGestionDB.MessageBox(self,retour)

    def Modifier(self, event):
        if len(self.Selection()) == 0 :
            aGestionDB.MessageBox(self, u"Vous n'avez sélectionné aucun bloc dans la liste")
            return
        listeDonnees = self.PrepareEnreg(self.Selection()[0],"modif")
        if len(listeDonnees)== 0 :return
        DB = aGestionDB.DB()
        code = str(listeDonnees[0][1])
        retour = DB.ReqMAJ("matBlocsFactures", listeDonnees, "lfaCodeBlocFacture",code)
        DB.Close()
        if retour == "ok" :
            self.MAJ()
        else :
            aGestionDB.MessageBox(self,retour)

    def Supprimer(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_activites", "supprimer") == False : return
        if len(self.Selection()) == 0 :
            dlg = wx.MessageDialog(self, _(u"Vous n'avez sélectionné aucun bloc dans la liste"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        bloc = self.Selection()[0]
        # Vérifie que ce type de bloc n'a pas déjà été utilisé
        DB = aGestionDB.DB()
        req = """SELECT COUNT (artCodeArticle)
        FROM matArticles
        WHERE artCodeBlocFacture=%s
        ;""" % bloc[0]
        DB.ExecuterReq(req)
        resultat = DB.ResultatReq()
        if resultat <> [] :
            nbreBlocs = len(resultat)
            dlg = wx.MessageDialog(self, _(u"Ce Bloc a déjà été attribué %d fois.\n\nVous ne pouvez donc pas le supprimer !") % nbreBlocs, _(u"Suppression impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        DB.Close()
        # Confirmation de suppression
        dlg = wx.MessageDialog(self, _(u"Souhaitez-vous vraiment supprimer ce bloc ?"), _(u"Suppression"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES :
            DB = aGestionDB.DB()
            retour = DB.ReqDEL("matBlocsFactures", "lfaCodeBlocFacture", bloc[0])
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
