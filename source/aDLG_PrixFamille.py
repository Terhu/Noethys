# Derive de DLG_PrixActivite.py
# -*- coding: iso-8859-15 -*-
# -----------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, Jacques Brunel
# Ecran de tarification niveau famille derrière inscription
# -----------------------------------------------------------

from UTILS_Traduction import _
import wx
import datetime
import wx.lib.agw.hyperlink as Hyperlink
from ObjectListView import FastObjectListView, ColumnDefn,Filter, CTRL_Outils
import copy
import CTRL_Bouton_image
import CTRL_Bandeau
import UTILS_Config
import UTILS_Utilisateurs
import aGestionDB
import aDLG_ChoixLigne
import aDLG_FacturationPieces
import aGestionArticle
import aGestionInscription
from UTILS_Decimal import FloatToDecimal as FloatToDecimal

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", u"€")

def Fmt2d(montant):
    # Convert the given montant into a string with zero null
    if montant != 0:
        return "%.2f" % (montant)
    else:
        return " "

def FmtXd(montant):
    # Convert the given montant into décimales variables
    fmt = "%.4f" % montant
    if (1000*montant) % 1 < 0.01: fmt = "%.3f" % montant
    if (100*montant) % 1 < 0.001: fmt = "%.2f" % montant
    if (10*montant) % 1 < 0.0001: fmt = "%.1f" % montant
    if (montant) % 1 < 0.00001: fmt = "%.0f" % montant
    if montant == 0: fmt = " "
    return fmt

class Track(object):
    def __init__(self, track, origine = "articles"):
        self.codeArticle = track["codeArticle"]
        self.libelle =  track["libelle"]
        self.prix2 = track["prix2"]
        self.typeLigne = track["typeLigne"]
        self.conditions = track["condition"]
        self.modeCalcul = track["modeCalcul"]
        self.force = track["force"]
        if origine == "articles":
            #ChampsTrack = ["codeArticle", "libelle", "prix1", "prix2", "typeLigne", "conditions", "modeCalcul", "force"]
            self.prixUnit = track["prix1"]
            self.qte = 1
            montant = 0
        if origine == "lignes":
            #listeChamps=["codeArticle","libelle","quantite","prixUnit","montant"]
            #liste2=["prix2", "typeLigne", "condition", "modeCalcul", "force"]
            self.prixUnit = track["prixUnit"]
            self.qte =  track["quantite"]
            montant =  track["montant"]
        if self.prixUnit == None: self.prixUnit = 0
        if self.qte == None: self.qte = 0
        self.montantCalcul = self.prixUnit * self.qte
        self.montant = float(montant)
        self.qte = float(self.qte)

class CTRL_Solde(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="panel_solde", style=wx.SUNKEN_BORDER | wx.TAB_TRAVERSAL,
                          size=(100, 40))
        self.parent = parent

        # Solde du compte
        self.ctrl_solde = wx.StaticText(self, -1, u"0.00 %s " % SYMBOLE)
        font = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.ctrl_solde.SetFont(font)

        # Layout
        grid_sizer_base = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_solde, 1, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(0)
        # self.SetToolTipString(u"Solde")
        self.ctrl_solde.SetToolTipString(u"Solde")

    def SetSolde(self, montant=FloatToDecimal(0.0)):
        """ MAJ integrale du controle avec MAJ des donnees """
        if montant > FloatToDecimal(0.0):
            label = u"+ %.2f %s" % (montant, SYMBOLE)
            self.SetBackgroundColour("#C4BCFC")  # Bleu
        elif montant == FloatToDecimal(0.0):
            label = u"0.00 %s" % SYMBOLE
            self.SetBackgroundColour("#5DF020")  # Vert
        else:
            label = u"- %.2f %s" % (-montant, SYMBOLE)
            self.SetBackgroundColour("#F81515")  # Rouge
        self.ctrl_solde.SetLabel(label)
        self.Layout()
        self.Refresh()

