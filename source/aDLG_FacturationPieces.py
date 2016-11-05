#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, Jacques BRUNEL
# Licence:         Licence GNU GPL
# Gestion des pieces niveau payeur en vue de facturation
# Derive de DLG_Famille_prestations
#------------------------------------------------------------------------


from UTILS_Traduction import _
import wx
import aOL_FacturationPieces
import aGestionDB
import aGestionInscription
import aUTILS_Facturation
import wx.lib.agw.hyperlink as Hyperlink
import CTRL_Bandeau
import CTRL_Bouton_image
import datetime
import UTILS_Utilisateurs
import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", u"€")

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL="", listeChoix=[], indexChoixDefaut=None, champFiltre="", labelDefaut="", size=(-1, -1), pos=(0, 0)):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL, size=size, pos=pos)
        self.parent = parent
        self.listeChoix = listeChoix
        self.indexChoixDefaut = indexChoixDefaut
        self.champFiltre = champFiltre
        self.labelDefaut = labelDefaut

        if self.GetGrandParent().GetName() == "notebook" :
            self.SetBackgroundColour(self.GetGrandParent().GetThemeBackgroundColour())

        self.URL = URL
        self.AutoBrowse(False)
        self.SetColours("BLUE", "BLUE", "BLUE")
        self.SetUnderlines(False, False, True)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)
    
    def SetListeChoix(self, listeChoix=[]):
        self.listeChoix = listeChoix
        
    def OnLeftLink(self, event):
        self.listeChoix.sort()
        listeItems = [self.labelDefaut,]
        for label, ID in self.listeChoix :
            listeItems.append(label)
        dlg = wx.SingleChoiceDialog(self, _(u"Choisissez un filtre dans la liste suivante :"), _(u"Filtrer la liste"), listeItems, wx.CHOICEDLG_STYLE)
        if self.indexChoixDefaut != None and self.indexChoixDefaut < len(self.listeChoix) :
            dlg.SetSelection(self.indexChoixDefaut)
        if dlg.ShowModal() == wx.ID_OK:
            indexChoix = dlg.GetSelection() - 1
            # Modification du label de l'hyperlien
            if indexChoix == -1 :
                self.SetLabel(self.labelDefaut)
                self.indexChoixDefaut = None
                ID = None
            else:
                self.SetLabel(self.listeChoix[indexChoix][0])
                self.indexChoixDefaut = self.listeChoix[indexChoix][1]
                ID = self.listeChoix[indexChoix][1]
            # MAJ
            self.parent.olv_piecesFiltrees.SetFiltre(self.champFiltre, ID)
            self.parent.gridsizer_options.Layout()
            self.parent.Refresh() 
        dlg.Destroy()
        self.UpdateLink()

# -----------------------------------------------------------------------------------------------------------------------

    def MAJ(self):
        self.listeDonnees = []
        self.Importation_factures()
        listeItems = []
        if len(self.listeDonnees) > 0 :
            for dictValeurs in self.listeDonnees :
                label = dictValeurs["nom"]
                if label == None :
                    label = "Inconnu (ID%d)" % dictValeurs["ID"]
                listeItems.append(label)
        self.Set(listeItems)

    def Importation_factures(self):
        db = aGestionDB.DB()
        req = """SELECT activites.IDactivite, nom, nbre_inscrits_max, COUNT(inscriptions.IDinscription)
        FROM activites
        LEFT JOIN inscriptions ON inscriptions.IDactivite = activites.IDactivite
        %s
        GROUP BY activites.IDactivite
        ORDER BY nom; """
        db.ExecuterReq(req)
        listeDonnees = db.ResultatReq()
        db.Close()
        for IDactivite, nom, nbre_inscrits_max, nbre_inscrits in listeDonnees :
            valeurs = { "ID" : IDactivite, "nom" : nom, "nbre_inscrits_max" : nbre_inscrits_max, "nbre_inscrits" : nbre_inscrits }
            self.listeDonnees.append(valeurs)

class PnlFactures(wx.Panel):
    def __init__(self, parent,IDpayeur=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.listviewAvecFooter = aOL_FacturationPieces.ListviewAvecFooter(self, kwargs={"IDpayeur" : IDpayeur, "factures_parent" : (True,self.parent)})
        self.olv_piecesFiltrees = self.listviewAvecFooter.GetListview()

        gridsizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=0, hgap=0)
        gridsizer_base.Add(self.listviewAvecFooter, 1, wx.EXPAND, 0)
        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableCol(0)
        gridsizer_base.AddGrowableRow(0)
        self.Layout()
        self.olv_piecesFiltrees.MAJ()
        self.Refresh()

