#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, Jacques Brunel
# Licence:         Licence GNU GPL
# Gestion des compléemnts transports cotisation et réductions famille
# Adapté à partir de DLG_Saisie_transport.Dialog
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import UTILS_Utilisateurs
import CTRL_Bouton_image
import CTRL_Bandeau
import CTRL_Saisie_euros
import aCTRL_Saisie_transport
import aGestionDB

# -----------------------------------------------------------------------------------------------------------------
class DlgTransports(wx.Dialog):
    def __init__(self, dictDonnees):
        wx.Dialog.__init__(self, None, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX|wx.THICK_FRAME)
        self.titre = (u"Gestion des compléments à l'inscription : Transports puis cotisation/réductions")
        self.SetTitle("aDLG_InscriptionComplements")
        self.dictDonnees = dictDonnees
        if dictDonnees["origine"] in ("consult","lecture"):
            self.modeVirtuel = True
        else :
            self.modeVirtuel = False
        droitCreation = UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_inscriptions", "creer")
        if not droitCreation : self.modeVirtuel = True
        self.IDfamille = dictDonnees["IDfamille"]
        self.IDindividu = dictDonnees["IDindividu"]
        self.IDactivite = dictDonnees["IDactivite"]
        self.IDgroupe = dictDonnees["IDgroupe"]
        self.codeNature = None
        self.IDcategorieTarif = dictDonnees["IDcategorie_tarif"]
        ligneInfo = u"Activité: " + dictDonnees["nom_activite"] + " | Groupe: " + dictDonnees["nom_groupe"]+ " | Tarif: " + dictDonnees["nom_categorie_tarif"]
        soustitreFenetre = "Campeur : " + dictDonnees["nom_individu"] + " | Famille : " + dictDonnees["nom_famille"]
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=ligneInfo, texte=soustitreFenetre, hauteurHtml=10,nomImage="Images/22x22/Smiley_nul.png")

        # Contenu
        self.__setData()
        self.staticbox_aller = wx.StaticBox(self, -1, _(u"Transport    ALLER"))
        self.staticbox_retour = wx.StaticBox(self, -1, _(u"Transport    RETOUR"))
        #     self.ctrl_saisie = CTRL_Saisie_transport.CTRL(self, IDtransport=IDtransport, IDindividu=IDindividu, dictDonnees=self.dictDonnees, verrouilleBoutons=verrouilleBoutons)
        self.ctrl_saisie_aller = aCTRL_Saisie_transport.CTRL(self, IDtransport=self.IDtranspAller, IDindividu=self.IDindividu, dictDonnees={}, verrouilleBoutons=self.modeVirtuel)
        self.ctrl_saisie_retour = aCTRL_Saisie_transport.CTRL(self, IDtransport=self.IDtranspRetour, IDindividu=self.IDindividu, dictDonnees={}, verrouilleBoutons=self.modeVirtuel)
        self.label_prixAller = wx.StaticText(self, -1, _(u"Prix du transport ALLER:"))
        self.ctrl_prixAller = CTRL_Saisie_euros.CTRL(self)
        self.label_prixRetour = wx.StaticText(self, -1, _(u"Prix du transport RETOUR:"))
        self.ctrl_prixRetour = CTRL_Saisie_euros.CTRL(self)
        self.ctrl_prixAller.SetValue(str(self.prixTranspAller))
        self.ctrl_prixRetour.SetValue(str(self.prixTranspRetour))

        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_(u"Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Valider"), cheminImage="Images/32x32/Suivant.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Interrompre"), cheminImage="Images/32x32/Annuler.png")

        self.__set_properties()
        self.__do_layout()

    def __setData(self):
        if self.dictDonnees["origine"] in ("ajout",):
            self.IDtranspAller = None
            self.IDtranspRetour = None
            self.prixTranspAller = None
            self.prixTranspRetour = None
        else:
            self.IDtranspAller = self.dictDonnees["IDtranspAller"]
            self.IDtranspRetour = self.dictDonnees["IDtranspRetour"]
            self.prixTranspAller = self.dictDonnees["prixTranspAller"]
            self.prixTranspRetour = self.dictDonnees["prixTranspRetour"]

    def __set_properties(self):
        self.bouton_aide.SetToolTipString(_(u"Cliquez ici pour obtenir de l'aide"))
        self.bouton_ok.SetToolTipString(_(u"Cliquez ici pour valider"))
        self.bouton_annuler.SetToolTipString(_(u"Cliquez ici pour annuler"))
        self.SetMinSize((450, 660))
        if self.modeVirtuel:
            self.ctrl_saisie_aller.Enable(False)
            self.ctrl_saisie_retour.Enable(False)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 1, wx.EXPAND, 0)

        grid_sizer_transports = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)

        staticsizer_aller = wx.StaticBoxSizer(self.staticbox_aller, wx.VERTICAL)
        grid_sizer_aller = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        grid_sizer_aller.Add(self.ctrl_saisie_aller, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        grid_sizer_prix_aller = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        grid_sizer_prix_aller.Add(self.label_prixAller, 0, wx.ALL|wx.ALIGN_TOP, 5)
        grid_sizer_prix_aller.Add(self.ctrl_prixAller, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_prix_aller.AddGrowableCol(1)
        grid_sizer_aller.Add(grid_sizer_prix_aller, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_aller.AddGrowableCol(0)

        staticsizer_aller.Add(grid_sizer_aller, 1, wx.RIGHT|wx.EXPAND,5)

        grid_sizer_transports.Add(staticsizer_aller, 0,wx.ALL|wx.EXPAND, 3)

        staticsizer_retour = wx.StaticBoxSizer(self.staticbox_retour, wx.VERTICAL)
        grid_sizer_retour = wx.FlexGridSizer(rows=2, cols=1, vgap=0, hgap=0)
        grid_sizer_retour.Add(self.ctrl_saisie_retour, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        grid_sizer_prix_retour = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        grid_sizer_prix_retour.Add(self.label_prixRetour, 0, wx.ALL|wx.ALIGN_TOP, 5)
        grid_sizer_prix_retour.Add(self.ctrl_prixRetour, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_prix_retour.AddGrowableCol(1)
        grid_sizer_retour.Add(grid_sizer_prix_retour, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_retour.AddGrowableCol(0)

        staticsizer_retour.Add(grid_sizer_retour, 1, wx.RIGHT|wx.EXPAND,5)

        grid_sizer_transports.Add(staticsizer_retour, 0,wx.ALL|wx.EXPAND, 3)

        grid_sizer_transports.AddGrowableCol(0)
        grid_sizer_transports.AddGrowableCol(1)
        grid_sizer_transports.AddGrowableRow(0)
        grid_sizer_base.Add(grid_sizer_transports, 1,wx.ALL|wx.EXPAND, 3)

        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        grid_sizer_base.AddGrowableCol(0)
        grid_sizer_base.AddGrowableRow(1)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        self.Layout()
        self.CenterOnScreen()

    def OnBoutonAide(self, event):
        import UTILS_Aide
        UTILS_Aide.Aide("Transports1")

    def OnBoutonOk(self, event):
        # Validation des données
        if self.Validation() == False :
            return
        # Fermeture sans sauvegarde
        if self.modeVirtuel == True :
            self.EndModal(wx.ID_OK)
            return
        # Sauvegarde
        resultat = self.ctrl_saisie_aller.Sauvegarde(mode="unique", )
        resultatRetour = self.ctrl_saisie_retour.Sauvegarde(mode="unique", )
        if resultat and resultatRetour == True :
            self.EndModal(wx.ID_OK)
            return
        else:
            msg = aGestionDB.Messages()
            msg.Box(message = u"Problème avec l'enregistrement des transports !")
            self.EndModal(wx.ID_CANCEL)

    def GetDictDonnees(self,dictDonnees):
        dictDonnees["IDtranspAller"] = self.ctrl_saisie_aller.GetIDtransport()
        prix = self.ctrl_prixAller.GetValue()
        if prix != "None": dictDonnees["prixTranspAller"] = float(prix)
        else: dictDonnees["prixTranspAller"] = 0.00
        dictDonnees["IDtranspRetour"] = self.ctrl_saisie_retour.GetIDtransport()
        prix = self.ctrl_prixRetour.GetValue()
        if prix != "None": dictDonnees["prixTranspRetour"] = float(prix)
        else: dictDonnees["prixTranspRetour"] = 0.00
        return dictDonnees

    def Validation(self):
        # Validation de la saisie
        resultatAller = self.ctrl_saisie_aller.Validation()
        resultatRetour = self.ctrl_saisie_retour.Validation()
        resultat = resultatAller and resultatRetour
        return resultat

if __name__ == "__main__":
    app = wx.App(0)
    listeDonnees = [
        ("IDinscription", None),
        ("IDindividu", 6163),
        ("IDfamille", 6163),
        ("origine", "modif"),
        ("etat", "00000"),
        ("IDactivite", 221),
        ("IDgroupe", 442),
        ("IDcategorie_tarif", 795),
        ("IDcompte_payeur", 6163),
        ("date_inscription", "2016-01-01"),
        ("parti", False),
        ("nature", "COM"),
        ("IDtranspAller", 494),
        ("prixTranspAller", 50.50),
        ("IDtranspRetour", 495),
        ("prixTranspRetour", 90.10),
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

    dlg = DlgTransports(dictDonnees)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()