# ---Gestion écran tarification --------------------------------------------------------------
class OLVtarification(FastObjectListView):
    def __init__(self,parent,IDpayeur, saisonFin, facture=False, *args, **kwds):
        FastObjectListView.__init__(self, parent, *args, **kwds)
        self.parent = parent
        self.facture = facture
        self.dictDonnees = {}
        self.dictDonneesParent = self.parent.dictDonneesParent
        IDfamille = self.dictDonneesParent["IDfamille"]
        fGest = aGestionInscription.Forfaits(self.parent)
        presence999 = fGest.GetPieceModif999(self,IDpayeur,saisonFin.year)
        if presence999:
            self.dictDonnees = fGest.dictPiece
            self.dictDonnees["origine"] = "modif"
        else:
            if (not facture) and fGest.AjoutPiece999(self,IDfamille,IDpayeur,saisonFin.year):
                self.dictDonnees = fGest.dictPiece
                self.dictDonnees["origine"] = "ajout"
        if not facture:
            if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer") == True :
                self.cellEditMode = FastObjectListView.CELLEDIT_SINGLECLICK
        self.listeChampsTrack = ["codeArticle", "libelle", "prix1", "prix2", "typeLigne", "condition", "modeCalcul","force"]
        #fin __init__

    def InitObjectListView(self):
        if len(self.dictDonnees)==0:
            self.listeOLV = None
        elif (len(self.dictDonnees["lignes_piece"]) == 0):
            self.listeOLV = self.AppelDonnees()
        elif self.facture == True:
            self.listeOLV = self.AppelDonneesAnte()
        elif (self.dictDonnees["origine"] == "ajout"):
            self.listeOLV = self.AppelDonnees()
        else :
            self.listeOLV = self.AppelDonneesAnte()

        # Couleur en alternance des lignes
        self.oddRowsBackColor = "#F0FBED"
        self.evenRowsBackColor = wx.Colour(255, 255, 255)
        self.useExpansionColumn = True

        liste_Colonnes = [
            ColumnDefn("Code", "center", 100, "codeArticle",typeDonnee="texte"),
            ColumnDefn("Libelle (libelles modifiables)", "left", 300,"libelle",typeDonnee="texte",isSpaceFilling = True ),
            ColumnDefn("Qté", "right", 50, "qte",typeDonnee="montant",stringConverter=FmtXd),
            ColumnDefn("Calculé", "right", 100, "montantCalcul",typeDonnee="montant",stringConverter="%.2f"),
            ColumnDefn("Forcé", "right", 100, "montant",typeDonnee="montant",stringConverter=Fmt2d),
            ]

        self.SetColumns(liste_Colonnes)
        self.SetEmptyListMsg(_(u"Aucune ligne trouvée"))
        self.SetEmptyListMsgFont(wx.FFont(11, wx.DEFAULT, face="Tekton"))
        self.CreateCheckStateColumn()
        self.SetSortColumn(self.columns[1])
        self.SetObjects(self.listeOLV)
        #fin InitObjectListView

    def OnItemActivated(self,event):
        self.parent.choix = self.GetSelectedObject()
        self.parent.EndModal(wx.ID_OK)

    def AppelDonnees(self,listeOLV = []):
        """ Récupération des données en mode ajout création de pièce """
        DB = aGestionDB.DB()
        req = """SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, matArticles.artPrix2, matBlocsFactures.lfaTypeLigne, matArticles.artConditions, matArticles.artModeCalcul, 'OUI' as force
                FROM matArticles
                LEFT JOIN matBlocsFactures ON matArticles.artCodeBlocFacture = matBlocsFactures.lfaCodeBlocFacture
                WHERE artNiveauFamille = 1 AND ((matArticles.artCodeArticle LIKE 'x%%') OR (matArticles.artCodeArticle LIKE '$%%'));
                """
        retour = DB.ExecuterReq(req)
        if retour <> "ok":
            DB.AfficheErr(self,retour)
        else :
            recordset = DB.ResultatReq()
            if len(recordset) > 0:
                listeOLV = self.AjoutDonneesOLV(recordset,listeOLV)
        DB.Close()
        return listeOLV
        #fin AppelDonnees

    def AppelDonneesAnte(self):
        # Ressortir les lignes des saisies précédentes provenant de table PieceLignes
        listeLignes= self.dictDonnees["lignes_piece"]
        listeOLV = self.EnrichirDonnees(listeLignes)
        # Ajout des articles communs
        listeOLV = self.AppelDonnees(listeOLV)
        return listeOLV

    def AjoutDonneesOLV(self,recordset,listeOLV):
        # Ajoute à le contenu de recordset à listeOLV avec étape intermédiaire en liste de dictionnaires
        donnees= []
        for item in recordset:
            i = 0
            record = {}
            for champ in self.listeChampsTrack :
                record[champ] = item[i]
                i= i +1
            # test de présence pour éviter les doubles
            ok = True
            for ligne in listeOLV:
                if ligne.codeArticle == record["codeArticle"]: ok = False
            if ok:
                donnees.append(record)
        #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        aCond= aGestionArticle.ActionsConditions(self.dictDonnees)
        for item in donnees:
            # Gestion pour PreCoche
            if item["codeArticle"][0] != "$" : item["force"] = "NON"
            # seulemnt si condition respectée
            if aCond.Condition(item["condition"],item["codeArticle"]):
                track = Track(item,"articles")
                listeOLV.append(track)
        return listeOLV

    def EnrichirDonnees(self,listeLignes):
        # Complete les articles simples en lignes-piece pour les champs liste2 liés à l'article et bascule en track la liste de dictionnaire
        donnees = []
        listeChamps=["codeArticle","libelle","quantite","prixUnit","montant"]
        liste2=["prix2", "typeLigne", "condition", "modeCalcul", "force"]
        DB = aGestionDB.DB()
        # Transposition des données SQL avec les noms de champs utilisés en track
        if listeLignes <> None:
            for dictLigne in listeLignes:
                record = {}
                i=0
                for champLigne in listeChamps:
                    record[champLigne] = dictLigne[champLigne]
                    i += 1
                req = """SELECT matArticles.artCodeArticle, matArticles.artLibelle, matArticles.artPrix1, matArticles.artPrix2, matBlocsFactures.lfaTypeLigne, matArticles.artConditions, matArticles.artModeCalcul, "OUI" as force
                    FROM matArticles LEFT JOIN matBlocsFactures ON matArticles.artCodeBlocFacture = matBlocsFactures.lfaCodeBlocFacture
                    WHERE (((matArticles.artCodeArticle)= "%s"));
                    """ % record["codeArticle"]
                retour = DB.ExecuterReq(req)
                if retour <> "ok" : DB.AfficheErr(self,retour)
                recordset = DB.ResultatReq()
                i=3
                for champLigne in liste2:
                    if len(recordset)>0:
                        record[champLigne] = recordset[0][i]
                    else: record[champLigne] = None
                    i += 1
                donnees.append(record)
        DB.Close()
        #Transpose les données de type listes avec clés en objets tracks avec attributs pour OLV
        listeOLV = []
        aCond= aGestionArticle.ActionsConditions(self.dictDonnees)
        for item in donnees:
            if aCond.Condition(item["condition"],item["codeArticle"]):
                track = Track(item,"lignes")
                listeOLV.append(track)
        return listeOLV
        #fin EnrichirDonnees

    def Selection(self):
        return self.GetSelectedObjects()