class Dialog(wx.Dialog):
    def __init__(self, parent, IDpayeur=None):
        wx.Dialog.__init__(self, parent, -1, pos=(-1,-1),  style=wx.DEFAULT_DIALOG_STYLE|wx.THICK_FRAME)
        self.parent = parent
        DB = aGestionDB.DB()
        self.user = DB.UtilisateurActuel()
        self.rw = UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_facturation", "creer", afficheMessage=False)
        nomPayeur = aGestionDB.AppelDB("GetNomIndividu",IDpayeur)
        self.titre = (u"Choix des pièces pour génération facture")
        intro = (u"Payeur %s" % nomPayeur )
        self.SetTitle("aDLG_FacturationPieces")
        self.IDpayeur = IDpayeur
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=self.titre, texte=intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")
        self.staticbox_factures = wx.StaticBox(self, -1, _(u"Factures de la saison"))
        self.ctrl_factures = PnlFactures(self,self.IDpayeur)
        self.ctrl_factures.SetMinSize((-1, 80))

        self.staticbox_pieces = wx.StaticBox(self, -1, _(u"Pieces non facturées"))
        # OL Pieces
        self.listviewAvecFooter = aOL_FacturationPieces.ListviewAvecFooter(self, kwargs={"IDpayeur" : IDpayeur, "factures_parent" : (False, self)})
        self.olv_piecesFiltrees = self.listviewAvecFooter.GetListview()
        self.ctrl_recherche = aOL_FacturationPieces.CTRL_Outils(self, listview=self.olv_piecesFiltrees, afficherCocher=True)
        self.ctrl_recherche.SetBackgroundColour((255, 255, 255))

        # Commandes boutons à droite Haut
        self.bouton_imprimerFact = wx.BitmapButton(self, -1, wx.Bitmap(u"Images/16x16/Imprimante.png", wx.BITMAP_TYPE_ANY))
        # Commandes boutons à droite Bas
        self.bouton_monter = wx.BitmapButton(self, -1, wx.Bitmap(u"Images/16x16/Fleche_haut.png", wx.BITMAP_TYPE_ANY))
        self.bouton_descendre = wx.BitmapButton(self, -1, wx.Bitmap(u"Images/16x16/Fleche_bas.png", wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(u"Images/16x16/Supprimer.png", wx.BITMAP_TYPE_ANY))
        self.bouton_imprimer = wx.BitmapButton(self, -1, wx.Bitmap(u"Images/16x16/Imprimante.png", wx.BITMAP_TYPE_ANY))

        # Pied
        #self.staticbox_pied= wx.StaticBox(self, -1, )
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Facturer"), cheminImage="Images/32x32/Generation.png")
        self.bouton_devis = CTRL_Bouton_image.CTRL(self, texte=_(u"Devis"), cheminImage="Images/32x32/zoom_tout.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Fermer"), cheminImage="Images/32x32/Annuler.png")

        #self.__set_data()
        self.__set_properties()
        self.__do_layout()
        self.MAJ()

    def __set_properties(self):
        self.SetMinSize((1000, 600))
        self.bouton_ok.Enable(self.rw)
        self.bouton_devis.Enable(self.rw)
        # Binds
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimerFact, self.bouton_imprimerFact)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonMonter, self.bouton_monter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonDescendre, self.bouton_descendre)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonImprimer, self.bouton_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOK, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonDevis, self.bouton_devis)

        # Propriétés
        self.bouton_imprimerFact.SetToolTipString(_(u"Cliquez ici pour imprimer les factures"))
        self.bouton_monter.SetToolTipString(_(u"Cliquez ici pour monter la pièce sélectionnée d'un niveau"))
        self.bouton_descendre.SetToolTipString(_(u"Cliquez ici pour descendre la pièce sélectionnée d'un niveau"))
        self.bouton_supprimer.SetToolTipString(_(u"Cliquez ici pour supprimer la piece sélectionnée"))
        self.bouton_imprimer.SetToolTipString(_(u"Cliquez ici pour imprimer la liste"))
        self.bouton_ok.SetToolTipString(_(u"Accéder à la facturation des pièces cochées"))
        self.bouton_devis.SetToolTipString(_(u"Faire une devis avec les pièces cochées"))
        self.olv_piecesFiltrees.SetToolTipString(_(u"Cochez les pièces que vous voulez assembler dans une seule facture"))

    def __do_layout(self):
        # Layout
        gridsizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=5, hgap=5)
        gridsizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        staticbox_factures = wx.StaticBoxSizer(self.staticbox_factures, wx.VERTICAL)
        gridsizer_factures = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        gridsizer_factures.Add(self.ctrl_factures, 1, wx.EXPAND, 0)
        gridsizer_factures.Add(self.bouton_imprimerFact, 1, wx.EXPAND, 0)
        gridsizer_factures.AddGrowableCol(0)
        gridsizer_factures.AddGrowableRow(0)
        staticbox_factures.Add(gridsizer_factures, 1, wx.EXPAND|wx.ALL, 5)
        gridsizer_base.Add(staticbox_factures, 1, wx.EXPAND|wx.ALL, 5)

        staticbox_pieces = wx.StaticBoxSizer(self.staticbox_pieces, wx.VERTICAL)

        gridsizer_BAS = wx.FlexGridSizer(rows=2, cols=1, vgap=5, hgap=5)
        gridsizer_pieces = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        
        gridsizer_pieces.Add(self.listviewAvecFooter, 1, wx.EXPAND, 0)
        
        gridsizer_boutons = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        gridsizer_boutons.Add(self.bouton_monter, 0, wx.ALL, 0)
        gridsizer_boutons.Add(self.bouton_descendre, 0, wx.ALL, 0)
        gridsizer_boutons.Add(self.bouton_supprimer, 0, wx.ALL, 0)
        gridsizer_boutons.Add( (10, 10), 0, wx.ALL, 0)
        gridsizer_boutons.Add(self.bouton_imprimer, 0, wx.ALL, 0)
        gridsizer_pieces.Add(gridsizer_boutons, 1, wx.ALL, 0)
        
        gridsizer_pieces.Add(self.ctrl_recherche, 0, wx.EXPAND|wx.ALL, 0)
        gridsizer_pieces.AddGrowableCol(0)
        gridsizer_pieces.AddGrowableRow(0)

        gridsizer_BAS.Add(gridsizer_pieces, 1, wx.EXPAND|wx.ALL, 5)

        gridsizer_pied = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        gridsizer_pied.Add((15, 15), 0, wx.EXPAND, 0)
        gridsizer_pied.Add(self.bouton_devis, 0, 0, 0)
        gridsizer_pied.Add(self.bouton_ok, 0, 0, 0)
        gridsizer_pied.Add(self.bouton_annuler, 0, 0, 0)
        gridsizer_pied.AddGrowableCol(0)
        gridsizer_pied.AddGrowableRow(0)
        gridsizer_BAS.Add(gridsizer_pied, 1, wx.EXPAND|wx.ALL, 5)
        gridsizer_BAS.AddGrowableCol(0)
        gridsizer_BAS.AddGrowableRow(0)
        staticbox_pieces.Add(gridsizer_BAS, 1, wx.EXPAND|wx.ALL, 5)

        gridsizer_base.Add(staticbox_pieces, 1, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(gridsizer_base)
        gridsizer_base.Fit(self)
        gridsizer_base.AddGrowableCol(0)
        gridsizer_base.AddGrowableRow(1)
        gridsizer_base.AddGrowableRow(2)

    def OnBoutonImprimerFact(self, event):
        objects = self.ctrl_factures.olv_piecesFiltrees.GetTracksCoches()
        if len(objects) == 0:
            aGestionDB.MessageBox(self,u"Vous n'avez coché aucune ligne ! ",titre="Continuation impossible")
            return
        # Calcul des champs de la table facture
        listeFactures = []
        for obj in objects:
            if obj.noFacture > 0:
                if not obj.noFacture in listeFactures:
                    listeFactures.append(obj.noFacture)
        if len(listeFactures)>0:
            fFact = aUTILS_Facturation.Facturation()
            dictOptions =  {u'largeur_colonne_date': 50, u'texte_conclusion': u'', u'image_signature': u'', u'texte_titre': u'Facture', u'taille_texte_prestation': 7, u'afficher_avis_prelevements': True, u'taille_texte_messages': 7, u'afficher_qf_dates': True, u'taille_texte_activite': 6, u'affichage_prestations': 0, u'affichage_solde': 0, u'afficher_coupon_reponse': True, u'taille_image_signature': 100, u'alignement_image_signature': 0, u'couleur_fond_conclusion': wx.Colour(255, 255, 255, 255), u'alignement_texte_introduction': 0, u'couleur_bord_conclusion': wx.Colour(255, 255, 255, 255), u'afficher_reglements': True, u'intitules': 0, u'integrer_impayes': False, u'taille_texte_introduction': 9, u'taille_texte_noms_colonnes': 5, u'texte_introduction': u'', u'taille_texte_individu': 9, u'taille_texte_conclusion': 9, u'taille_texte_labels_totaux': 9, u'afficher_periode': False, u'couleur_bord_introduction': wx.Colour(255, 255, 255, 255), u'afficher_codes_barres': True, u'couleur_fond_introduction': wx.Colour(255, 255, 255, 255), u'taille_texte_titre': 19, u'taille_texte_periode': 8, u'IDmodele': 5, u'couleur_fond_2': wx.Colour(234, 234, 255, 255), u'afficher_titre': True, u'couleur_fond_1': wx.Colour(204, 204, 255, 255), u'largeur_colonne_montant_ht': 50, u'afficher_impayes': True, 'messages': [], u'memoriser_parametres': True, u'afficher_messages': True, u'largeur_colonne_montant_ttc': 70, u'taille_texte_montants_totaux': 10, u'alignement_texte_conclusion': 0, u'style_texte_introduction': 0, u'style_texte_conclusion': 0, u'repertoire_copie': u'', u'largeur_colonne_montant_tva': 50}
            fFact.Impression(listeNoFactures=listeFactures,typeLancement="factures", dictOptions = dictOptions, afficherDoc=True,repertoire = dictOptions["repertoire_copie"])

    def OnBoutonMonter(self, event):
        self.olv_piecesFiltrees.Monter(None)

    def OnBoutonDescendre(self, event):
        self.olv_piecesFiltrees.Descendre(None)

    def OnBoutonSupprimer(self, event):
        droitModif = UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "modifier")
        if droitModif:
            self.olv_piecesFiltrees.Supprimer(None)
            self.olv_piecesFiltrees.MAJ
            self.MAJ()
        else:
            aGestionDB.MessageBox(self, u"Vous ne disposez pas des droits 'individus_inscriptions' 'modifier' !", titre = "Utilisateur Noethys")

    def OnBoutonImprimer(self, event):
        if len(self.olv_piecesFiltrees.GetSelectedObjects()) == 0:
            noSelection = True
        else:
            noSelection = False
            ID = self.olv_piecesFiltrees.GetSelectedObjects()[0].IDnumPiece
                
        # Création du menu contextuel
        menuPop = wx.Menu()
        
        # Item Apercu avant impression
        item = wx.MenuItem(menuPop, 20, _(u"Aperçu avant impression"))
        bmp = wx.Bitmap("Images/16x16/Apercu.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=20)
        
        # Item Imprimer
        item = wx.MenuItem(menuPop, 30, _(u"Imprimer"))
        bmp = wx.Bitmap("Images/16x16/Imprimante.png", wx.BITMAP_TYPE_PNG)
        item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=30)
        
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        self.olv_piecesFiltrees.Apercu(None)

    def Imprimer(self, event):
        self.olv_piecesFiltrees.Imprimer(None)

    def OnBoutonOK(self,event):
        # Création d'une facture avec toutes les pièces cochées
        objects = self.olv_piecesFiltrees.GetTracksCoches()
        if len(objects) == 0:
            aGestionDB.MessageBox(self,u"Vous n'avez coché aucune ligne ! ",titre="Continuation impossible")
            return
        fGest = aGestionInscription.Forfaits(self)
        for obj in objects:
            fFac = aOL_FacturationPieces.ListView(self, IDpayeur= self.IDpayeur, factures_parent= (True,self.parent))
            dictDonnees = fFac.ComposeDictDonnees(obj)
            if dictDonnees["nature"] == u"DEV":
                fGest.AjoutConsommations(self,dictDonnees)
            if dictDonnees["nature"] in (u"RES",u"DEV"):
                fGest.GetPieceModif(self,dictDonnees["IDindividu"],dictDonnees["IDactivite"])
                dictDonnees = fGest.dictPiece
                IDprestation = fGest.AjoutPrestation(self,dictDonnees)
                dictDonnees["IDprestation"] = IDprestation
                if IDprestation > 0 :
                    fGest.ModifiePieceCree(self,dictDonnees)
                    fGest.ModifieConsoCree(self,dictDonnees)
                    obj.IDprestation = IDprestation
        # Calcul des champs de la table facture
        activites = []
        individus = []
        date_debut = "2999-01-01"
        date_fin =  "1900-01-01"
        total = 0.00
        regle = 0.00
        for obj in objects:
            if obj.IDactivite > 0: activites.append(obj.IDactivite)
            if obj.IDindividu > 0:individus.append(obj.IDindividu)
            if obj.dateModif < date_debut:
                date_debut = obj.dateModif
            if obj.dateModif > date_fin:
                date_fin = obj.dateModif
            if obj.montant != None: total += obj.montant
            if obj.mttRegle != None: regle += obj.mttRegle
        def listeChaine(maListe):
            chaine = ""
            for item in maListe:
                chaine = chaine + str(item) +";"
            chaine = chaine[:-1]
            return chaine
        numero, date = aGestionInscription.GetNoFactureMin()
        # test des ventilations de réglement sur les prestations

        # Composition de l'enregistrement facture
        listeDonnees = [
            ("numero",numero ),
            ("IDcompte_payeur", self.IDpayeur),
            ("date_edition", date),
            ("date_echeance", str(datetime.date.today()+datetime.timedelta(days=30))),
            ("IDutilisateur", self.user),
            ("IDlot", 1),
            ("prestations", "Origine Piece Facture"),
            ("etat", None),
            ("activites",listeChaine(activites)),
            ("individus",listeChaine(individus)),
            ("date_debut",date_debut),
            ("date_fin",date_fin),
            ("total",total),
            ("regle",regle),
            ("solde",(total-regle)),
            ]
        #self.Destroy()
        DB = aGestionDB.DB()
        retour = DB.ReqInsert("factures", listeDonnees,retourID = True)
        if retour != "ok" :
            aGestionDB.MessageBox(self,retour)
            DB.Close()
            return None
        IDnumFacture = DB.newID
        # Ecriture du numéro de facture dans les pieces, ecrire l'IDfacture dans les prestations.
        fGest = aGestionInscription.Forfaits(self)
        for obj in objects:
            retour = fGest.MajNoFact(self,obj,listeDonnees,IDnumFacture)
        self.Destroy()
        #fin OnBoutonOK

    def OnBoutonDevis(self,event):
        # Impression d'un Devis avec toutes les pièces cochées
        objects = self.olv_piecesFiltrees.GetTracksCoches()
        if len(objects) == 0:
            aGestionDB.MessageBox(self,u"Vous n'avez coché aucune ligne ! ",titre="Continuation impossible")
            return
        listePieces = []
        for obj in objects:
            listePieces.append(obj.IDnumPiece)
        dictOptions = {u'largeur_colonne_date': 50, u'texte_conclusion': u'', u'image_signature': u'', u'texte_titre': u'Devis', u'taille_texte_prestation': 7, u'afficher_avis_prelevements': True, u'taille_texte_messages': 7, u'afficher_qf_dates': True, u'taille_texte_activite': 6, u'affichage_prestations': 0, u'affichage_solde': 0, u'afficher_coupon_reponse': True, u'taille_image_signature': 100, u'alignement_image_signature': 0, u'couleur_fond_conclusion': wx.Colour(255, 255, 255, 255), u'alignement_texte_introduction': 0, u'couleur_bord_conclusion': wx.Colour(255, 255, 255, 255), u'afficher_reglements': True, u'intitules': 0, u'integrer_impayes': False, u'taille_texte_introduction': 9, u'taille_texte_noms_colonnes': 5, u'texte_introduction': u'', u'taille_texte_individu': 9, u'taille_texte_conclusion': 9, u'taille_texte_labels_totaux': 9, u'afficher_periode': False, u'couleur_bord_introduction': wx.Colour(255, 255, 255, 255), u'afficher_codes_barres': True, u'couleur_fond_introduction': wx.Colour(255, 255, 255, 255), u'taille_texte_titre': 19, u'taille_texte_periode': 8, u'IDmodele': 5, u'couleur_fond_2': wx.Colour(234, 234, 255, 255), u'afficher_titre': True, u'couleur_fond_1': wx.Colour(204, 204, 255, 255), u'largeur_colonne_montant_ht': 50, u'afficher_impayes': True, 'messages': [], u'memoriser_parametres': True, u'afficher_messages': True, u'largeur_colonne_montant_ttc': 70, u'taille_texte_montants_totaux': 10, u'alignement_texte_conclusion': 0, u'style_texte_introduction': 0, u'style_texte_conclusion': 0, u'repertoire_copie': u'', u'largeur_colonne_montant_tva': 50}
        fImp = aUTILS_Facturation.Facturation()
        retour = fImp.Impression(listePieces=listePieces,typeLancement="devis", dictOptions=dictOptions, afficherDoc=True,repertoire=dictOptions["repertoire_copie"])
        #fin OnBoutonDevis

    def MAJ(self):
        """ MAJ integrale du controle avec MAJ des donnees """
        self.olv_piecesFiltrees.MAJ()
        self.Refresh()

    def ValidationData(self):
        """ Return True si les données sont valides et pretes à être sauvegardées """
        return True
    
    def Sauvegarde(self):
        pass

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dlg = Dialog(None, 6163)
    #dlg.MAJ()
    app.SetTopWindow(dlg)
    dlg.Show()
    app.MainLoop()