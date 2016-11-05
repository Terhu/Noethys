#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, Jacques BRUNEL
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
# gére l'édition proforma à partir des pièces regroupées sur numero de facture
# et prend les lignes pièces au lieu des prestations
#------------------------------------------------------------------------

from UTILS_Traduction import _
import wx
import CTRL_Bouton_image
import datetime
import copy
import sys
import traceback
import wx.lib.agw.pybusyinfo as PBI
import UTILS_Conversion
import UTILS_Config
import DATA_Civilites as Civilites
import FonctionsPerso
import UTILS_Titulaires
import UTILS_Questionnaires
import UTILS_Dates
import DLG_Apercu_facture
import aUTILS_Infos_individus
import aUTILS_Impression_facture
import aGestionInscription
import aGestionDB
from UTILS_Decimal import FloatToDecimal as FloatToDecimal

SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", u"€")
MONNAIE_SINGULIER = UTILS_Config.GetParametre("monnaie_singulier", _(u"Euro"))
MONNAIE_DIVISION = UTILS_Config.GetParametre("monnaie_division", _(u"Centime"))
DICT_CIVILITES = Civilites.GetDictCivilites()

def DateEngEnDateDD(dateEng):
    if dateEng == None or dateEng == "" : return ""
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DateEngFr(textDate):
    text = str(textDate[8:10]) + u"/" + str(textDate[5:7]) + u"/" + str(textDate[:4])
    return text