class DlgTarification(wx.Dialog):
    def __init__(self,dictDonneesParent):
        """Constructor   |wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.THICK_FRAME"""
        wx.Dialog.__init__(self, None, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.THICK_FRAME)
        if dictDonneesParent.has_key("IDactivite"):
            self.saisonDeb,self.saisonFin = aGestionArticle.Saison(IDactivite = dictDonneesParent["IDactivite"])
        else: self.saisonDeb,self.saisonFin = aGestionArticle.Saison()
        self.IDcompte_payeur = dictDonneesParent["IDcompte_payeur"]
        self.dictDonneesParent = dictDonneesParent
        # Verrouillage utilisateurs
        self.SetTitle(_(u"aDLG_PrixFamille"))
        DB = aGestionDB.DB()
        ligneInfo = "Payeur : " + DB.GetNomIndividu(self.IDcompte_payeur)+ " - Niveau familles"
        DB.Close()
        soustitreFenetre = u"Compléments pour l'ensemble des Inscriptions du " + self.saisonDeb.strftime("%d/%m/%Y")+ u" au "+ self.saisonFin.strftime("%d/%m/%Y")
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=ligneInfo, texte=soustitreFenetre, hauteurHtml=10,nomImage="Images/22x22/Smiley_nul.png")
        # Verrouillage utilisateurs
        self.rw = True
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "creer") == False :
            self.rw = False
        # conteneur des données
        self.staticbox_facture = wx.StaticBox(self, -1, _(u"Déjà facturé..."))
        self.staticbox_nonFacture = wx.StaticBox(self, -1, _(u"Non facturé modifiable ..."))
        self.resultsOlv = OLVtarification(self, self.IDcompte_payeur, self.saisonFin, facture=False,id=1, name="aDLG_PrixFamille", style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        self.resultsOlv.InitObjectListView()
        self.PreCoche()
        self.dictDonnees = self.resultsOlv.dictDonnees
        self.ctrl_recherche = CTRL_Outils(self, listview=self.resultsOlv)
        self.data = self.resultsOlv.listeOLV
        self.dataorigine = copy.deepcopy(self.data)
        self.resultsOlvFact = OLVtarification(self, self.IDcompte_payeur, self.saisonFin, facture=True, id=2, name="aDLG_Facture", style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES)
        self.resultsOlvFact.InitObjectListView()
        # pour conteneur des actions en pied d'écran
        self.pied_staticbox = wx.StaticBox(self, -1, _(u"Actions"))
        self.hyper_tout = Hyperlien(self, label=_(u"Tout cocher"), infobulle=_(u"Cliquez ici pour tout cocher"),
                                    URL="tout")
        self.hyper_rien = Hyperlien(self, label=_(u"Tout décocher"), infobulle=_(u"Cliquez ici pour tout décocher"),
                                    URL="rien")
        self.hyper_ajoutArticle = Hyperlien(self, label=_(u"| Ajouter Ligne"), infobulle=_(u"Ajouter un article"), URL="article")
        self.hyper_ajoutCommentaire = Hyperlien(self, label=_(u"| Commentaire"), infobulle=_(u"En Projet : ajouter un commentaire Libre"), URL="commentaire")
        self.bouton_oj = CTRL_Bouton_image.CTRL(self, texte=_(u"Retour\nInscriptions"), cheminImage="Images/32x32/Fleche_gauche.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Aller Vers\nFacturation"), cheminImage="Images/32x32/Fleche_droite.png")
        if self.rw :
            self.bouton_annuler = wx.BitmapButton(self, wx.ID_CANCEL,wx.Bitmap("Images/BoutonsImages/Annuler_L72.png", wx.BITMAP_TYPE_ANY))
        else:
            self.bouton_annuler = wx.BitmapButton(self, wx.ID_CANCEL,wx.Bitmap("Images/BoutonsImages/Retour_L72.png", wx.BITMAP_TYPE_ANY))
        self.ctrl_solde = CTRL_Solde(self)
        self.ctrl_solde.SetSolde(1000)

        self.__set_properties()
        self.__do_layout()

        self.resultsOlv.Bind(wx.EVT_COMMAND_LEFT_CLICK, self.Activated)
        self.resultsOlv.Bind(wx.EVT_LIST_ITEM_SELECTED, self.Selected)
        self.resultsOlv.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.Activated)
        self.resultsOlv.Bind(wx.EVT_TEXT, self.Texte)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOj, self.bouton_oj)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)

        self.CalculSolde()
        self.dataorigine = copy.deepcopy(self.data)
        self.lastBind = "clic"
        self.saisie = False
        self.obj = None
        self.lastObj = None
        # fin de init

    def __set_properties(self):
        if not self.rw :
            self.bouton_ok.Enable(False)
            self.resultsOlv.Enable(False)
            self.hyper_ajoutArticle.Enable(False)
            self.hyper_ajoutCommentaire.Enable(False)
            self.hyper_rien.Enable(False)
            self.hyper_tout.Enable(False)
        self.bouton_ok.SetToolTipString(_(u"Chaîner sur la synthèse famille et la facturation"))
        self.bouton_oj.SetToolTipString(_(u"Retour sur les inscriptions, sans passer par la facturation"))
        self.bouton_annuler.SetToolTipString(_(u"Cliquez ici pour annuler, les modifs du niveau famille"))
        self.ctrl_solde.SetToolTipString(_(u"Ne Saisissez pas le montant ici, mais sur les lignes cochées"))
        self.ctrl_solde.ctrl_solde.SetToolTipString(_(u"Ne Saisissez pas le montant ici, mais sur les lignes cochées"))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        staticsizer_facture = wx.StaticBoxSizer(self.staticbox_facture, wx.VERTICAL)
        grid_sizer_facture = wx.FlexGridSizer(rows=2, cols=1, vgap=1, hgap=10)

        grid_sizer_facture.Add(self.resultsOlvFact, 1, wx.EXPAND, 0)
        grid_sizer_facture.AddGrowableCol(0)
        grid_sizer_facture.AddGrowableRow(0)
        staticsizer_facture.Add(grid_sizer_facture, 1, wx.RIGHT|wx.EXPAND,5)
        grid_sizer_base.Add(staticsizer_facture, 1, wx.EXPAND, 0)

        staticsizer_nonFacture = wx.StaticBoxSizer(self.staticbox_nonFacture, wx.VERTICAL)
        grid_sizer_nonFacture = wx.FlexGridSizer(rows=2, cols=1, vgap=1, hgap=10)

        grid_sizer_nonFacture.Add(self.resultsOlv, 0, wx.EXPAND, 0)
        grid_sizer_nonFacture.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)
        grid_sizer_nonFacture.AddGrowableCol(0)
        grid_sizer_nonFacture.AddGrowableRow(0)
        staticsizer_nonFacture.Add(grid_sizer_nonFacture, 1, wx.RIGHT|wx.EXPAND,5)
        grid_sizer_base.Add(staticsizer_nonFacture, 1, wx.EXPAND, 0)

        pied_staticboxSizer = wx.StaticBoxSizer(self.pied_staticbox, wx.VERTICAL)
        grid_sizer_pied = wx.FlexGridSizer(rows=1, cols=7, vgap=3, hgap=3)

        grid_sizer_cocher = wx.FlexGridSizer(rows=2, cols=1, vgap=1, hgap=10)
        grid_sizer_cocher.Add(self.hyper_tout, 0, wx.ALL, 0)
        grid_sizer_cocher.Add(self.hyper_rien, 0, wx.ALL, 0)
        grid_sizer_pied.Add(grid_sizer_cocher, 1, wx.EXPAND, 0)

        grid_sizer_outils = wx.FlexGridSizer(rows=2, cols=1, vgap=1, hgap=10)
        grid_sizer_outils.Add(self.hyper_ajoutArticle, 0, wx.ALL, 0)
        grid_sizer_outils.Add(self.hyper_ajoutCommentaire, 0, wx.ALL, 0)
        grid_sizer_pied.Add(grid_sizer_outils, 1, wx.EXPAND, 0)

        grid_sizer_pied.Add(self.bouton_oj, 0, 0, 0)
        grid_sizer_pied.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_pied.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_pied.Add(self.ctrl_solde, 0, 0, 0)
        grid_sizer_pied.AddGrowableCol(1)

        pied_staticboxSizer.Add(grid_sizer_pied, 1, wx.EXPAND, 5)        
        grid_sizer_base.Add(pied_staticboxSizer, 1, wx.EXPAND, 5)

        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableRow(2)
        grid_sizer_base.AddGrowableCol(0)
        self.SetMinSize((650, 550))
        self.Layout()
        self.CenterOnScreen()

    def ListeDict(self,olv,):
        # Permet de récupérer le format liste de dictionnaires pour les lignes de la pièce
        objects = olv.GetObjects()
        listeLignesPiece = []
        for obj in objects:
            if olv.IsChecked(obj) == True:
                dictTemp = {}
                dictTemp["codeArticle"]= obj.codeArticle
                dictTemp["libelle"]= obj.libelle
                if obj.qte == None: obj.qte = 1
                if obj.qte == 0: obj.qte = 1
                dictTemp["quantite"]= obj.qte
                dictTemp["prixUnit"]= obj.montantCalcul / obj.qte
                dictTemp["montant"]= obj.montant
                listeLignesPiece.append(dictTemp)
        return listeLignesPiece

    def Final(self):
        self.listeLignesPiece = self.ListeDict(self.resultsOlv)
        fGest = aGestionInscription.Forfaits(self)
        mtt = 0.00
        for ligne in self.listeLignesPiece:
            # calcul du total avec lignes cochées et priorité au montants saisis
            if ligne["montant"] != 0.00:
                mtt += abs(ligne["montant"])
            else: mtt += abs(ligne["quantite"] * ligne["prixUnit"])
        if mtt > 0:
            # enregistrement de la pièce et de ses prolongements prestation
            self.dictDonnees["lignes_piece"] = self.listeLignesPiece
            self.dictDonnees["etat"]="11100"
            # Enregistre dans Pieces
            ret = fGest.ModifiePiece(self,self.dictDonnees)
            # Enregistre la prestation
            IDprestation=self.dictDonnees["IDprestation"]
            if IDprestation != None:
                DB=aGestionDB.DB()
                DB.ReqDEL("prestations", "IDprestation", IDprestation)
            IDprestation = fGest.AjoutPrestation999(self,self.dictDonnees)
            self.dictDonnees["IDprestation"] = IDprestation
            if IDprestation > 0 :
                ret = fGest.ModifiePieceCree(self,self.dictDonnees)
        else:
            # si la piece ne comporte pas de ligne elle est supprimée (contexte piece niveau famille, crée vide préalablement)
            fGest.Suppression(self,self.dictDonnees,1)
        self.EndModal(wx.ID_OK)
        #fin Final

    def OnBoutonOj(self, event):
        self.Final()
        self.Destroy()

    def OnBoutonOk(self, event):
        self.Final()
        #lancer la synthèse
        dlg = aDLG_FacturationPieces.Dialog(self,self.IDcompte_payeur)
        dlg.ShowModal()
        self.Destroy()

    def CocheTout(self, state):
        objects = self.resultsOlv.GetObjects()
        for obj in objects:
            self.resultsOlv.SetCheckState(obj, state)
        self.RazUnchecked()
        self.CalculSolde()
        self.resultsOlv.RefreshObjects(objects)

    def AjouteLigne(self, typeLigne):
        if typeLigne == "article":
            self.listeLignes = []
            # la liste est alimentée par le ok du dlg
            dlg = aDLG_ChoixLigne.DlgChoixArticle(self)
            if dlg.ShowModal() == wx.ID_OK:
                self.ActionAjout(self.listeLignes)

    def ActionAjout(self, listeLignes):
        fOLV = OLVtarification(self, self.IDcompte_payeur,self.saisonDeb, self.saisonFin)
        listeLignesPlus = fOLV.EnrichirDonnees(listeLignes)
        fOLV.Destroy()
        if len(listeLignesPlus)>0:
            for ligne in listeLignesPlus:
                ligne2= copy.deepcopy(ligne)
                self.data.append(ligne)
                self.dataorigine.append(ligne2)
                self.resultsOlv.SetCheckState(ligne, True)
            self.resultsOlv.SetObjects(self.data)
            self.RazUnchecked()
            self.CalculSolde()

    def Texte(self, event):
        if self.lastBind != "texte":
            self.lastObj = copy.deepcopy(self.obj)
            self.lastBind = "texte"

    def Selected(self, event):
        if self.lastBind == "texte":
            objects = self.resultsOlv.GetObjects()
            for obj in objects:
                if obj.codeArticle == self.obj.codeArticle:
                    # une saisie texte a eu lieu le zéro doit désactiver la ligne
                    if obj.montant == 0 and self.lastObj.montant != 0:
                        self.resultsOlv.SetCheckState(obj, False)
        self.obj = copy.deepcopy(self.resultsOlv.GetSelectedObjects()[0])
        self.lastBind = "select"
        self.CalculSolde()

    def Activated(self, event):
        selection = self.resultsOlv.GetSelectedObjects()
        if len(selection)>0:
            obj = selection[0]
            # reprend un montant antérieur si retour d'une coche après décoche
            if self.resultsOlv.IsChecked(obj) == True:
                for objOrigine in self.dataorigine:
                    if objOrigine.codeArticle == obj.codeArticle:
                        obj.prixUnit = objOrigine.prixUnit
        self.CalculSolde()

    def CalculSolde(self):
        objects = self.resultsOlv.GetObjects()
        total, mtt = 0, 0
        aCalc= aGestionArticle.ActionsModeCalcul(self.dictDonnees)
        for obj in objects:
            # les non cochés sont dé-forcés en mettant à zéro le montant mais pas les quantités
            if self.resultsOlv.IsChecked(obj) == False:
                obj.montant = 0.00
                obj.prixUnit = 0.00
                obj.montantCalcul = obj.prixUnit * obj.qte
            # les cochés sont recalculés
            if self.resultsOlv.IsChecked(obj) == True:
                # recalcul des arcticles selon leur mode de calcul.
                obj.montantCalcul = obj.prixUnit * obj.qte
                qte,mtt = aCalc.ModeCalcul(obj,objects)
                if mtt != None:
                    obj.montantCalcul = mtt
                    obj.qte = qte
                # déduction des montants déjà facturés
                for objfac in self.resultsOlvFact.GetObjects():
                    if objfac.codeArticle == obj.codeArticle:
                        obj.montantCalcul -= objfac.montant
                # un forçage au même montant que le résultat du calcul n'est plus un forçage: remis à zéro
                if obj.montant == obj.montantCalcul:
                    obj.montant = 0.00
                # calcul du total avec lignes cochées et priorité au montants saisis
                if obj.montant != 0.00:
                    total += obj.montant
                else: total += (obj.montantCalcul)
            obj.montant = float(obj.montant)
            obj.qte = float(obj.qte)
            obj.montantCalcul = float(obj.montantCalcul)
        self.ctrl_solde.SetSolde(total)

    def RazUnchecked(self):
        objects = self.resultsOlv.GetObjects()
        for obj in objects:
            if self.resultsOlv.IsChecked(obj) == False:
                obj.montant = 0
                obj.prixUnit = 0

    def PreCoche(self):
        objects = self.resultsOlv.GetObjects()
        for obj in objects:
            if obj.force == "NON":
                self.resultsOlv.SetCheckState(obj, False)
                obj.montant = 0.00
            else:
                self.resultsOlv.SetCheckState(obj, True)
            self.resultsOlv.RefreshObjects(objects)

