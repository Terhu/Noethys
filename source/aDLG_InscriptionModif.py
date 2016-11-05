#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, Jacques Brunel
# Licence:         Licence GNU GPL
# Gestion de la piece en modifiction
# Adapté à partir de aDLG_ValidationPiece
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import CTRL_Bouton_image
import CTRL_Saisie_euros
import UTILS_Utilisateurs
import datetime
import copy
import DLG_Inscription
import aGestionArticle
import aGestionDB
import aDLG_PrixActivite
import aGestionInscription
import aDLG_ValidationPiece
import aDLG_InscriptionComplements
import CTRL_Bandeau

# -----------------------------------------------------------------------------------------------------------------
class Dialog(wx.Dialog):
    def __init__(self, parent, dictPiece,dictFamillesRattachees):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.THICK_FRAME)
        self.dictDonneesOrigine = dictPiece
        self.dictFamillesRattachees = dictFamillesRattachees
        self.parent = parent
        self.titre = (u"Gestion de la modifiction de la pièce")
        intro = (u"Les pièces transférées en compta ne sont pas modifiables")
        self.SetTitle("aDLG_InscriptionsModif")
        if dictPiece["origine"] in ("consult","lecture"):
            self.rw = False
        else :
            self.rw = True
        if dictPiece["nature"] == "AVO": self.rw = False
        droitModif = UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "modifier")
        if not droitModif : self.rw = False

        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=self.titre, texte=intro,  hauteurHtml=15, nomImage="Images/22x22/Smiley_nul.png")
        self.staticbox_TIERS = wx.StaticBox(self, -1, _(u"Tiers"))
        self.label_individu = wx.StaticText(self, -1, _(u"Individu inscrit :"))
        self.ctrl_nom_individu = wx.TextCtrl(self, -1, "",size=(50, 20))
        self.label_famille = wx.StaticText(self, -1,  _(u"Famille :"))
        self.ctrl_nom_famille = wx.TextCtrl(self, -1, "",size=(50, 20))
        self.bouton_famille = wx.Button(self, -1, "...", size=(20, 20))
        self.label_payeur = wx.StaticText(self, -1, _(u"Tiers payeur :"))
        self.ctrl_nom_payeur = wx.TextCtrl(self, -1, "",size=(50, 20))

        self.staticbox_CAMPgauche = wx.StaticBox(self, -1, _(u"Activite"))
        self.label_activite = wx.StaticText(self, -1, _(u"Activité (hors cotisation et transport):"))
        self.ctrl_nom_activite = wx.TextCtrl(self, -1, "",size=(50, 20))
        self.bouton_activite = wx.Button(self, -1, "...", size=(20, 20))
        self.label_groupe = wx.StaticText(self, -1,  _(u"Groupe :"))
        self.ctrl_nom_groupe = wx.TextCtrl(self, -1, "",size=(50, 20))
        self.label_tarif = wx.StaticText(self, -1, _(u"Catégorie Tarif:"))
        self.ctrl_nom_tarif = wx.TextCtrl(self, -1, "",size=(50, 20))

        self.staticbox_PRIX = wx.StaticBox(self, -1,_(u"Prix de l'activité"))
        self.label_prix1 = wx.StaticText(self, -1, _(u"Actuel :"))
        self.ctrl_prix1 = CTRL_Saisie_euros.CTRL(self)
        self.bouton_prix1 = wx.Button(self, -1, "...", size=(20, 20))
        self.label_prix2 = wx.StaticText(self, -1, _(u"Nouveau :"))
        self.ctrl_prix2 = CTRL_Saisie_euros.CTRL(self)
        self.bouton_prix2 = wx.Button(self, -1, "...", size=(20, 20))

        self.staticbox_PIECEgauche = wx.StaticBox(self, -1, _(u"Pièce"))
        self.label_nature = wx.StaticText(self, -1, _(u"Nature :"))
        self.ctrl_nom_nature = wx.TextCtrl(self, -1, "",size=(150, 20))
        self.bouton_piece = wx.Button(self, -1, "...", size=(20, 20))
        self.label_etat = wx.StaticText(self, -1,  _(u"Etat pièce :"))
        self.ctrl_nom_etat = wx.TextCtrl(self, -1, "",size=(150, 20))

        self.staticbox_CONTENU = wx.StaticBox(self, -1, _(u"Contenu"))
        self.label_commentaire = wx.StaticText(self, -1, _(u"Notes\nmodifiables :"))
        self.txt_commentaire = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE,size = (150,60))
        self.label_infos = wx.StaticText(self, -1, _(u"Infos pièce :"))
        self.choice_infos = wx.Choice(self, -1, choices=[],size = (150,20))
        self.staticbox_BOUTONS= wx.StaticBox(self, -1, )
        if dictPiece["nature"] == "FAC":
            self.bouton_avoir = CTRL_Bouton_image.CTRL(self, texte=_(u"Avoir Piece"), cheminImage="Images/32x32/Places_refus.png")
        else:
            self.bouton_avoir = CTRL_Bouton_image.CTRL(self, texte=_(u" "), cheminImage="Images/32x32/Rectangle.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Valider"), cheminImage="Images/32x32/Suivant.png")
        if self.rw:
            self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Abandon"), cheminImage="Images/32x32/Annuler.png")
        else:
            self.bouton_annuler = wx.BitmapButton(self, wx.ID_CANCEL,wx.Bitmap("Images/BoutonsImages/Retour_L72.png", wx.BITMAP_TYPE_ANY))

        self.__set_data()
        self.__set_properties()
        self.__do_layout()

    def __set_data(self):
        self.modifPrestations = False
        self.modifConsommations = False
        self.modifInscriptions = False
        self.modifPieces = False
        self.dictDonnees = {}
        self.listeNoms = []
        self.listeFamille = []
        #self.dictFamillesRattachees = self.parent.dictFamillesRattachees

        #alimente Choice des listeInfo
        self.listeChamps = sorted(self.dictDonneesOrigine.keys())
        for champ in self.listeChamps:
            self.dictDonnees[champ] = self.dictDonneesOrigine[champ]
            tip = type(self.dictDonneesOrigine[champ])
            if tip in ( str, unicode):
                valeur = self.dictDonneesOrigine[champ].encode('iso-8859-15')
            elif tip in (int, float):
                valeur = str(self.dictDonneesOrigine[champ])
            elif self.dictDonneesOrigine[champ] == None:
                valeur = "  -"
            elif tip == list:
                valeur = str(len(self.dictDonneesOrigine[champ])) +" lignes"
            else:
                valeur = str(tip)
            self.choice_infos.Append(((champ + " :"+ ("_"*25))[:30] + valeur))
        self.choice_infos.Select(16)

        # transposition de la nature et de l'état de la pièce
        self.liste_naturesPieces = copy.deepcopy(aGestionArticle.LISTEnaturesPieces)
        self.liste_codesNaturePiece = []
        for a,b,c in self.liste_naturesPieces: self.liste_codesNaturePiece.append(a)
        self.liste_etatsPieces = copy.deepcopy(aGestionArticle.LISTEetatsPieces)
        #ajout de l'avoir pour usage en lecture seule
        self.liste_naturesPieces.extend(aGestionArticle.LISTEnaturesPiecesFac)
        nature,etat = self.GetNomsNatureEtat(self.dictDonneesOrigine)
        self.ctrl_nom_nature.SetValue(nature)
        self.ctrl_nom_etat.SetValue(etat)

        #Calcul du prix
        prix = 0.00
        listeLignes = self.dictDonneesOrigine["lignes_piece"]
        for dictLigne in listeLignes:
            if dictLigne["montant"]==0:
                prix +=  dictLigne["quantite"] * dictLigne["prixUnit"]
            else: prix += dictLigne["montant"]
        self.ctrl_prix1.SetValue(str("{:10.2f}".format((prix))))
        self.AffichePrix2()
        #Autre elements gérés, appel des données
        self.txt_commentaire.SetValue(self.dictDonneesOrigine["commentaire"])
        self.ctrl_nom_individu.SetValue(self.dictDonneesOrigine["nom_individu"])
        self.ctrl_nom_famille.SetValue(self.dictDonneesOrigine["nom_famille"])
        self.ctrl_nom_payeur.SetValue(self.dictDonneesOrigine["nom_payeur"])
        self.ctrl_nom_activite.SetValue(self.dictDonneesOrigine["nom_activite"])
        self.ctrl_nom_groupe.SetValue(self.dictDonneesOrigine["nom_groupe"])
        self.ctrl_nom_tarif.SetValue(self.dictDonneesOrigine["nom_categorie_tarif"])
        # éléments pour modif
        self.IDindividu = self.dictDonneesOrigine["IDindividu"]
        self.IDfamille = self.dictDonneesOrigine["IDfamille"]
        self.IDpayeur = self.dictDonneesOrigine["IDcompte_payeur"]
        #fin SetData

    def __set_properties(self):
        self.SetMinSize((500, 600))
        self.bouton_famille.SetToolTipString(_(u"Cliquez pour modifier les éléments tiers"))
        self.bouton_activite.SetToolTipString(_(u"Cliquez pour modifier les éléments acitivité"))
        self.bouton_prix1.SetToolTipString(_(u"Cliquez pour consulter la composition du prix"))
        self.bouton_prix2.SetToolTipString(_(u"Cliquez pour modifier la tarification actuelle"))
        self.bouton_piece.SetToolTipString(_(u"Cliquez pour modifier la nature de la pièce, l'état en découle"))
        self.choice_infos.SetToolTipString(_(u"Pour info seulement, contenu du fichier pièce"))
        self.txt_commentaire.SetToolTipString(_(u"Ces infos sont générées automatiquement lors de la création mais vous pouvez les modifier"))
        self.bouton_avoir.SetToolTipString(_(u"L'avoir compense une facture sans la supprimer"))
        self.bouton_ok.SetToolTipString(_(u"Cliquez ici pour valider et fermer"))
        self.bouton_annuler.SetToolTipString(_(u"Cliquez ici pour annuler et fermer"))
        self.ctrl_nom_famille.SetToolTipString(_(u"Cliquez sur le bouton pour modifier les éléments tiers"))
        self.ctrl_nom_payeur.SetToolTipString(_(u"Le payeur est celui de la famille"))
        self.ctrl_nom_activite.SetToolTipString(_(u"Cliquez sur le bouton pour modifier les éléments acitivité"))
        self.ctrl_nom_groupe.SetToolTipString(_(u"Cliquez sur le bouton pour modifier les éléments acitivité"))
        self.ctrl_nom_tarif.SetToolTipString(_(u"Cliquez sur le bouton pour modifier les éléments acitivité"))
        self.ctrl_prix1.SetToolTipString(_(u"Cliquez pour consulter la composition du prix"))
        self.ctrl_prix2.SetToolTipString(_(u"Cliquez sur le bouton pour modifier la tarification actuelle"))
        self.ctrl_nom_nature.SetToolTipString(_(u"Cliquez sur le bouton pour changer la nature de la pièce, l'état en découle"))

        self.Bind(wx.EVT_BUTTON, self.On_famille, self.bouton_famille)
        self.ctrl_nom_famille.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_famille)
        self.Bind(wx.EVT_BUTTON, self.On_activite, self.bouton_activite)
        self.ctrl_nom_activite.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_activite)
        self.ctrl_nom_groupe.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_activite)
        self.ctrl_nom_tarif.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_activite)
        self.Bind(wx.EVT_BUTTON, self.On_prix1, self.bouton_prix1)
        self.Bind(wx.EVT_BUTTON, self.On_prix2, self.bouton_prix2)
        self.ctrl_prix2.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_prix2)
        self.Bind(wx.EVT_BUTTON, self.On_piece, self.bouton_piece)
        self.ctrl_nom_nature.Bind(wx.EVT_SET_FOCUS, self.On_ctrl_nom_nature)
        self.txt_commentaire.Bind(wx.EVT_KILL_FOCUS, self.On_commentaire)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAvoir, self.bouton_avoir)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.label_individu.Enable(False)
        self.label_etat.Enable(False)
        self.ctrl_nom_etat.Enable(False)
        self.ctrl_nom_individu.Enable(False)
        self.ctrl_nom_payeur.Enable(False)
        self.ctrl_prix1.Enable(False)
        self.bouton_famille.Enable(self.rw)
        self.bouton_prix2.Enable(self.rw)
        self.bouton_piece.Enable(self.rw)
        self.bouton_activite.Enable(self.rw)
        self.ctrl_nom_etat.Enable(self.rw)
        self.ctrl_prix2.Enable(self.rw)
        self.ctrl_nom_nature.Enable(self.rw)
        self.ctrl_nom_famille.Enable(self.rw)
        self.ctrl_nom_activite.Enable(self.rw)
        self.ctrl_nom_groupe.Enable(self.rw)
        self.ctrl_nom_tarif.Enable(self.rw)
        self.ctrl_nom_nature.Enable(self.rw)
        self.ctrl_nom_etat.Enable(self.rw)
        if self.dictDonneesOrigine["nature"] in  ("FAC","AVO"):
            self.ctrl_nom_nature.Enable(False)
            self.label_nature.Enable(False)
            self.bouton_piece.Enable(False)
        if self.dictDonneesOrigine["nature"] in  ("FAC"):
                self.bouton_avoir.Enable(True)
        else: self.bouton_avoir.Enable(False)
        #fin _set_properties

    def __do_layout(self):
        gridsizer_BASE = wx.FlexGridSizer(rows=7, cols=1, vgap=0, hgap=0)
        gridsizer_BASE.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        staticsizer_TIERS = wx.StaticBoxSizer(self.staticbox_TIERS, wx.VERTICAL)
        gridsizer_TIERS = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        gridsizer_TIERShaut = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        gridsizer_TIERShaut.Add(self.label_individu, 1, wx.LEFT, 15)
        gridsizer_TIERShaut.Add(self.ctrl_nom_individu, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_TIERShaut.AddGrowableCol(1)
        gridsizer_TIERS.Add(gridsizer_TIERShaut, 1, wx.BOTTOM|wx.EXPAND, 5)

        gridsizer_TIERSbas = wx.FlexGridSizer(rows=2, cols=3, vgap=5, hgap=5)
        gridsizer_TIERSbas.Add(self.label_famille, 1, wx.LEFT, 15)
        gridsizer_TIERSbas.Add(self.ctrl_nom_famille, 1, wx.LEFT|wx.EXPAND, 15)
        gridsizer_TIERSbas.Add(self.bouton_famille, 1, wx.LEFT, 10)
        gridsizer_TIERSbas.Add(self.label_payeur, 1, wx.LEFT, 15)
        gridsizer_TIERSbas.Add(self.ctrl_nom_payeur, 1, wx.LEFT|wx.EXPAND, 15)
        gridsizer_TIERSbas.AddGrowableCol(1)
        gridsizer_TIERS.Add(gridsizer_TIERSbas, 1,wx.BOTTOM|wx.EXPAND, 5)
        gridsizer_TIERS.AddGrowableCol(0)
        staticsizer_TIERS.Add(gridsizer_TIERS, 1, wx.RIGHT|wx.EXPAND,5)
        gridsizer_BASE.Add(staticsizer_TIERS, 1,wx.ALL|wx.EXPAND, 3)

        gridsizer_CAMP = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        staticsizer_CAMPgauche = wx.StaticBoxSizer(self.staticbox_CAMPgauche, wx.VERTICAL)
        gridsizer_CAMPgauche = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        gridsizer_CAMPgauche.Add(self.label_activite, 1, wx.LEFT,15)
        gridsizer_CAMPgauche.Add(self.ctrl_nom_activite, 1, wx.TOP|wx.EXPAND, 0)
        gridsizer_CAMPgauche.Add(self.label_groupe, 1, wx.LEFT, 15)
        gridsizer_CAMPgauche.Add(self.ctrl_nom_groupe, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_CAMPgauche.Add(self.label_tarif, 1, wx.LEFT, 15)
        gridsizer_CAMPgauche.Add(self.ctrl_nom_tarif, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_CAMPgauche.AddGrowableCol(1)
        staticsizer_CAMPgauche.Add(gridsizer_CAMPgauche, 1, wx.RIGHT|wx.EXPAND,10)
        gridsizer_CAMP.Add(staticsizer_CAMPgauche, 1, wx.BOTTOM|wx.EXPAND, 5)

        gridsizer_CAMPdroite = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        gridsizer_CAMPdroite.Add(self.bouton_activite, 1, wx.TOP, 30)
        gridsizer_CAMP.Add(gridsizer_CAMPdroite, 1, wx.ALL, 5)

        gridsizer_CAMP.AddGrowableCol(0)
        gridsizer_BASE.Add(gridsizer_CAMP, 1,wx.ALL|wx.EXPAND, 3)

        staticsizer_PRIX = wx.StaticBoxSizer(self.staticbox_PRIX, wx.VERTICAL)
        gridsizer_PRIX = wx.FlexGridSizer(rows=1, cols=6, vgap=5, hgap=5)
        gridsizer_PRIX.Add(self.label_prix1, 1, wx.LEFT, 10)
        gridsizer_PRIX.Add(self.ctrl_prix1, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_PRIX.Add(self.bouton_prix1, 1, wx.LEFT, 0)
        gridsizer_PRIX.Add(self.label_prix2, 1, wx.LEFT, 10)
        gridsizer_PRIX.Add(self.ctrl_prix2, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_PRIX.Add(self.bouton_prix2, 1, wx.LEFT, 0)
        staticsizer_PRIX.Add(gridsizer_PRIX, 1, wx.RIGHT|wx.EXPAND,0)
        gridsizer_PRIX.AddGrowableCol(1)
        gridsizer_PRIX.AddGrowableCol(4)
        gridsizer_BASE.Add(staticsizer_PRIX, 1,wx.ALL|wx.EXPAND, 3)

        gridsizer_PIECE = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        staticsizer_PIECEgauche = wx.StaticBoxSizer(self.staticbox_PIECEgauche, wx.VERTICAL)
        gridsizer_PIECEgauche = wx.FlexGridSizer(rows=3, cols=2, vgap=5, hgap=5)
        gridsizer_PIECEgauche.Add(self.label_nature, 1, wx.LEFT,15)
        gridsizer_PIECEgauche.Add(self.ctrl_nom_nature, 1, wx.TOP, 0)
        gridsizer_PIECEgauche.Add(self.label_etat, 1, wx.LEFT, 15)
        gridsizer_PIECEgauche.Add(self.ctrl_nom_etat, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_PIECEgauche.AddGrowableCol(1)
        staticsizer_PIECEgauche.Add(gridsizer_PIECEgauche, 1, wx.RIGHT|wx.EXPAND,10)
        gridsizer_PIECE.Add(staticsizer_PIECEgauche, 1, wx.BOTTOM|wx.EXPAND, 5)
        gridsizer_PIECEdroite = wx.FlexGridSizer(rows=1, cols=1, vgap=5, hgap=5)
        gridsizer_PIECEdroite.Add(self.bouton_piece, 1, wx.TOP, 15)
        gridsizer_PIECE.Add(gridsizer_PIECEdroite, 1, wx.ALL, 5)
        gridsizer_PIECE.AddGrowableCol(0)
        gridsizer_BASE.Add(gridsizer_PIECE, 1,wx.ALL|wx.EXPAND, 3)

        staticsizer_CONTENU = wx.StaticBoxSizer(self.staticbox_CONTENU, wx.VERTICAL)
        gridsizer_CONTENU = wx.FlexGridSizer(rows=2, cols=2, vgap=5, hgap=5)
        gridsizer_CONTENU.Add(self.label_commentaire, 1, wx.LEFT, 10)
        gridsizer_CONTENU.Add(self.txt_commentaire, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_CONTENU.Add(self.label_infos, 1, wx.LEFT, 10)
        gridsizer_CONTENU.Add(self.choice_infos, 1, wx.LEFT|wx.EXPAND, 0)
        gridsizer_CONTENU.AddGrowableCol(1)
        staticsizer_CONTENU.Add(gridsizer_CONTENU, 1, wx.RIGHT|wx.EXPAND,0)
        gridsizer_BASE.Add(staticsizer_CONTENU, 1,wx.ALL|wx.EXPAND, 3)

        gridsizer_BOUTONS = wx.FlexGridSizer(rows=1, cols=5, vgap=10, hgap=10)
        staticsizer_BOUTONS = wx.StaticBoxSizer(self.staticbox_BOUTONS, wx.VERTICAL)
        gridsizer_BOUTONS.Add(self.bouton_avoir, 0, 0, 0)
        gridsizer_BOUTONS.Add((15, 15), 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_ok, 0, 0, 0)
        gridsizer_BOUTONS.Add(self.bouton_annuler, 0, 0, 0)
        gridsizer_BOUTONS.AddGrowableCol(1)
        staticsizer_BOUTONS.Add(gridsizer_BOUTONS, 1, wx.RIGHT|wx.EXPAND, 10)
        gridsizer_BASE.Add(staticsizer_BOUTONS, 1, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        self.SetSizer(gridsizer_BASE)
        gridsizer_BASE.Fit(self)
        gridsizer_BASE.AddGrowableRow(5)
        gridsizer_BASE.AddGrowableCol(0)
        self.Layout()
        self.CentreOnScreen()
        #fin do_layout

    def GetNomsNatureEtat(self,dictDonnees):
        nature, etat = "",""
        IDnature,i = 0,0
        self.naturePiece = dictDonnees["nature"]
        for a,b,c in self.liste_naturesPieces:
            if a == self.naturePiece:
                nature = b
                IDnature=i
            i+=1
        codeEtat = dictDonnees["etat"][IDnature]
        for a,b,c in self.liste_etatsPieces:
            if a == codeEtat: etat = dictDonnees["etat"]+" "+b+" : "+ c
        return nature, etat
        #fin GetNomsNatureEtat

    def AffichePrix2(self):
        prix = 0.00
        listeLignes = self.dictDonnees["lignes_piece"]
        for dictLigne in listeLignes:
            if dictLigne["montant"] == 0:
                prix +=  dictLigne["quantite"] * dictLigne["prixUnit"]
            else: prix += dictLigne["montant"]
        self.ctrl_prix2.SetValue(str("{:10.2f}".format((prix))))
        if self.dictDonnees["nature"] == "AVO":
            self.ctrl_prix2.SetValue("0")

    def On_ctrl_famille(self, event):
            self.ctrl_nom_famille.Enable(False)
            msg = aGestionDB.Messages()
            msg.Box(message = u"Pour modifier les éléments de la famille il faut passer par le bouton plus à droite !")

    def On_ctrl_nom_nature(self, event):
            self.ctrl_nom_nature.Enable(False)
            msg = aGestionDB.Messages()
            msg.Box(message = u"Pour modifier l'état de la pièce il faut passer par le bouton plus à droite !")

    def On_ctrl_activite(self, event):
            self.ctrl_nom_activite.Enable(False)
            self.ctrl_nom_groupe.Enable(False)
            self.ctrl_nom_tarif.Enable(False)
            msg = aGestionDB.Messages()
            msg.Box(message = u"Pour modifier les éléments de l'activité il faut passer par le bouton plus à droite !")

    def On_ctrl_prix2(self, event):
            self.ctrl_prix2.Enable(False)
            msg = aGestionDB.Messages()
            msg.Box(message = u"Pour modifier les éléments de prix il faut passer par le bouton plus à droite !")

    def On_famille(self, event):
        self.ctrl_nom_famille.Enable(True)
        self.nom_famille = ""
        fGest = aGestionInscription.Forfaits(self.parent)
        #dlg = DLG_Inscription.Dialog(self)
        appel = fGest.GetFamille(self)
        if not appel:
            msg = aGestionDB.Messages()
            msg.Box(message = u"Pour ajouter des familles associées à un individu il faut entrer dans la famille manquante et créer des rattachements !")
            msg.Destroy()
            return
        self.IDcompte_payeur = fGest.GetPayeurFamille(self,self.IDfamille)
        DB = aGestionDB.DB()
        self.nom_payeur = DB.GetNomIndividu( self.IDcompte_payeur)
        DB.Close()
        self.ctrl_nom_famille.SetValue(self.nom_famille)
        self.ctrl_nom_payeur.SetValue(self.nom_payeur)
        commentaire = self.dictDonnees["commentaire"]
        commentaire = str(datetime.date.today()) + u" Famille : " + self.nom_famille + "\n" + commentaire
        self.listeDonnees = [
            ("IDfamille", self.IDfamille ),
            ("IDcompte_payeur", self.IDcompte_payeur),
            ("nom_famille", self.nom_famille),
            ("nom_payeur", self.nom_payeur),
            ]
        self.dictDonnees = fGest.ModifDictDonnees(self,self.listeDonnees)
        self.modifPrestations = True
        self.modifConsommations = True
        self.modifInscriptions = True
        self.modifPieces = True

    def On_activite(self, event):
        self.ctrl_nom_activite.Enable(True)
        self.ctrl_nom_groupe.Enable(True)
        self.ctrl_nom_tarif.Enable(True)
        fGest = aGestionInscription.Forfaits(self.parent)
        # Ouverture de la fenêtre d'inscription choix de l'activité, groupe, catTarif
        dlg = DLG_Inscription.Dialog(self)
        dlg.SetFamille(self.listeNoms, self.listeFamille, self.IDfamille, False)
        choixInscription = dlg.ShowModal()
        if choixInscription != wx.ID_OK:
            dlg.Destroy()
            return
        IDgroupe =  dlg.GetIDgroupe()
        IDcategorie_tarif = dlg.GetIDcategorie()
        if IDgroupe == None or IDcategorie_tarif == None :
            aGestionDB.MessageBox(self,u"Pour une inscription il faut préciser une activité, un groupe et une catégorie de tarif!\nIl y a aussi la possibilité de facturer sans inscription")
            dlg.Destroy()
            return
        nom_activite = dlg.GetNomActivite()
        nom_groupe = dlg.GetNomGroupe()
        nom_categorie = dlg.GetNomCategorie()
        self.ctrl_nom_activite.SetValue(nom_activite)
        self.ctrl_nom_groupe.SetValue(nom_groupe)
        self.ctrl_nom_tarif.SetValue(nom_categorie)
        self.IDactivite = dlg.GetIDactivite()
        self.IDcompte_payeur = fGest.GetPayeurFamille(self,self.IDfamille)
        commentaire = self.dictDonnees["commentaire"]
        commentaire = str(datetime.date.today()) + u" Modifié: " + nom_activite + "-" + nom_groupe + "\n" + commentaire
        self.listeDonnees = [
            ("IDactivite", self.IDactivite),
            ("IDgroupe", IDgroupe),
            ("IDcategorie_tarif", IDcategorie_tarif),
            ("commentaire", commentaire),
            ]
        self.txt_commentaire.SetValue(commentaire)
        self.dictDonnees = fGest.ModifDictDonnees(self,self.listeDonnees)
        self.modifPrestations = True
        self.modifConsommations = True
        self.modifInscriptions = True
        self.modifPieces = True

    def On_prix1(self, event):
        origine = self.dictDonneesOrigine["origine"]
        self.dictDonneesOrigine["origine"]= "lecture"
        fTar = aDLG_PrixActivite.DlgTarification(self,self.dictDonneesOrigine)
        fTar.ShowModal()
        self.dictDonneesOrigine["origine"]= origine

    def On_prix2(self, event):
        # récupération des lignes de l'inscription génération de la piece
        self.dictDonnees["origine"]= "modif"
        fTar = aDLG_PrixActivite.DlgTarification(self,self.dictDonnees)
        tarification = fTar.ShowModal()
        if not(tarification == wx.ID_OK): return
        etatPiece = self.dictDonneesOrigine["etat"]
        listeLignesPiece = fTar.listeLignesPiece
        #la nature de pièce a changé
        if (self.naturePiece != fTar.codeNature) and (fTar.codeNature != None):
            self.naturePiece = fTar.codeNature
            self.dictDonnees["nature"] = self.naturePiece
            i = self.liste_codesNaturePiece.index(self.naturePiece)
            # Mise à "1" du caractère en la position correspondant à la nature de la pièce (ex: FAC = 4eme)
            etatPiece = etatPiece[:i]+"1"+ etatPiece[i+1:]
            self.dictDonnees["etat"] = etatPiece
            nature, etat = self.GetNomsNatureEtat(self.dictDonnees)
            self.ctrl_nom_nature.SetValue(nature)
            self.ctrl_nom_etat.SetValue(etat)
            commentaire = self.dictDonnees["commentaire"]
            commentaire = str(datetime.date.today()) + u" Nature: " + nature + "\n" + commentaire
            self.dictDonnees["commentaire"] = commentaire
            self.txt_commentaire.SetValue(commentaire)
        #si le montant a changé
        if self.dictDonnees["lignes_piece"] != listeLignesPiece:
            self.dictDonnees["lignes_piece"] = listeLignesPiece
            self.AffichePrix2()
            commentaire = self.dictDonnees["commentaire"]
            commentaire = str(datetime.date.today()) + u" Montant modifié "+ "\n" + commentaire
            self.dictDonnees["commentaire"] = commentaire
            self.txt_commentaire.SetValue(commentaire)
        # récup parrainage
        self.dictDonnees["IDparrain"] = fTar.IDparrain
        self.dictDonnees["parrainAbandon"] = fTar.parrainAbandon
        self.modifPrestations = True
        self.modifPieces = True

    def On_piece(self, event):
        fGest = aGestionInscription.Forfaits(self.parent)
        self.ctrl_nom_nature.Enable(True)
        interroChoix = wx.ID_CANCEL
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer")  :
            dlg = aDLG_ValidationPiece.Dialog(self,"modif")
            interroChoix = dlg.ShowModal()
            self.codeNature = dlg.codeNature
            #dlg.Destroy()
        if interroChoix != wx.ID_OK :
            return
        etatPiece = self.dictDonnees["etat"]
        i = self.liste_codesNaturePiece.index(self.codeNature)
        # Mise à "1" du caractère en la position correspondant à la nature de la pièce (ex: FAC = 4eme)
        etatPiece = etatPiece[:i]+"1"+ etatPiece[i+1:]
        self.dictDonnees["etat"] = etatPiece
        commentaire = self.dictDonnees["commentaire"]
        commentaire = str(datetime.date.today()) + u" Nature: " + self.codeNature + "\n" + commentaire
        self.dictDonnees["commentaire"] = commentaire
        self.txt_commentaire.SetValue(commentaire)
        self.listeDonnees = [
            ("nature", self.codeNature),
            ("etat", etatPiece),
            ]
        self.dictDonnees = fGest.ModifDictDonnees(self,self.listeDonnees)
        nature,etat = self.GetNomsNatureEtat(self.dictDonnees)
        self.ctrl_nom_nature.SetValue(nature)
        self.ctrl_nom_etat.SetValue(etat)
        self.modifPrestations = True
        self.modifConsommations = True
        self.modifPieces = True
        #fin OnPiece

    def On_commentaire(self, event):
        fGest = aGestionInscription.Forfaits(self.parent)
        self.listeDonnees = [
            ("commentaire", self.txt_commentaire.GetValue()),
            ]
        self.dictDonnees = fGest.ModifDictDonnees(self,self.listeDonnees)        
        self.modifPieces = True

    def GenereAvoir(self):
        # Création d'une facture d'avoir sur la pièce facturée
        fGest = aGestionInscription.Forfaits(self)
        # Calcul des champs de la table facture
        activites,individus = [],[]
        activites.append(self.dictDonnees["IDactivite"])
        individus.append(self.dictDonnees["IDindividu"])
        def listeChaine(maListe):
            chaine = ""
            for item in maListe:
                chaine = chaine + str(item) +";"
            chaine = chaine[:-1]
            return chaine
        numero = aGestionInscription.GetNoFactureSuivant()
        DB = aGestionDB.DB()
        self.user = DB.UtilisateurActuel()
        montant = -float(self.ctrl_prix2.GetValue())
        # Composition de l'enregistrement facture
        listeDonnees = [
            ("numero",numero ),
            ("IDcompte_payeur", self.IDpayeur),
            ("date_edition", datetime.date.today()),
            ("date_echeance", str(datetime.date.today()+datetime.timedelta(days=30))),
            ("IDutilisateur", self.user),
            ("IDlot", 2),
            ("prestations", "avoir"),
            ("etat", None),
            ("activites",listeChaine(activites)),
            ("individus",listeChaine(individus)),
            ("date_debut",datetime.date.today()),
            ("date_fin",datetime.date.today()),
            ("total",montant),
            ("regle",0.0),
            ("solde",montant),
            ]
        retour = DB.ReqInsert("factures", listeDonnees,retourID = True)
        self.IDnumAvoir = DB.newID
        DB.Close()
        if retour != "ok" :
            aGestionDB.MessageBox(self,retour)
            return None
        self.dictDonnees["noAvoir"] = numero
        self.dictDonnees["etat"] = self.dictDonnees["etat"][0:4]+"1"
        commentaire = self.dictDonnees["commentaire"]
        commentaire = str(datetime.date.today()) + u" Génération Avoir Piece" + "\n" + commentaire
        self.dictDonnees["commentaire"] = commentaire
        # Ecriture du numéro d'avoir dans la piece
        fGest = aGestionInscription.Forfaits(self)
        fGest.MajNoAvoir(self,self.dictDonnees)
        #fin GenereAvoir

    def OnBoutonAvoir(self,event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("familles_factures", "creer")  :
            interroChoix = wx.ID_OK
        if interroChoix != wx.ID_OK :
            return
        msg = aGestionDB.Messages()
        interroChoix,texte = msg.Choix(listeTuples=[(1,"Je souhaite un avoir limité à cette pièce et conserver la facture et l'inscription"),(2,"NON J'abandonne")], titre = u"Un avoir sur pièce n'annule pas les autres pièces de la même facture \nA utiliser quand la facture ne peut pas être supprimée par l'inscription ou la gestion des factures ?", intro = u"Confirmation")
        if interroChoix == None : interroChoix = 2
        if interroChoix !=1 :
            return
        interroChoix = wx.ID_CANCEL
        # generation de l'avoir dans les tables factures et pièces
        self.GenereAvoir()
        #generation d'une prestation avoir
        IDprestation = self.dictDonnees["IDprestation"]
        DB = aGestionDB.DB()
        if IDprestation != None:
            retour = DB.ReqSelect("prestations", "IDprestation = %s ;"% IDprestation)
            if retour != "ok" :
                aGestionDB.MessageBox(self,retour)
            retour = DB.ResultatReq()
            retour[0][3] = datetime.date.today()
            retour[0][6] = -float(retour[0][6])
            retour[0][5] = -float(retour[0][5])
            retour[0][4] = "Avoir "+ retour[0][3]
            retour[0][9] = self.IDnumAvoir
            ret = DB.ReqInsert("prestations",retour,retourID=False)
        # Suppression consommations et ventilations
        IDinscription = self.dictDonnees["IDinscription"]
        if IDinscription != None:
            DB.ReqDEL("consommations", "IDinscription", IDinscription)
        DB.ReqDEL("deductions", "IDprestation", IDprestation)
        DB.ReqDEL("ventilation", "IDprestation", IDprestation)
        DB.Close
        self.txt_commentaire.SetValue(self.dictDonnees["commentaire"])
        nature,etat = self.GetNomsNatureEtat(self.dictDonnees)
        self.rw = False
        self.__set_data()
        self.__set_properties()
        self.ctrl_nom_etat.SetValue(etat)
        self.bouton_ok.Enable(False)
        #self.Destroy()
        #fin OnBoutonAvoir

    def OnBoutonOk(self, event):
        fGest = aGestionInscription.Forfaits(self)
        
        # Gestion des compléments de facturation
        fTransp = aDLG_InscriptionComplements.DlgTransports(self.dictDonnees)
        transports = fTransp.ShowModal()
        self.dictDonnees = fTransp.GetDictDonnees(self.dictDonnees)
        if transports != wx.ID_OK:
            aGestionDB.MessageBox(self, u"Vous n'avez pas géré les transports !\nIls restent en l'état antérieur")
            self.dictDonnees["prixTranspAller"] = self.dictDonneesOrigine["prixTranspAller"]
            self.dictDonnees["prixTranspRetour"] = self.dictDonneesOrigine["prixTranspRetour"]
        fTransp.Destroy()
        if (self.dictDonnees["prixTranspAller"],self.dictDonnees["prixTranspRetour"]) != (self.dictDonneesOrigine["prixTranspAller"],self.dictDonneesOrigine["prixTranspRetour"]):
            self.modifPieces = True
            self.modifPrestations = True

        # Enregistre l'inscription façon noethys
        if self.modifInscriptions == True:
            fGest.ModifieInscription(self,self.dictDonnees)

        # Enregistre dans Pieces
        if self.modifPieces == True:
            fGest.ModifiePiece(self,self.dictDonnees)

        # Suppression consommations et prestations avant reconstitution éventuelle
        DB = aGestionDB.DB()
        if self.modifConsommations == True:
            IDinscription = self.dictDonnees["IDinscription"]
            if IDinscription != None:
                DB.ReqDEL("consommations", "IDinscription", IDinscription)
        if self.modifPrestations == True:
            IDprestation = self.dictDonnees["IDprestation"]
            if IDprestation != None:
                DB.ReqDEL("prestations", "IDprestation", IDprestation)
                DB.ReqDEL("deductions", "IDprestation", IDprestation)
                DB.ReqDEL("ventilation", "IDprestation", IDprestation)
        DB.Close()
        # arret du traitement si seulement devis
        if self.naturePiece == "DEV":
            self.EndModal(wx.ID_OK)
            self.Destroy()
            return
            # Enregistre les consommations
        if self.modifConsommations == True:
            ajout = fGest.AjoutConsommations(self,self.dictDonnees)
            if not ajout :
                self.dictDonnees["nature"] = "DEV"
                id = fGest.ModifiePieceCree(self,self.dictDonnees)
                self.EndModal(wx.ID_OK)
                self.Destroy()
                return
        # arret du traitement si seulement réservation
        if self.naturePiece not in ("COM","FAC","AVO"):
            self.EndModal(wx.ID_OK)
            self.Destroy()
            return
        # Enregistre la prestation
        if self.modifPrestations == True:
            IDprestation = fGest.AjoutPrestation(self,self.dictDonnees)
            self.dictDonnees["IDprestation"] = IDprestation
            if IDprestation > 0 :
                fGest.ModifiePieceCree(self,self.dictDonnees)
                fGest.ModifieConsoCree(self,self.dictDonnees)
        self.EndModal(wx.ID_OK)
        self.Destroy()
        #fin OnBouttonOk

if __name__ == "__main__":
    app = wx.App(0)
    listeDonnees = [
        ("IDinscription",6938),
        ("IDindividu", 13481),
        ("IDfamille", 5325),
        ("origine", "lecture"),
        ("etat", "00000"),
        ("IDactivite", 221),
        ("IDgroupe", 442),
        ("IDcategorie_tarif", 795),
        ("IDcompte_payeur", 6163),
        ("date_inscription", "2016-01-01"),
        ("parti", False),
        ("nature", "COM"),
        ("nom_activite", "Sejour 41 Mon activite"),
        ("nom_groupe", "Groupe Pasto Plus"),
        ("nom_payeur", "celui qui paye"),
        ("nom_categorie_tarif", "Tarif Normal"),
        ("nom_individu", "nom de  l'individu"),
        ("commentaire", "differents commentaires"),
        ("nom_famille", "nom de la famille"),
        ("lignes_piece",[{'utilisateur': u'NoName', 'quantite': 1.0, 'montant': 800.0, 'codeArticle': u'SEJ_CORSE_S1', 'libelle': u'Sejour Jeunes Corse S1', 'IDnumPiece': 10, 'prixUnit': 500.0, 'date': u'2016-07-27', 'IDnumLigne': 190}, {'utilisateur': u'NoName', 'quantite': 1.0, 'montant': 10.0, 'codeArticle': u'ZLUN', 'libelle': u'Option lunettes de soleil', 'IDnumPiece': 10, 'prixUnit': 10.0, 'date': u'2016-07-27', 'IDnumLigne': 191}, {'utilisateur': u'NoName', 'quantite': 1.0, 'montant': 90.0, 'codeArticle': u'ART4', 'libelle': u'Quatrieme article', 'IDnumPiece': 10, 'prixUnit': 90.0, 'date': u'2016-07-27', 'IDnumLigne': 192}]),
        ]
    dictDonnees = {}
    listeChamps = []
    listeValeurs = []
    for donnee in listeDonnees:
        champ = donnee[0]
        valeur = donnee[1]
        dictDonnees[champ] = valeur
        listeChamps.append(champ)
        listeValeurs.append(valeur)
    dlg = Dialog(None,dictDonnees,None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()