class Facturation():
    def __init__(self):
        #préparation des conteneurs d'initialisation
        self.dictIndividus = {}
        self.dictMessageFamiliaux = {}
        self.dictOrganisme = {}
        self.listeAgrements = []
        self.infosIndividus = {}
        # " Get noms Titulaires"
        #self.dictNomsTitulaires = UTILS_Titulaires.GetTitulaires()
        # " Récupération des questionnaires"
        self.Questionnaires = UTILS_Questionnaires.ChampsEtReponses(type="famille")
        # "fin __init__"

    def RechercheAgrement(self, IDactivite, date):
        for IDactiviteTmp, agrement, date_debut, date_fin in self.listeAgrements :
            if IDactivite == IDactiviteTmp and date >= date_debut and date <= date_fin :
                return agrement
        return None

    def Supprime_accent(self, texte):
        liste = [ (u"é", u"e"), (u"è", u"e"), (u"ê", u"e"), (u"ë", u"e"), (u"ä", u"a"), (u"à", u"a"), (u"û", u"u"), (u"ô", u"o"), (u"ç", u"c"), (u"î", u"i"), (u"ï", u"i"), (u"/", u""), (u"\\", u""), ]
        for a, b in liste :
            texte = texte.replace(a, b)
            texte = texte.replace(a.upper(), b.upper())
        return texte

    def EcritStatusbar(self, texte=u""):
        try :
            topWindow = wx.GetApp().GetTopWindow() 
            topWindow.SetStatusText(texte)
        except : 
            pass
    
    def RemplaceMotsCles(self, texte="", dictValeurs={}):
        for key, valeur, in dictValeurs.iteritems() :
            if key in texte :
                texte = texte.replace(key, valeur)
        return texte

    def GetInfos(self):
        #  Ancien __init__, pour récupération de toutes les données de base, filtré sur conditions
        DB = aGestionDB.DB()
        # Récupération de tous les individus de la base
        if len(self.listeIndividus) == 1:
            condition = "WHERE IDindividu in (%s) " % str(self.listeIndividus[0])
        elif len(self.listeIndividus) == 0:
            condition = "WHERE IDindividu = 0 "
        else:
            condition = "WHERE IDindividu in ("
            for ind in self.listeIndividus:
                condition += str(ind) +','
            condition = condition[:-1]+") "

        req = """SELECT IDindividu, IDcivilite, nom, prenom, date_naiss, adresse_auto, rue_resid, cp_resid, ville_resid
        FROM individus %s;""" % condition
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            Msg = aGestionDB.Messages()
            Msg.Box( message= retour)
            Msg.Close()
            return None
        listeIndividus = DB.ResultatReq()
        for IDindividu, IDcivilite, nom, prenom, date_naiss, adresse_auto, rue_resid, cp_resid, ville_resid in listeIndividus :
            self.dictIndividus[IDindividu] = {"IDcivilite":IDcivilite, "nom":nom, "prenom":prenom, "date_naiss":date_naiss, "adresse_auto":adresse_auto, "rue_resid":rue_resid, "cp_resid":cp_resid, "ville_resid":ville_resid}

        # Récupération de tous les messages familiaux à afficher
        req = """SELECT IDmessage, IDcategorie, date_parution, priorite, IDfamille, nom, texte
        FROM messages
        WHERE afficher_facture=1 AND IDfamille IS NOT NULL;"""
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            msg = aGestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        listeMessagesFamiliaux = DB.ResultatReq()
        for IDmessage, IDcategorie, date_parution, priorite, IDfamille, nom, texte in listeMessagesFamiliaux :
            date_parution = UTILS_Dates.DateEngEnDateDD(date_parution)
            if self.dictMessageFamiliaux.has_key(IDfamille) == False :
                self.dictMessageFamiliaux[IDfamille] = []
            self.dictMessageFamiliaux[IDfamille].append({"IDmessage":IDmessage, "IDcategorie":IDcategorie, "date_parution":date_parution, "priorite":priorite, "nom":nom, "texte":texte})

        # Récupération des infos sur l'organisme
        req = """SELECT nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape
        FROM organisateur
        WHERE IDorganisateur=1;"""
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            msg = aGestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        listeDonnees = DB.ResultatReq()
        for nom, rue, cp, ville, tel, fax, mail, site, num_agrement, num_siret, code_ape in listeDonnees :
            self.dictOrganisme["nom"] = nom
            self.dictOrganisme["rue"] = rue
            self.dictOrganisme["cp"] = cp
            if ville != None : ville = ville.capitalize()
            self.dictOrganisme["ville"] = ville
            self.dictOrganisme["tel"] = tel
            self.dictOrganisme["fax"] = fax
            self.dictOrganisme["mail"] = mail
            self.dictOrganisme["site"] = site
            self.dictOrganisme["num_agrement"] = num_agrement
            self.dictOrganisme["num_siret"] = num_siret
            self.dictOrganisme["code_ape"] = code_ape

        # Get noms Titulaires
        self.dictNomsTitulaires = UTILS_Titulaires.GetTitulaires(self.listeFamilles)

        # Recherche des numéros d'agréments
        if len(self.listeActivites) == 1:
            conditionActivites = "WHERE IDactivite in (%s) " % str(self.listeActivites[0])
        else:
            conditionActivites = "WHERE IDactivite in ( "
            for ind in self.listeActivites:
                conditionActivites += str(ind) +','
            conditionActivites = conditionActivites[:-1]+") "

        req = """SELECT IDactivite, agrement, date_debut, date_fin
        FROM agrements %s
        ORDER BY date_debut;""" % conditionActivites
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            msg = aGestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        self.listeAgrements = DB.ResultatReq()
        DB.Close()

        # Récupération des questionnaires
        self.Questionnaires = UTILS_Questionnaires.ChampsEtReponses(type="famille")

        # Récupération des infos de base familles
        self.infosIndividus = aUTILS_Infos_individus.Informations(conditionIndividus=condition)

        #fin GetInfos

    def GetDonnees(self, listeFactures=[], date_debut=None, date_fin=None, date_edition=None, date_echeance=None, prestations=["consommation", "cotisation", "autre"], typeLabel=0):
        """ Recherche des factures à créer """
        dictFactures = {}
        for dictTemp in listeFactures :
            dictFactures[dictTemp["numero"]] = dictTemp

        # Recherche des prestations recomposées par les lignes des pièces
        DB = aGestionDB.DB()
        conditions = " WHERE matPieces.pieIDnumPiece in (" + str(self.listeIDnumPieces)[1:-1] + ") "
        req =   """
                SELECT matPieces.pieIDnumPiece, matPieces.pieIDprestation, matPieces.pieIDcompte_payeur, matPieces.pieNoFacture, matPieces.pieDateModif, 
                    prestations.categorie, matPiecesLignes.ligLibelle, matPiecesLignes.ligQuantite, matPiecesLignes.ligPrixUnit, matPiecesLignes.ligMontant,
                    prestations.tva, matPieces.pieIDactivite,matPieces.pieIDgroupe, activites.nom, activites.abrege, activites.date_debut, activites.date_fin,
                    prestations.IDfacture, matPieces.pieIDindividu, matPieces.pieIDfamille, matBlocsFactures.lfaOrdre, matPiecesLignes.ligIDnumLigne,
                    matPieces.piePrixTranspAller, matPieces.piePrixTranspRetour
                FROM matPieces
                INNER JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece
                LEFT JOIN prestations ON matPieces.pieIDprestation = prestations.IDprestation
                LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
                LEFT JOIN matArticles ON matPiecesLignes.ligCodeArticle = matArticles.artCodeArticle
                LEFT JOIN matBlocsFactures ON matArticles.artCodeBlocFacture = matBlocsFactures.lfaCodeBlocFacture
                 %s GROUP BY matPieces.pieIDnumPiece, matPieces.pieIDprestation, matPieces.pieIDcompte_payeur, matPieces.pieDateModif, prestations.categorie, matPiecesLignes.ligLibelle, matPiecesLignes.ligPrixUnit, matPiecesLignes.ligMontant, prestations.tva, matPieces.pieIDactivite, activites.nom, activites.abrege, activites.date_fin,activites.date_fin, prestations.IDfacture, matPieces.pieIDindividu, matPieces.pieIDfamille, matBlocsFactures.lfaOrdre, matPiecesLignes.ligIDnumLigne
                ORDER BY matPieces.pieIDnumPiece, matPieces.pieDateModif, matPiecesLignes.ligIDnumLigne
                ;""" % conditions
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            msg = aGestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        listePrestations = DB.ResultatReq()
        champsPrestations=["IDnumPiece","IDprestation", "IDcompte_payeur", "numero", "date", "categorie", "label","quantite", "prixUnit",
                           "montant", "tva", "IDactivite","IDgroupe", "nomActivite", "abregeActivite", "dateDebut", "dateFin",
                           "IDfacture", "IDindividu", "IDfamille", "ordre", "IDnumLigne", "prixTranspAller", "prixTranspRetour"]
        #listePrestations : IDnumPiece, IDprestation, IDcompte_payeur, numero, date, categorie, label, quantite, prixUnit,
        #                   montant, tva, IDactivite, nomActivite, abregeActivite, nomTarif, IDfacture, IDindividu, IDfamille, Ordre, IDnumLigne
        fGest = aGestionInscription.Forfaits(self)

        # composition de la liste des prestations noethys existantes
        self.listeIDprestations = []
        for ligne in listePrestations:
            if ligne[1] != None and ligne[1] !=0:
                if not ligne[1] in self.listeIDprestations:
                    self.listeIDprestations.append(ligne[1])
                    # Ajout du transport dans la ligne
                    ligneTrans = fGest.DictTrack(champsPrestations,ligne)
                    if ligneTrans['prixTranspAller']  == None : ligneTrans['prixTranspAller']  = 0
                    if ligneTrans['prixTranspRetour'] == None : ligneTrans['prixTranspRetour'] = 0
                    if ligneTrans["prixTranspAller"] + ligneTrans["prixTranspRetour"] != 0:
                        ligneTrans["ordre"] = 9999
                        ligneTrans["IDnumLigne"] = 9999
                        ligneTrans["label"] = u'Voyage en groupe - Forfait'
                        ligneTrans["lprixUnit"] = ligneTrans["prixTranspAller"] + ligneTrans["prixTranspRetour"]
                        ligneTrans["montant"] = ligneTrans["prixTranspAller"] + ligneTrans["prixTranspRetour"]
                        lstTransPrest=[]
                        for champ in champsPrestations:
                            lstTransPrest.append(ligneTrans[champ])
                        listePrestations.append(lstTransPrest)

        conditionPrestations = " WHERE prestations.IDprestation in (" + str(self.listeIDprestations)[1:-1] + ") "
        # Recherche de la ventilation des prestations
        req = """
        SELECT ventilation.IDprestation, ventilation.IDreglement, ventilation.IDcompte_payeur, SUM(ventilation.montant) AS montant_ventilation,
        reglements.date, reglements.montant, reglements.numero_piece, modes_reglements.label, emetteurs.nom, payeurs.nom
        FROM ventilation
        LEFT JOIN prestations ON prestations.IDprestation = ventilation.IDprestation
        LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
        LEFT JOIN reglements ON reglements.IDreglement = ventilation.IDreglement
        LEFT JOIN modes_reglements ON modes_reglements.IDmode = reglements.IDmode
        LEFT JOIN emetteurs ON emetteurs.IDemetteur = reglements.IDemetteur
        LEFT JOIN payeurs ON payeurs.IDpayeur = reglements.IDpayeur
        %s
        GROUP BY ventilation.IDprestation, ventilation.IDreglement
        ORDER BY prestations.date
        ;""" % conditionPrestations
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            msg = aGestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        listeVentilationPrestations = DB.ResultatReq()
        dictVentilationPrestations = {}
        dictReglements = {}
        for IDprestation, IDreglement, IDcompte_payeur, montant_ventilation, date, montant, numero_piece, mode, emetteur, payeur in listeVentilationPrestations :
            date = UTILS_Dates.DateEngEnDateDD(date)
            montant = FloatToDecimal(montant)
            montant_ventilation = FloatToDecimal(montant_ventilation)

            # Mémorisation des règlements
            if dictReglements.has_key(IDcompte_payeur) == False :
                dictReglements[IDcompte_payeur] = {}
            if dictReglements[IDcompte_payeur].has_key(IDreglement) == False :
                dictReglements[IDcompte_payeur][IDreglement] = {"date" : date, "montant" : montant, "mode" : mode, "emetteur" : emetteur, "numero" : numero_piece, "payeur" : payeur, "ventilation" : FloatToDecimal(0.0)}
            dictReglements[IDcompte_payeur][IDreglement]["ventilation"] += montant_ventilation
            # Mémorisation de la ventilation
            if dictVentilationPrestations.has_key(IDprestation) == False :
                dictVentilationPrestations[IDprestation] = FloatToDecimal(0.0)
            dictVentilationPrestations[IDprestation] += montant_ventilation

        # Recherche des QF aux dates concernées
        date_min = datetime.date(9999, 12, 31)
        date_max = datetime.date(1, 1, 1)
        conditions = "WHERE quotients.date_fin>='%s' AND quotients.date_debut<='%s' " % (date_min, date_max)
        req = """
        SELECT quotients.IDfamille, quotients.quotient, quotients.date_debut, quotients.date_fin
        FROM quotients
        %s
        ORDER BY quotients.date_debut
        ;""" % conditions
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            msg = aGestionDB.Messages()
            msg.Box("Problème sql", retour)
            return

        listeQfdates = DB.ResultatReq()
            
        # Recherche des anciennes prestations impayées (=le report antérieur pour le payeur)
        if len(listeFactures) != 0 :
            conditionPayeurs = " WHERE prestations.IDcompte_payeur in ("
            for dicFact in self.listeFactures :
                conditionPayeurs += str(dicFact["IDcompte_payeur"]) + ","
            conditionPayeurs = conditionPayeurs[:-1] + " ) "
        else :
            conditionPayeurs = ""
        req = """
            SELECT prestations.IDprestation, prestations.IDcompte_payeur, prestations.Date, prestations.categorie, prestations.label, prestations.montant, prestations.IDactivite, activites.nom, activites.abrege, prestations.IDtarif, prestations.IDfacture, prestations.IDindividu, prestations.IDfamille
            FROM prestations
            LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
            LEFT JOIN matPieces ON prestations.IDprestation = matPieces.pieIDinscription
            %s
            GROUP BY prestations.IDprestation
            ORDER BY prestations.date
            ;""" % conditionPayeurs
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            msg = aGestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        listeReports = DB.ResultatReq()
        # Recherche de la ventilation des reports
        req = """
        SELECT ventilation.IDprestation, SUM(ventilation.montant) AS montant_ventilation
        FROM ventilation
        LEFT JOIN prestations ON prestations.IDprestation = ventilation.IDprestation
        LEFT JOIN activites ON prestations.IDactivite = activites.IDactivite
        %s 
        GROUP BY prestations.IDprestation
        ;""" % conditionPayeurs
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            msg = aGestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        listeVentilationReports = DB.ResultatReq()
        dictVentilationReports = {}
        for IDprestation, montant_ventilation in listeVentilationReports :
            dictVentilationReports[IDprestation] = montant_ventilation

        # Recherche des déductions
        req = u"""
        SELECT IDdeduction, deductions.IDprestation, deductions.date, deductions.montant, deductions.label, deductions.IDaide
        FROM deductions
        LEFT JOIN prestations ON prestations.IDprestation = deductions.IDprestation
        %s
        ;""" % conditionPrestations
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            msg = aGestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        listeDeductionsTemp = DB.ResultatReq()
        dictDeductions = {}
        for IDdeduction, IDprestation, date, montant, label, IDaide in listeDeductionsTemp :
            if dictDeductions.has_key(IDprestation) == False :
                dictDeductions[IDprestation] = []
            dictDeductions[IDprestation].append({"IDdeduction":IDdeduction, "date":date, "montant":montant, "label":label, "IDaide":IDaide})

        # Analyse et regroupement des données
        num_facture = 0
        dictComptes = {}
        dictComptesPayeursFactures = {}

        #ex listePrestations : IDnumPiece, IDprestation, IDcompte_payeur, numero, date, categorie, label, quantite, prixUnit,
        #                   montant, tva, IDactivite, nomActivite, abregeActivite, nomTarif, IDfacture, IDindividu, IDfamille, Ordre, IDnumLigne

        #for IDnumPiece, IDprestation, IDcompte_payeur, numero, date, categorie, label, quantite, prixUnit,
        #    montant, tva, IDactivite, IDgroupe, nomActivite, abregeActivite, dateDebut, dateFin, IDfacture,
        #    IDindividu, IDfamille, Ordre, IDnumLigne in listePrestations :
        for IDnumPiece, IDprestation, IDcompte_payeur, numero, date, categorie, label, quantite, prixUnit, montant, tva, IDactivite, IDgroupe, nomActivite, abregeActivite, dateDebut, dateFin, IDfacture, IDindividu, IDfamille, Ordre, IDnumLigne, prixTranspAller, prixTranspRetour in listePrestations :
            # Recherche nbre de jours d'ouverture
            nbJours = 0
            if IDactivite != None and IDgroupe!= None:
                req = "SELECT COUNT(date) FROM ouvertures WHERE IDactivite = %d  AND IDgroupe = %d;" % (IDactivite,IDgroupe)
                DB.ExecuterReq(req,MsgBox=True)
                recordset = DB.ResultatReq()
                if len(recordset) != 0: nbJours = recordset[0][0]
            #Autres éléments à incorporer au dictionnaire de la facture
            date_debut = UTILS_Dates.DateEngEnDateDD(dateDebut)
            date_fin = UTILS_Dates.DateEngEnDateDD(dateFin)
            if numero == None:
                numero = 0
            montant = FloatToDecimal(montant)
            ID = numero
            if dictComptesPayeursFactures.has_key(IDcompte_payeur) == False :
                dictComptesPayeursFactures[IDcompte_payeur] = []
            if numero not in dictComptesPayeursFactures[IDcompte_payeur] :
                dictComptesPayeursFactures[IDcompte_payeur].append(numero)
            if IDfamille == None:
                IDfamille = IDcompte_payeur
            if dictFactures.has_key(numero):
                date_edition = UTILS_Dates.DateEngEnDateDD(dictFactures[numero]["date_edition"])
                date_echeance = UTILS_Dates.DateEngEnDateDD(dictFactures[numero]["date_echeance"])
            # Regroupement par compte payeur
            if dictComptes.has_key(ID) == False:
                # Recherche des titulaires
                dictInfosTitulaires = self.dictNomsTitulaires[IDfamille]
                nomsTitulairesAvecCivilite = dictInfosTitulaires["titulairesAvecCivilite"]
                nomsTitulairesSansCivilite = dictInfosTitulaires["titulairesSansCivilite"]
                rue_resid = dictInfosTitulaires["adresse"]["rue"]
                cp_resid = dictInfosTitulaires["adresse"]["cp"]
                ville_resid = dictInfosTitulaires["adresse"]["ville"]

                # Recherche des règlements
                if dictReglements.has_key(IDcompte_payeur) :
                    dictReglementsCompte = dictReglements[IDcompte_payeur]
                else :
                    dictReglementsCompte = {}

                # Mémorisation des infos
                dictComptes[ID] = {
                    "date_debut" : date_debut,
                    "date_fin" : date_fin,
                    #"nombre_jours": nbJours,
                    #liste activité peutrester vide
                    "liste_activites" : [],
                    "{FAMILLE_NOM}" : nomsTitulairesAvecCivilite,
                    "nomSansCivilite" : nomsTitulairesSansCivilite,
                    "IDfamille" : IDfamille,
                    "{IDFAMILLE}" : str(IDfamille),
                    "{FAMILLE_RUE}" : rue_resid,
                    "{FAMILLE_CP}" : cp_resid,
                    "{FAMILLE_VILLE}" : ville_resid,
                    "individus" : {},
                    "listePrestations" : [],
                    "listeDeductions" : [],
                    "prestations_familiales" : [],
                    "total" : FloatToDecimal(0.0),
                    "ventilation" : FloatToDecimal(0.0),
                    "solde" : FloatToDecimal(0.0),
                    "qfdates" : {},
                    "reports" : {},
                    "total_reports" : FloatToDecimal(0.0),
                    "{TOTAL_REPORTS}" : u"0.00 %s" % SYMBOLE,
                    "solde_avec_reports" : FloatToDecimal(0.0),
                    "{SOLDE_AVEC_REPORTS}" : u"0.00 %s" % SYMBOLE,
                    "num_facture" : None,
                    "select" : True,
                    "messages_familiaux" : [],
                    "{NOM_LOT}" : "",
                    "reglements" : dictReglementsCompte,

                    "date_edition" : date_edition,
                    "{DATE_EDITION_LONG}" : UTILS_Dates.DateComplete(date_edition),
                    "{DATE_EDITION_COURT}" : UTILS_Dates.DateEngFr(str(date_edition)),

                    "numero" : _(u"Facture n°%06d") % num_facture,
                    "num_facture" : num_facture,
                    "{NUM_FACTURE}" : u"%06d" % num_facture,
                    "{CODEBARRES_NUM_FACTURE}" :"F%06d" % num_facture,

                    "{ORGANISATEUR_NOM}" : self.dictOrganisme["nom"],
                    "{ORGANISATEUR_RUE}" : self.dictOrganisme["rue"],
                    "{ORGANISATEUR_CP}" : self.dictOrganisme["cp"],
                    "{ORGANISATEUR_VILLE}" : self.dictOrganisme["ville"],
                    "{ORGANISATEUR_TEL}" : self.dictOrganisme["tel"],
                    "{ORGANISATEUR_FAX}" : self.dictOrganisme["fax"],
                    "{ORGANISATEUR_MAIL}" : self.dictOrganisme["mail"],
                    "{ORGANISATEUR_SITE}" : self.dictOrganisme["site"],
                    "{ORGANISATEUR_AGREMENT}" : self.dictOrganisme["num_agrement"],
                    "{ORGANISATEUR_SIRET}" : self.dictOrganisme["num_siret"],
                    "{ORGANISATEUR_APE}" : self.dictOrganisme["code_ape"],
                    }

                # Ajoute les informations de base famille
                dictComptes[ID].update(self.infosIndividus.GetDictValeurs(mode="famille", ID=IDfamille, formatChamp=True))

                # Date échéance
                if date_echeance != None :
                    if date_echeance != None :
                        dictComptes[ID]["date_echeance"] = date_echeance
                        dictComptes[ID]["{DATE_ECHEANCE_LONG}"] = UTILS_Dates.DateComplete(date_echeance)
                        dictComptes[ID]["{DATE_ECHEANCE_COURT}"] = UTILS_Dates.DateEngFr(str(date_echeance))
                        dictComptes[ID]["{TEXTE_ECHEANCE}"] = _(u"Echéance du règlement : %s") % UTILS_Dates.DateEngFr(str(date_echeance))
                else:
                    dictComptes[ID]["date_echeance"] = None
                    dictComptes[ID]["{DATE_ECHEANCE_LONG}"] = ""
                    dictComptes[ID]["{DATE_ECHEANCE_COURT}"] = ""
                    dictComptes[ID]["{TEXTE_ECHEANCE}"] = ""

                # Ajoute les réponses des questionnaires
                for dictReponse in self.Questionnaires.GetDonnees(IDfamille) :
                    dictComptes[ID][dictReponse["champ"]] = dictReponse["reponse"]
                    if dictReponse["controle"] == "codebarres" :
                        dictComptes[ID]["{CODEBARRES_QUESTION_%d}" % dictReponse["IDquestion"]] = dictReponse["reponse"]

                # Ajoute les messages familiaux
                if self.dictMessageFamiliaux.has_key(IDfamille) :
                    dictComptes[ID]["messages_familiaux"] = self.dictMessageFamiliaux[IDfamille]


            # Insert les montants pour le compte payeur
            if dictVentilationPrestations.has_key(IDprestation) :
                montant_ventilation = FloatToDecimal(dictVentilationPrestations[IDprestation])
                dictVentilationPrestations[IDprestation]=0.0
            else :
                montant_ventilation = FloatToDecimal(0.0)
            dictComptes[ID]["total"] += montant
            dictComptes[ID]["ventilation"] += montant_ventilation
            dictComptes[ID]["solde"] = dictComptes[ID]["total"] - dictComptes[ID]["ventilation"]
            dictComptes[ID]["{TOTAL_PERIODE}"] = u"%.02f %s" % (dictComptes[ID]["total"], SYMBOLE)
            dictComptes[ID]["{TOTAL_REGLE}"] = u"%.02f %s" % (dictComptes[ID]["ventilation"], SYMBOLE)
            dictComptes[ID]["{SOLDE_DU}"] = u"%.02f %s" % (dictComptes[ID]["solde"], SYMBOLE)

            # Ajout d'une prestation familiale
            if IDindividu == None :
                IDindividu = 0
            if IDactivite == None :
                IDactivite = 0

            # Ajout d'un individu
            if dictComptes[ID]["individus"].has_key(IDindividu) == False :
                if self.dictIndividus.has_key(IDindividu) :
                    # Si c'est bien un individu
                    IDcivilite = self.dictIndividus[IDindividu]["IDcivilite"]
                    nomIndividu = self.dictIndividus[IDindividu]["nom"]
                    prenomIndividu = self.dictIndividus[IDindividu]["prenom"]
                    dateNaiss = self.dictIndividus[IDindividu]["date_naiss"]
                    if dateNaiss != None :
                        if DICT_CIVILITES[IDcivilite]["sexe"] == "M" :
                            texteDateNaiss = _(u", né le %s") % UTILS_Dates.DateEngFr(str(dateNaiss))
                        else:
                            texteDateNaiss = _(u", née le %s") % UTILS_Dates.DateEngFr(str(dateNaiss))
                    else:
                        texteDateNaiss = u""
                    texteIndividu = _(u"<b>%s %s</b><font size=7>%s</font>") % (nomIndividu, prenomIndividu, texteDateNaiss)
                    nom = u"%s %s" % (nomIndividu, prenomIndividu)

                else:
                    # Si c'est pour une prestation familiale on créé un individu ID 0 :
                    nom = _(u"Prestations familiales")
                    texteIndividu = u"<b>%s</b>" % nom

                dictComptes[ID]["individus"][IDindividu] = { "texte" : texteIndividu, "activites" : {}, "total" : FloatToDecimal(0.0), "ventilation" : FloatToDecimal(0.0), "total_reports" : FloatToDecimal(0.0), "nom" : nom, "select" : True }

            # Ajout de l'activité
            if dictComptes[ID]["individus"][IDindividu]["activites"].has_key(IDactivite) == False :
                texteActivite = nomActivite
                if dateFin != None:
                    texteActivite += _(u"\nDu %s au %s soit %d jours") % (DateEngFr(str(dateDebut)), DateEngFr(str(dateFin)), nbJours)
                    #texteActivite += label
                agrement = self.RechercheAgrement(IDactivite, date)
                if agrement != None :
                    texteActivite += _(u" - n° agrément : %s") % agrement
                dictComptes[ID]["individus"][IDindividu]["activites"][IDactivite] = { "texte" : texteActivite, "presences" : {} }

            # Ajout de la présence
            if dictComptes[ID]["individus"][IDindividu]["activites"][IDactivite]["presences"].has_key(date) == False :
                dictComptes[ID]["individus"][IDindividu]["activites"][IDactivite]["presences"][date] = { "texte" : UTILS_Dates.DateEngFr(str(date)), "unites" : [], "total" : FloatToDecimal(0.0) }

            # Recherche des déductions
            if dictDeductions.has_key(IDprestation) :
                deductions = dictDeductions[IDprestation]
            else :
                deductions = []

            # Mémorisation des déductions pour total
            for dictDeduction in deductions :
                dictComptes[ID]["listeDeductions"].append(dictDeduction)

            # Adaptation du label
            #label = nomActivite

            # Mémorisation de la prestation
            dictPrestation = {
                "IDprestation" : IDprestation, "date" : date, "categorie" : categorie, "label" : label,
                "montant_initial" : quantite * prixUnit, "montant" : montant, "tva" : tva,
                "montant_ventilation" : montant_ventilation,
                "deductions" : deductions,
                }

            dictComptes[ID]["individus"][IDindividu]["activites"][IDactivite]["presences"][date]["unites"].append(dictPrestation)

            # Ajout des totaux
            if montant != None :
                dictComptes[ID]["individus"][IDindividu]["total"] += montant
                dictComptes[ID]["individus"][IDindividu]["activites"][IDactivite]["presences"][date]["total"] += montant
            if montant_ventilation != None :
                dictComptes[ID]["individus"][IDindividu]["ventilation"] += montant_ventilation

            # Stockage des IDprestation pour saisir le IDfacture après création de la facture
            dictComptes[ID]["listePrestations"].append( (IDindividu, IDprestation) )

            # Intégration des qf aux dates concernées
            for qf_idfamille, quotient, qfdate_debut, qfdate_fin in listeQfdates :
                qfdate_debut = UTILS_Dates.DateEngEnDateDD(qfdate_debut)
                qfdate_fin = UTILS_Dates.DateEngEnDateDD(qfdate_fin)
                if qf_idfamille == IDfamille and qfdate_debut <= date_fin and qfdate_fin >= date_debut :
                    if qfdate_debut < date_debut :
                        plage = "du %s " % UTILS_Dates.DateEngFr(str(date_debut))
                    else :
                        plage = "du %s " % UTILS_Dates.DateEngFr(str(qfdate_debut))
                    if qfdate_fin > date_fin :
                        plage = plage + "au %s" % UTILS_Dates.DateEngFr(str(date_fin))
                    else :
                        plage = plage + "au %s" % UTILS_Dates.DateEngFr(str(qfdate_fin))
                    dictComptes[ID]["qfdates"][plage] = quotient


        # Intégration des total des déductions
        for ID, valeurs in dictComptes.iteritems() :
            totalDeductions = 0.0
            for dictDeduction in dictComptes[ID]["listeDeductions"] :
                totalDeductions += dictDeduction["montant"]
            dictComptes[ID]["{TOTAL_DEDUCTIONS}"] = u"%.02f %s" % (totalDeductions, SYMBOLE)

        # Intégration du REPORT des anciennes prestations NON PAYEES
        for IDprestation, IDcompte_payeur, date, categorie, label, montant, IDactivite, nomActivite, abregeActivite, IDtarif, IDfacture, IDindividu, IDfamille in listeReports :
            montant = FloatToDecimal(montant)
            if dictVentilationReports.has_key(IDcompte_payeur) :
                montant_ventilation = FloatToDecimal(dictVentilationReports[IDcompte_payeur])
            else :
                montant_ventilation = FloatToDecimal(0.0)

            montant_impaye = montant - montant_ventilation

            date = UTILS_Dates.DateEngEnDateDD(date)
            mois = date.month
            annee = date.year
            periode = (annee, mois)

            if montant_ventilation != montant :
                if len(listeFactures) == 0 :
                    if dictComptes.has_key(IDcompte_payeur) :
                        if dictComptes[IDcompte_payeur]["reports"].has_key(periode) == False :
                            dictComptes[IDcompte_payeur]["reports"][periode] = FloatToDecimal(0.0)
                        dictComptes[IDcompte_payeur]["reports"][periode] += montant_impaye
                        dictComptes[IDcompte_payeur]["total_reports"] += montant_impaye
                        dictComptes[IDcompte_payeur]["{TOTAL_REPORTS}"] = u"%.02f %s" % (dictComptes[IDcompte_payeur]["total_reports"], SYMBOLE)

                else :
                    if dictComptesPayeursFactures.has_key(IDcompte_payeur) :
                        for IDfacture in dictComptesPayeursFactures[IDcompte_payeur] :
                            if dictComptes[IDfacture]["date_debut"] != None :
                                if date < dictComptes[IDfacture]["date_debut"] :
                                    if dictComptes[IDfacture]["reports"].has_key(periode) == False :
                                        dictComptes[IDfacture]["reports"][periode] = FloatToDecimal(0.0)
                                    dictComptes[IDfacture]["reports"][periode] += montant_impaye
                                    dictComptes[IDfacture]["total_reports"] += montant_impaye
                                    dictComptes[IDfacture]["{TOTAL_REPORTS}"] = u"%.02f %s" % (dictComptes[IDfacture]["total_reports"], SYMBOLE)
        
        # Ajout des impayés au solde
        for ID, dictValeurs in dictComptes.iteritems() :
            dictComptes[ID]["solde_avec_reports"] = dictComptes[ID]["solde"] + dictComptes[ID]["total_reports"]
            dictComptes[ID]["{SOLDE_AVEC_REPORTS}"] = u"%.02f %s" % (dictComptes[ID]["solde_avec_reports"], SYMBOLE)
        return dictComptes
        #fin GetDonnees

    def GetDonneesImpression(self, listePieces=[], dictOptions=None):
        """ Impression des factures """
        dlgAttente = PBI.PyBusyInfo(_(u"Recherche des données de facturation..."), parent=None, title=_(u"Veuillez patienter..."), icon=wx.Bitmap("Images/16x16/Logo.png", wx.BITMAP_TYPE_ANY))
        try :
            wx.Yield() 
        except :
            pass

        # Récupère les données pour reconstituer les factures à partir la liste pièces
        if len(listePieces) == 0 : conditions = "()"
        elif len(listePieces) == 1 : conditions = "(%d)" % listePieces[0]
        else : conditions = str(tuple(listePieces))

        # Noms dans la requête
        #     IDnumPiece, IDfacture, IDinscription, NoFacture, IDcompte_payeur, IDactivite,
        #    IDindividu, DateFacturation, DateEcheance, UtilisateurModif,
        #    dateDebut, dateFin, IDprestation,
        #    date_debut, date_fin, total, regle, solde, prestations, lots_nom
        champsDonnees = ["IDnumPiece","IDfacture", "IDinscription", "numero", "IDcompte_payeur", "IDactivite","IDindividu",
                         "IDfamille", "date_edition", "date_echeance", "IDutilisateur","dateModif", "IDprestation" ,
                         "date_debut", "date_fin","total", "regle", "solde", "typesPrestations"]
        DB = aGestionDB.DB()

        #  LEFT JOIN lots_factures ON factures.IDlot = lots_factures.IDlot

        req = """
        SELECT matPieces.pieIDnumPiece, factures.IDfacture, matPieces.pieIDinscription, matPieces.pieNoFacture, matPieces.pieIDcompte_payeur, matPieces.pieIDactivite,matPieces.pieIDindividu,
            matPieces.pieIDfamille, matPieces.pieDateFacturation, matPieces.pieDateEcheance, matPieces.pieUtilisateurModif,matPieces.pieDateModif, matPieces.pieIDprestation,
            factures.date_debut, factures.date_fin, factures.total, factures.regle, factures.solde, factures.prestations
        FROM matPieces
        LEFT JOIN  factures
        ON matPieces.pieNoFacture = factures.numero
        WHERE matPieces.pieIDnumPiece In %s
        GROUP BY matPieces.pieIDnumPiece, factures.IDfacture, matPieces.pieIDinscription, matPieces.pieNoFacture, matPieces.pieIDcompte_payeur, matPieces.pieIDactivite, matPieces.pieIDindividu, matPieces.pieIDfamille, matPieces.pieDateFacturation, matPieces.pieDateEcheance, matPieces.pieUtilisateurModif, matPieces.pieIDprestation, factures.date_debut, factures.date_fin, factures.total, factures.regle, factures.solde, factures.prestations
        ORDER BY factures.IDfacture
        ;""" % conditions
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            msg = aGestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        listeDonneesPieces = DB.ResultatReq()
        # Regroupements des individus familles et activités
        self.listeIndividus=[]
        self.listeActivites=[]
        self.listeInscriptions=[]
        activites = []
        individus = []
        inscriptions = []
        IDnumPieces=[]
        self.listeFamilles=[]
        self.listeFactures=[]
        self.listeIDnumPieces=[]
        IDfacture = listeDonneesPieces[0][1]
        dicFact = {}

        def Rupture(individus,activites,inscriptions,IDnumPiece):
            self.listeIndividus.extend(individus)
            self.listeActivites.extend(activites)
            self.listeInscriptions.extend(inscriptions)
            self.listeIDnumPieces.extend(IDnumPiece)
            if dicFact["numero"] == None:
                dicFact["numero"] = 0
            dicFact["individus"] = individus
            dicFact["activites"] = activites
            dicFact["inscriptions"] = inscriptions
            dicFact["IDnumPieces"] = IDnumPieces
            dicFact["prestations"] = [u'consommation', u'cotisation', u'autre']
            self.listeFactures.append(dicFact)

        fGest = aGestionInscription.Forfaits(self)
        for piece in listeDonneesPieces:
            dicTemp = fGest.DictTrack(champsDonnees,piece,"xxx")
            #rupture sur changement de IDfacture
            if dicTemp["IDfacture"] != IDfacture:
                Rupture(individus,activites,inscriptions,IDnumPieces)
                individus = []
                activites = []
                inscriptions = []
                IDnumPieces = []
            dicFact = dicTemp
            if not dicTemp["IDindividu"] in individus:
                individus.append(dicTemp["IDindividu"])
            if not dicTemp["IDactivite"] in activites:
                activites.append(dicTemp["IDactivite"])
            if not dicTemp["IDinscription"] in inscriptions:
                inscriptions.append(dicTemp["IDinscription"])
            if not dicTemp["IDnumPiece"] in IDnumPieces:
                IDnumPieces.append(dicTemp["IDnumPiece"])
            if not dicTemp["IDfamille"] in self.listeFamilles:
                if dicTemp["IDfamille"] != None : self.listeFamilles.append(dicTemp["IDfamille"])
            if not dicTemp["IDcompte_payeur"] in self.listeFamilles:
                if dicTemp["IDcompte_payeur"]!= None : self.listeFamilles.append(dicTemp["IDcompte_payeur"])
        Rupture(individus,activites,inscriptions,IDnumPieces)
        if 0 in self.listeIndividus:
            self.listeIndividus.remove(0)
        if 0 in self.listeActivites:
            self.listeActivites.remove(0)
        #fin de préparation de listeFactures conteneur de tuples (IDfacture, dictFacture)
        #dictFacture.keys = ['IDfacture', 'nomLot', 'regle', 'total', 'date_echeance', 'IDfamille', 'individus', 'IDactivite', 'IDindividu',
        #        'typesPrestations', 'numero', 'activites', 'date_fin', 'IDnumPiece', 'date_edition', 'IDprestation', 'IDcompte_payeur',
        #        'dateModif', 'date_debut', 'solde', 'IDutilisateur']

        self.GetInfos()

        # Récupération des prélèvements
        req = """SELECT 
        prelevements.IDprelevement, prelevements.prelevement_numero, prelevements.prelevement_iban,
        prelevements.IDfacture, prelevements.montant, prelevements.statut, 
        comptes_payeurs.IDcompte_payeur, lots_prelevements.date,
        prelevement_reference_mandat, comptes_bancaires.code_ics
        FROM prelevements
        LEFT JOIN lots_prelevements ON lots_prelevements.IDlot = prelevements.IDlot
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDfamille = prelevements.IDfamille
        LEFT JOIN comptes_bancaires ON comptes_bancaires.IDcompte = lots_prelevements.IDcompte
        WHERE prelevements.IDfacture IN %s
        ;""" % conditions
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            msg = aGestionDB.Messages()
            msg.Box("Problème sql", retour)
            return
        listePrelevements = DB.ResultatReq()
        dictPrelevements = {}
        for IDprelevement, numero_compte, iban, IDfacture, montant, statut, IDcompte_payeur, datePrelevement, rum, code_ics in listePrelevements :
            datePrelevement = UTILS_Dates.DateEngEnDateDD(datePrelevement)
            dictPrelevements[IDfacture] = {
                "IDprelevement" : IDprelevement, "numero_compte" : numero_compte, "montant" : montant, 
                "statut" : statut, "IDcompte_payeur" : IDcompte_payeur, "datePrelevement" : datePrelevement, 
                "iban" : iban, "rum" : rum, "code_ics" : code_ics,
                }
        
        DB.Close() 
        if len(self.listeFactures) == 0 :
            del dlgAttente
            return False

        self.EcritStatusbar(_(u"Recherche des factures"))

        # Récupération des données de facturation
        typeLabel = 0
        if dictOptions != None and dictOptions.has_key("intitules") :
            typeLabel = dictOptions["intitules"]
            
        dictComptes = self.GetDonnees(listeFactures=self.listeFactures, typeLabel=typeLabel)
        dictFactures = {}
        dictChampsFusion = {}

        # Déroulement des factures composition du dictionnaire d'impression
        for dicFact in self.listeFactures :
            numero = dicFact["numero"]
            date_edition = dicFact["date_edition"]
            date_echeance = dicFact["date_echeance"]
            date_debut = dicFact["date_debut"]
            date_fin = dicFact["date_fin"]
            regle = FloatToDecimal(dicFact["regle"])
            solde = FloatToDecimal(dicFact["solde"])
            #nomLot = dicFact["nomLot"]
            if dictComptes.has_key(numero) :
                dictCompte = dictComptes[numero]
                dictCompte["select"] = True
                
                # Affichage du solde initial
                if dictOptions != None and dictOptions["affichage_solde"] == 1:
                    dictCompte["ventilation"] = regle
                    dictCompte["solde"] = solde
                
                # Attribue un numéro de facture
                dictCompte["num_facture"] = numero
                dictCompte["num_codeBarre"] = "%07d" % numero
                dictCompte["numero"] = _(u"Facture n°%07d") % numero
                dictCompte["{NUM_FACTURE}"] = u"%06d" % numero
                dictCompte["{CODEBARRES_NUM_FACTURE}"] = "F%06d" % numero
                dictCompte["{NUMERO_FACTURE}"] = dictCompte["{NUM_FACTURE}"]
                dictCompte["{DATE_DEBUT}"] = UTILS_Dates.DateEngFr(str(date_debut))
                dictCompte["{DATE_FIN}"] = UTILS_Dates.DateEngFr(str(date_fin))
                dictCompte["{DATE_EDITION_FACTURE}"] = UTILS_Dates.DateEngFr(str(date_edition))
                dictCompte["{DATE_ECHEANCE}"] = UTILS_Dates.DateEngFr(str(date_echeance))
                dictCompte["{SOLDE}"] = u"%.2f %s" % (dictCompte["solde"], SYMBOLE)
                dictCompte["{SOLDE_LETTRES}"] = UTILS_Conversion.trad(solde, MONNAIE_SINGULIER, MONNAIE_DIVISION).strip().capitalize() 
                dictCompte["{SOLDE_AVEC_REPORTS}"] = u"%.2f %s" % (dictCompte["solde_avec_reports"], SYMBOLE)
                dictCompte["{SOLDE_AVEC_REPORTS_LETTRES}"] = UTILS_Conversion.trad(solde+dictCompte["total_reports"], MONNAIE_SINGULIER, MONNAIE_DIVISION).strip().capitalize() 

                #if nomLot == None :
                nomLot = ""
                dictCompte["{NOM_LOT}"] = nomLot
                
                for IDindividu, dictIndividu in dictCompte["individus"].iteritems() :
                    dictIndividu["select"] = True
                
                # Recherche de prélèvements
                if dictPrelevements.has_key(numero) :
                    if datePrelevement < dictCompte["date_edition"] :
                        verbe = _(u"a été")
                    else :
                        verbe = _(u"sera")
                    montant = dictPrelevements[numero]["montant"]
                    datePrelevement = dictPrelevements[numero]["datePrelevement"]
                    iban = dictPrelevements[numero]["iban"]
                    rum = dictPrelevements[numero]["rum"]
                    code_ics = dictPrelevements[numero]["code_ics"]
                    if iban != None :
                        dictCompte["prelevement"] = _(u"La somme de %.2f %s %s prélevée le %s sur le compte ***%s") % (montant, SYMBOLE, verbe, UTILS_Dates.DateEngFr(str(datePrelevement)), iban[-7:])
                    else :
                        dictCompte["prelevement"] = _(u"La somme de %.2f %s %s prélevée le %s") % (montant, SYMBOLE, verbe, UTILS_Dates.DateEngFr(str(datePrelevement)))
                    if rum != None :
                        dictCompte["prelevement"] += _(u"<br/>Réf. mandat unique : %s / Code ICS : %s") % (rum, code_ics)
                else :
                    dictCompte["prelevement"] = None

                # Champs de fusion pour Email
                dictChampsFusion[numero] = {}
                dictChampsFusion[numero]["{NUMERO_FACTURE}"] = dictCompte["{NUM_FACTURE}"]
                dictChampsFusion[numero]["{DATE_DEBUT}"] = UTILS_Dates.DateEngFr(str(date_debut))
                dictChampsFusion[numero]["{DATE_FIN}"] = UTILS_Dates.DateEngFr(str(date_fin))
                dictChampsFusion[numero]["{DATE_EDITION_FACTURE}"] = UTILS_Dates.DateEngFr(str(date_edition))
                dictChampsFusion[numero]["{DATE_ECHEANCE}"] = UTILS_Dates.DateEngFr(str(date_echeance))
                dictChampsFusion[numero]["{SOLDE}"] = u"%.2f %s" % (dictCompte["solde"], SYMBOLE)
                dictChampsFusion[numero]["{SOLDE_AVEC_REPORTS}"] = dictCompte["{SOLDE_AVEC_REPORTS}"]
                
                
                # Fusion pour textes personnalisés
                dictCompte["texte_introduction"] = self.RemplaceMotsCles(dictOptions["texte_introduction"], dictCompte)
                dictCompte["texte_conclusion"] = self.RemplaceMotsCles(dictOptions["texte_conclusion"], dictCompte)

                # Mémorisation de la facture
                dictFactures[numero] = dictCompte

        del dlgAttente
        self.EcritStatusbar("")   

        if len(dictFactures) == 0 :
            return False
           
        return dictFactures, dictChampsFusion
        #fin GetDonneesImpression

    def GetListePieces(self,listeFactures):
        # Récupération de la liste des pièces concernées par la liste des Factures
        listeReq = str(tuple(listeFactures)).replace(",)",")")
        DB = aGestionDB.DB()
        conditions = "WHERE factures.numero in %s " % listeReq
        req = """SELECT matPieces.pieIDnumPiece
                FROM factures
                LEFT JOIN matPieces ON factures.numero = matPieces.pieNoFacture
                %s ;""" % conditions
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            Msg = aGestionDB.Messages()
            Msg.Box( message= retour)
            Msg.Close()
            return None
        retour = DB.ResultatReq()
        listePieces = []
        for rec in retour:
            listePieces.append(rec[0])
        return listePieces
        #fin GetListePieces

    def Impression(self, listeNoFactures=[], listePieces=[],typeLancement = "factures", nomDoc=None, afficherDoc=True, dictOptions=None, repertoire=None, repertoireTemp=False):
        """ Impression des factures """
        # Composition de la liste des pièces
        if typeLancement == "factures":
            if len(listeNoFactures) == 0:
                Msg = aGestionDB.Messages()
                Msg.Box( message= "Aucune facture dans listeFactures")
                Msg.Close()
                return None
            mode = "facture"
            self.listePieces = self.GetListePieces(listeNoFactures)
        else:
            mode = "devis"
            if len(listePieces) == 0:
                Msg = aGestionDB.Messages()
                Msg.Box( message= "Aucune pieces dans listePieces")
                Msg.Close()
                return None
            self.listePieces= listePieces

        # Récupération des paramètres d'affichage
        if dictOptions == None :
            if afficherDoc == False :
                dlg = DLG_Apercu_facture.Dialog(None, titre=_(u"Sélection des paramètres de la facture"), intro=_(u"Sélectionnez ici les paramètres d'affichage de la facture à envoyer par Email."))
                dlg.bouton_ok.SetImageEtTexte("Images/32x32/Valider.png", _("Ok"))
            else :
                dlg = DLG_Apercu_facture.Dialog(None)
            if dlg.ShowModal() == wx.ID_OK:
                dictOptions = dlg.GetParametres()
                dlg.Destroy()
            else :
                dlg.Destroy()
                return False

        # Récupération des données à partir de la listeIDpieces
        resultat = self.GetDonneesImpression(self.listePieces, dictOptions)
        if resultat == False :
            return False
        dictFactures, dictChampsFusion = resultat

        # Création des PDF à l'unité
        def CreationPDFunique(repertoireCible=""):
            dictPieces = {}
            dlgAttente = PBI.PyBusyInfo(_(u"Génération des factures à l'unité au format PDF..."), parent=None, title=_(u"Veuillez patienter..."), icon=wx.Bitmap("Images/16x16/Logo.png", wx.BITMAP_TYPE_ANY))
            try :
                wx.Yield() 
            except :
                pass
            try :
                index = 0
                for IDfacture, dictFacture in dictFactures.iteritems() :
                    if dictFacture["select"] == True :
                        num_facture = dictFacture["num_facture"]
                        nomTitulaires = self.Supprime_accent(dictFacture["nomSansCivilite"])
                        nomFichier = _(u"Facture %d - %s") % (num_facture, nomTitulaires)
                        cheminFichier = u"%s/%s.pdf" % (repertoireCible, nomFichier)
                        dictComptesTemp = {IDfacture : dictFacture}
                        self.EcritStatusbar(_(u"Edition de la facture %d/%d : %s") % (index, len(dictFactures), nomFichier))
                        aUTILS_Impression_facture.Impression(dictComptesTemp, dictOptions, IDmodele=dictOptions["IDmodele"], ouverture=False, nomFichier=cheminFichier)
                        dictPieces[IDfacture] = cheminFichier
                        index += 1
                self.EcritStatusbar("")
                del dlgAttente
                return dictPieces
            except Exception, err:
                del dlgAttente
                traceback.print_exc(file=sys.stdout)
                dlg = wx.MessageDialog(None, _(u"Désolé, le problème suivant a été rencontré dans l'édition des factures : \n\n%s") % err, _(u"Erreur"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False
        
        # Répertoire souhaité par l'utilisateur
        if repertoire not in (None, "") :
            resultat = CreationPDFunique(repertoire)
            if resultat == False :
                return False

        # Répertoire TEMP (pour Emails)
        dictPieces = {}
        if repertoireTemp == True :
            dictPieces = CreationPDFunique("Temp")
            if dictPieces == False :
                return False

        # Fabrication du PDF global
        if repertoireTemp == False :
            dlgAttente = PBI.PyBusyInfo(_(u"Création du PDF des factures..."), parent=None, title=_(u"Veuillez patienter..."), icon=wx.Bitmap("Images/16x16/Logo.png", wx.BITMAP_TYPE_ANY))
            try :
                wx.Yield() 
            except :
                pass
            self.EcritStatusbar(_(u"Création du PDF des factures en cours... veuillez patienter..."))
            try :
                # ------------------------------------Lancement de l'impression ----------------------------------------
                #print dictFactures
                #print dictOptions
                aUTILS_Impression_facture.Impression(dictFactures, dictOptions, IDmodele=dictOptions["IDmodele"], ouverture=afficherDoc, nomFichier=nomDoc, mode=mode)
                self.EcritStatusbar("")
                del dlgAttente
            except Exception, err:
                del dlgAttente
                traceback.print_exc(file=sys.stdout)
                err = str(err).decode("iso-8859-15")
                dlg = wx.MessageDialog(None, _(u"Désolé, le problème suivant a été rencontré dans l'édition des factures : \n\n%s") % err, _(u"Erreur"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return False

        return dictChampsFusion, dictPieces
    #fin Impression

def SuppressionFacture(listeIDFactures=[], mode="suppression"):
    """ Suppression d'une facture """
    dlgAttente = PBI.PyBusyInfo(_(u"%s des factures en cours...") % mode.capitalize(), parent=None, title=_(u"Veuillez patienter..."), icon=wx.Bitmap("Images/16x16/Logo.png", wx.BITMAP_TYPE_ANY))
    wx.Yield() 
    DB = aGestionDB.DB()
    
    # Suppression
    if mode == "suppression" :
        for IDfacture in listeIDFactures :
            DB.ReqMAJ("prestations", [("IDfacture", None),], "IDfacture", IDfacture)
            DB.ReqDEL("factures", "IDfacture", IDfacture)
            
    # Annulation
    if mode == "annulation" :
        for IDfacture in listeIDFactures :
            DB.ReqMAJ("prestations", [("IDfacture", None),], "IDfacture", IDfacture)
            DB.ReqMAJ("factures", [("etat", "annulation"),], "IDfacture", IDfacture)
            
    DB.Close() 
    del dlgAttente
    return True

if __name__ == '__main__':
    app = wx.App(0)

    liste = [81]
    dictOptions =  {u'largeur_colonne_date': 50, u'texte_conclusion': u'', u'image_signature': u'', u'texte_titre': u'Facture', u'taille_texte_prestation': 7, u'afficher_avis_prelevements': True, u'taille_texte_messages': 7, u'afficher_qf_dates': True, u'taille_texte_activite': 6, u'affichage_prestations': 0, u'affichage_solde': 0, u'afficher_coupon_reponse': True, u'taille_image_signature': 100, u'alignement_image_signature': 0, u'couleur_fond_conclusion': wx.Colour(255, 255, 255, 255), u'alignement_texte_introduction': 0, u'couleur_bord_conclusion': wx.Colour(255, 255, 255, 255), u'afficher_reglements': True, u'intitules': 0, u'integrer_impayes': False, u'taille_texte_introduction': 9, u'taille_texte_noms_colonnes': 5, u'texte_introduction': u'', u'taille_texte_individu': 9, u'taille_texte_conclusion': 9, u'taille_texte_labels_totaux': 9, u'afficher_periode': False, u'couleur_bord_introduction': wx.Colour(255, 255, 255, 255), u'afficher_codes_barres': True, u'couleur_fond_introduction': wx.Colour(255, 255, 255, 255), u'taille_texte_titre': 19, u'taille_texte_periode': 8, u'IDmodele': 5, u'couleur_fond_2': wx.Colour(234, 234, 255, 255), u'afficher_titre': True, u'couleur_fond_1': wx.Colour(204, 204, 255, 255), u'largeur_colonne_montant_ht': 50, u'afficher_impayes': True, 'messages': [], u'memoriser_parametres': True, u'afficher_messages': True, u'largeur_colonne_montant_ttc': 70, u'taille_texte_montants_totaux': 10, u'alignement_texte_conclusion': 0, u'style_texte_introduction': 0, u'style_texte_conclusion': 0, u'repertoire_copie': u'', u'largeur_colonne_montant_tva': 50}
    facturation = Facturation()

    retour = facturation.Impression(typeLancement = "devis", listePieces=liste, dictOptions=dictOptions, afficherDoc=True,repertoire=dictOptions["repertoire_copie"])

    app.MainLoop()