# -------------------------------------------------------------------------------------------------------------------------------------------
class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent):
        wx.SearchCtrl.__init__(self, parent, size=(-1, -1), style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.rechercheEnCours = False

        self.SetDescriptiveText(_(u"Rechercher un Bloc..."))
        self.ShowSearchButton(True)

        self.listView = self.parent.resultsOlv
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

class Hyperlien(Hyperlink.HyperLinkCtrl):
    def __init__(self, parent, id=-1, label="", infobulle="", URL=""):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL)
        self.parent = parent
        self.URL = URL
        self.AutoBrowse(False)

        # SetColours(1,2,3 )1'link':à l'ouverture, 2`visited`: survol avant clic, 3`rollover`: après le clic,
        self.SetColours("BLUE", "BLUE", "PURPLE")

        # SetUnderlines(1,2,3 ) 1'link':`True` underlined(à l'ouverture),2`visited`:'True` underlined(lors du survol avant clic), 3`rollover`:`True` (trace après le clic),
        self.SetUnderlines(False, True, False)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)

    def OnLeftLink(self, event):
        if self.URL == "tout": self.parent.CocheTout(True)
        if self.URL == "rien": self.parent.CocheTout(False)
        if self.URL == "article": self.parent.AjouteLigne("article")
        if self.URL == "commentaire": self.parent.AjouteLigne("commentaire")
        self.UpdateLink()

# --------------------Lancement de test ----------------------
if __name__ == "__main__":
    app = wx.App(0)
    listeDonnees = [
        ("origine", "modif"),
        ("IDindividu", 5325),
        ("IDfamille", 5325),
        ("IDactivite", 221),
        ("IDgroupe", 442),
        ("IDcategorie_tarif", 795),
        ("IDcompte_payeur", 5325),
        ("date_inscription", datetime.date.today()),
        ("parti", False),
        ("nom_activite", "Sejour 41"),
        ("nom_payeur", "ma famille"),
        ("nom_groupe", "Groupe Pasto Plus"),
        ("nom_categorie_tarif", "Tarif Normal"),
        ("nom_individu", "nom de  l'individu"),
        ("lignes_piece", [{'utilisateur': u'NoName', 'quantite': 1, 'montant': 480.5, 'codeArticle': u'SEJ_CORSE_S1', 'libelle': u'Séjour Jeunes Corse S1', 'IDnumPiece': 5, 'prixUnit': 480.0, 'date': u'2016-07-24', 'IDnumLigne': 128}
]),
    ]
    dictDonnees = {}
    for donnee in listeDonnees:
        champ = donnee[0]
        valeur = donnee[1]
        dictDonnees[champ] = valeur

    f = DlgTarification(dictDonnees)
    app.SetTopWindow(f)
    if f.ShowModal() == wx.ID_OK:
        print "OK"
    else:
        print "KC"
    app.MainLoop()
