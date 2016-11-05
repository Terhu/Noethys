#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Derive de DLG_Appliquer_forfait.py class Forfaits
# pour gerer l'enregistrement des inscriptions
# Application :    Noethys, Matthania
# Auteur:          Ivan LUCAS, Jacques Brunel
# Traitement des inscriptions derrière la tarification
# -----------------------------------------------------------

from UTILS_Traduction import _
import wx
import datetime
import aGestionDB
import aDATA_Tables
from DATA_Tables import DB_DATA as DICT_TABLES

def DateComplete(dateDD):
    """ Transforme une date DD en date complète : Ex : lundi 15 janvier 2008 """
    listeJours = (_(u"Lundi"), _(u"Mardi"), _(u"Mercredi"), _(u"Jeudi"), _(u"Vendredi"), _(u"Samedi"), _(u"Dimanche"))
    listeMois = (
    _(u"janvier"), _(u"février"), _(u"mars"), _(u"avril"), _(u"mai"), _(u"juin"), _(u"juillet"), _(u"août"),
    _(u"septembre"), _(u"octobre"), _(u"novembre"), _(u"décembre"))
    dateComplete = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month - 1] + " " + str(
        dateDD.year)
    return dateComplete

def DateEngEnDateDD(dateEng):
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def GetNoFactureSuivant():
    DB = aGestionDB.DB()
    req = "SELECT MAX(pieNoFacture),MAX(pieNoAvoir) FROM matpieces;"
    retour = DB.ExecuterReq(req)
    if retour != "ok" :
        aGestionDB.MessageBox(retour)
    retour = DB.ResultatReq()
    if (retour[0][0]== None) or (len(retour) == 0) : noFacture = 1
    else:
        if retour[0][1] == None:
            noAvoir = 0
        else : noAvoir = retour[0][1]
        noFacture = max(int(retour[0][0])+1,int(noAvoir)+1)
    DB.Close
    return noFacture

def GetNoFactureMin():
    # principe : lors d'une suppression de facture le numéro et sa date sont mis dans matParams avec clé prmUser = "NoLibre",prmParam = str(numero), prmInt = numero, prmDate = dateFact
    # la recherche d'un numero trouve le plus petit prmInt et sa date puis le supprime
    # pour la date, priorité sera donnée à celle de la première ventilation associée si elle existe à une date antérieure à la facture.
    value,noFacture,date = None,None,None
    DB = aGestionDB.DB()
    req = "SELECT MIN(prmInteger) FROM matParams WHERE prmUser = 'NoLibre';"
    retour = DB.ExecuterReq(req)
    if retour <> "ok" :
        aGestionDB.MessageBox(retour)
    recordset = DB.ResultatReq()
    if len(recordset)>0 :
        if len(recordset[0])>0 :
            value = recordset[0][0]
            if value != None:
                req = "SELECT prmInteger,prmDate FROM matParams WHERE prmUser = 'NoLibre' AND prmInteger = %d ;" % value
                retour = DB.ExecuterReq(req)
                if retour <> "ok" :
                    aGestionDB.MessageBox(retour)
                recordset = DB.ResultatReq()
                noFacture = recordset[0][0]
                dateRet = recordset[0][1]
                req = "DELETE FROM matParams WHERE prmUser = 'NoLibre' AND prmInteger = %d ;" % value
                retour = DB.ExecuterReq(req,commit = True)
                if retour <> "ok" :
                    aGestionDB.MessageBox(retour)
                # condition année civile en cours
                if dateRet != None:
                    date = DateEngEnDateDD(dateRet)
                    if date.year != datetime.date.today().year:
                        date=None
    # quand il n'y a plus de numéro libre on prend le suivant du plus grand
    if date == None:
        date = datetime.date.today()
    if noFacture== None:
        noFacture = GetNoFactureSuivant()
    DB.Close
    return noFacture,date

# Forfaits dans le sens de definition des consommations forfaitisées par un prix de camp
class Forfaits():
    def __init__(self,parent):
        self.parent = parent
        DB = aGestionDB.DB()
        self.user = DB.UtilisateurActuel()
        DB.Close()

    def StandardiseNomsChamps(self,listeChamps, prefixe = "pie"):
        #ote le prefixe au nom du champ et lower sur premier caractère
        newListe=[]
        for champ in listeChamps:
            idx = listeChamps.index(champ)
            if champ[:3] == prefixe:
                champ = champ[3:]
            if champ[:2]=="ID":
                nom =  champ
            else : nom = champ[0].lower()+ champ[1:]
            newListe.append(nom)
        return newListe

    def DictTrack(self,listeChamps, valeurs, prefixe = "pie"):
        #transforme en dictionnaire un record de  requête (liste de valeurs ) selon liste champs
        dictTrack = {}
        newListe = self.StandardiseNomsChamps(listeChamps)
        if len(newListe) != len(valeurs):
            Mess = aGestionDB.Messages()
            message = "Le nombre de champs et de valeurs ne correspondent pas \nNb champs : %d   Nb valeurs : %d !" % (len(newListe),len(valeurs))
            Mess.Box( message= message)
        for champ in newListe:
            idx = newListe.index(champ)
            if champ[:3] == prefixe:
                champ = champ[3:]
            if champ[:2]=="ID":
                nom =  champ
            else : nom = champ[0].lower()+ champ[1:]
            valeur = valeurs[idx]
            dictTrack[nom] = valeur
        return dictTrack

    def GetForfaits(self,IDactivite):
        """ Permet d'obtenir la liste des jours de consommations """
        DB = aGestionDB.DB()
        # Recherche les params de l'activite
        dictActivites = {}
        req = """SELECT activites.IDactivite, activites.nom, abrege, date_debut, date_fin
        FROM activites
        WHERE activites.IDactivite IN (%s) ;""" % IDactivite
        DB.ExecuterReq(req)
        listeActivites = DB.ResultatReq()
        for IDact, nom, abrege, date_debut, date_fin in listeActivites :
            if date_debut != None : date_debut = DateEngEnDateDD(date_debut)
            if date_fin != None : date_fin = DateEngEnDateDD(date_fin)
            dictTemp = { "nom" : nom, "abrege" : abrege, "date_debut" : date_debut, "date_fin" : date_fin, "tarifs" : [], "ouvertures" : {} }
            dictActivites[IDact] = dictTemp

        # Recherche des ouvertures des activités
        req = """SELECT IDouverture, IDactivite, IDunite, IDgroupe, date
        FROM ouvertures
        WHERE IDactivite IN (%s)
        ORDER BY date;""" % IDactivite
        DB.ExecuterReq(req)
        listeOuvertures = DB.ResultatReq()
        for IDouverture, IDact, IDunite, IDgroupe, date in listeOuvertures :
            date = DateEngEnDateDD(date)
            if dictActivites.has_key(IDact) :
                if dictActivites[IDact]["ouvertures"].has_key(IDgroupe) == False :
                    dictActivites[IDact]["ouvertures"][IDgroupe] = {}
                if dictActivites[IDact]["ouvertures"][IDgroupe].has_key(date) == False :
                    dictActivites[IDact]["ouvertures"][IDgroupe][date] = []
                dictActivites[IDact]["ouvertures"][IDgroupe][date].append((date, IDunite, IDgroupe))
        # Cloture de la base de données
        DB.Close()
        return dictActivites

    def ChoixPiece(self,retour):
        # On demande quelle piece supprimer  et on récupére la ligne retour
        msg = aGestionDB.Messages()
        listeTuples = []
        for ligneRetour in retour:
            listeTuples.append((ligneRetour[0],ligneRetour[9]))
        ixChoix,nom = msg.Choix(listeTuples=listeTuples, titre = (u"Cette inscription est rattachée à  %d pièces")% len(listeTuples), intro = u"Double clic pour choisir la pièce")
        if ixChoix == None:
            return None
        else:
            #appel de la piece choisie
            for tuple in listeTuples:
                if ixChoix == tuple[0]:
                    for ligne in retour:
                        if ligne[0] == ixChoix:
                            ligneRetour = ligne
        return ligneRetour

    def AjoutPiece(self,parent,dictDonnees):
        # Sauvegarde de la piece
        dictActivites = self.GetForfaits(dictDonnees["IDactivite"])
        dd=None
        for IDact, dictActivite in dictActivites.iteritems() :
            dd = dictActivite["date_debut"]
        echeance = dd
        datefacture = None
        self.noFacture= None
        listeDonnees = [
            ("pieIDinscription", dictDonnees["IDinscription"]),
            ("pieIDprestation", dictDonnees["IDprestation"]),
            ("pieIDindividu", dictDonnees["IDindividu"]),
            ("pieIDfamille", dictDonnees["IDfamille"]),
            ("pieIDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ("pieIDactivite", dictDonnees["IDactivite"]),
            ("pieIDgroupe", dictDonnees["IDgroupe"]),
            ("pieIDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
            ("pieDateCreation", str(datetime.date.today())),
            ("pieUtilisateurCreateur", self.user),
            ("pieDateModif",str(datetime.date.today())),
            ("pieUtilisateurModif", None),
            ("pieNature", dictDonnees["nature"]),
            ("pieEtat",dictDonnees["etat"]),
            ("pieDateFacturation", datefacture),
            ("pieNoFacture", self.noFacture),
            ("pieDateEcheance", echeance),
            ("pieDateAvoir", None),
            ("pieNoAvoir",None ),
            ("pieCommentaire", dictDonnees["commentaire"]),
            ]
        DB = aGestionDB.DB()
        retour = DB.ReqInsert("matPieces", listeDonnees,retourID = True)
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
            DB.Close()
            return None
        IDnumPiece = DB.newID
       # Enregistre dans PiecesLignes
        listeInit = [
            ("ligIDnumPiece", IDnumPiece),
            ("ligDate",str(datetime.date.today())),
            ("ligUtilisateur", self.user),
            ]
        listeLignesPiece = dictDonnees["lignes_piece"]
        for ligne in listeLignesPiece:
            listeDonnees = listeInit[:]
            listeDonnees.append(("ligCodeArticle",ligne["codeArticle"]))
            listeDonnees.append(("ligLibelle",ligne["libelle"]))
            listeDonnees.append(("ligQuantite",ligne["quantite"]))
            listeDonnees.append(("ligPrixUnit",ligne["prixUnit"]))
            listeDonnees.append(("ligMontant",ligne["montant"]))
            retour = DB.ReqInsert("matPiecesLignes", listeDonnees,retourID = False)
            if retour != "ok" :
                aGestionDB.MessageBox(parent,retour)
                DB.Close()
                return None
        DB.Close()        
        return IDnumPiece
        # fin AjoutPiece

    def AjoutPiece999(self,parent,IDfamille,IDpayeur,saison):
        listeDonnees = [
            ("pieIDinscription", saison),
            ("pieIDindividu", 0),
            ("pieIDcompte_payeur", IDpayeur),
            ("pieIDactivite", 0),
            ("pieIDfamille",IDfamille),
            ("pieDateCreation", str(datetime.date.today())),
            ("pieUtilisateurCreateur", self.user),
            ("pieDateModif",str(datetime.date.today())),
            ("pieUtilisateurModif", None),
            ("pieNature", "COM"),
            ("pieEtat","00000"),
            ]
        DB = aGestionDB.DB()
        retour = DB.ReqInsert("matPieces", listeDonnees,retourID = True)
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
            DB.Close()
            return False
        DB.Close()
        return self.GetPieceModif999(parent,IDpayeur,saison)
        # fin AjoutPiece999

    def AjoutInscription(self,dictDonnees) :
        self.listeDonneesInscriptions = []
        IDactivite = dictDonnees["IDactivite"]
        IDgroupe = dictDonnees["IDgroupe"]
        # Récupération des inscriptions à créer
        listeInscriptions = []
        # Sauvegarde des inscriptions
        DB = aGestionDB.DB()
        listeDonnees = [
            ("IDindividu",  dictDonnees["IDindividu"]),
            ("IDfamille",  dictDonnees["IDfamille"]),
            ("IDactivite",  dictDonnees["IDactivite"]),
            ("IDgroupe",  dictDonnees["IDgroupe"]),
            ("IDcategorie_tarif",  dictDonnees["IDcategorie_tarif"]),
            ("IDcompte_payeur",  dictDonnees["IDcompte_payeur"]),
            ("date_inscription",  dictDonnees["dateCreation"]),
            ("parti", 0)
            ]
        # Insertion des données
        DB.ReqInsert("inscriptions", listeDonnees,retourID=True, MsgBox=True)
        IDinscription = DB.newID
        DB.Close()
        return IDinscription
        #fin AjoutInscription

    def AjoutConsommations(self,parent,dictDonnees) :
        if dictDonnees["nature"]=="AVO":
            return True
        self.listeDonneesConsommations = []
        IDactivite = dictDonnees["IDactivite"]
        IDgroupe = dictDonnees["IDgroupe"]
        dictActivites = self.GetForfaits(IDactivite)
        for IDact, dictActivite in dictActivites.iteritems() :
            date_debut_activite = dictActivite["date_debut"]
            date_fin_activite = dictActivite["date_fin"]
        combinaisons = []
        for dateTemp, listeCombis in dictActivites[IDactivite]["ouvertures"][IDgroupe].iteritems() :
            if dateTemp >= date_debut_activite and (date_fin_activite == None or dateTemp <= date_fin_activite):
                combinaisons.append(tuple(listeCombis))
        combinaisons.sort()
        # Récupération des consommations à créer
        listeConsommations = []
        listeDatesStr = []
        for combi in combinaisons :
            for date, IDunite, IDgroupeTemp in combi :
                if IDgroupeTemp == IDgroupe or IDgroupeTemp == None :
                    listeConsommations.append( {"date" : date, "IDunite" : IDunite} )
                    if date not in listeDatesStr : listeDatesStr.append(str(date))
        # Vérifie que les dates ne sont pas déjà prises pour alerte conflit
        DB = aGestionDB.DB()
        if len(listeDatesStr) == 0 : conditionDates = "()"
        elif len(listeDatesStr) == 1 : conditionDates = "('%s')" % listeDatesStr[0]
        else : conditionDates = str(tuple(listeDatesStr))
        req = """SELECT IDconso, date, IDunite
        FROM consommations
        WHERE IDindividu=%d AND date IN %s
        ; """ % (dictDonnees["IDindividu"] , conditionDates)
        DB.ExecuterReq(req)
        listeConsoExistantes = DB.ResultatReq()
        DB.Close()
        listeDatesPrises = []
        for IDconso, dateConso, IDuniteConso in listeConsoExistantes :
            dateConso = DateEngEnDateDD(dateConso)
            if {"date" : dateConso, "IDunite" : IDuniteConso} in listeConsommations :
                if dateConso not in listeDatesPrises :
                    listeDatesPrises.append(dateConso)
        if len(listeDatesPrises) > 0 :
            texteDatesPrises = u""
            for datePrise in listeDatesPrises :
                texteDatesPrises += u"   > %s\n" % DateComplete(datePrise)
            dlg = wx.MessageDialog(None, _(u"Il est impossible d'enregistrer ! \n\nDes consommations existent déjà sur les dates suivantes :\n\n%s") % (texteDatesPrises), "Erreur", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        # Sauvegarde des consommations
        DB = aGestionDB.DB()
        for conso in listeConsommations :
            date = conso["date"]
            IDunite = conso["IDunite"]
            # Récupération des données
            if dictDonnees["nature"] in ("COM","FAC",):
                etatConsommation = "present"
            else : etatConsommation = "reservation"
            listeDonnees = [
                ("IDindividu", dictDonnees["IDindividu"]),
                ("IDinscription", dictDonnees["IDinscription"]),
                ("IDactivite", dictDonnees["IDactivite"]),
                ("date", str(date)),
                ("IDunite", IDunite),
                ("IDgroupe", IDgroupe),
                ("etat", etatConsommation),
                ("forfait", 2),
                ("verrouillage", False),
                ("date_saisie", str(datetime.date.today())),
                ("IDutilisateur", self.user),
                ("IDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
                ("IDcompte_payeur", dictDonnees["IDcompte_payeur"]),
                ]
            # Insertion des données
            retour = DB.ReqInsert("consommations", listeDonnees,MsgBox=True)
        DB.Close()
        return True
        #fin AjoutConsommations

    def AjoutPrestation(self,parent,dictDonnees,modif=False,recree=False) :
        # origine : DLG_Appliquer_forfait.Applique_forfait(self, selectionIDcategorie_tarif=None, selectionIDtarif=None, inscription=False, selectionIDactivite=None, labelTarif=None)
        nom_individu = dictDonnees["nom_individu"]
        nom_activite = dictDonnees["nom_activite"]
        nom_groupe = dictDonnees["nom_groupe"]
        # Prestation camp
        montant = 0.00
        for item in dictDonnees["lignes_piece"]:
            montant += item["montant"]
        if dictDonnees["prixTranspAller"]!=None:
            montant += dictDonnees["prixTranspAller"]
        if dictDonnees["prixTranspRetour"]!=None:
            montant += dictDonnees["prixTranspRetour"]
        if dictDonnees["nature"]=="AVO":
            montant = -montant
            modif = False
        # Sauvegarde de la prestation camp
        DB = aGestionDB.DB()
        listeDonnees = [
            ("IDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ("date", str(datetime.date.today())),
            ("categorie", "consommation"),
            ("label", nom_individu + " - " + nom_activite + " - " + nom_groupe),
            ("IDfacture", dictDonnees["noFacture"]),
            ("montant_initial", montant),
            ("montant", montant),
            ("forfait", 2),
            ("IDactivite",dictDonnees["IDactivite"]),
            ("IDfamille", dictDonnees["IDfamille"]),
            ("IDindividu", dictDonnees["IDindividu"]),
            ("IDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
            ("IDcontrat", dictDonnees["IDnumPiece"]),
            ]
        IDprestation = dictDonnees["IDprestation"]
        if modif:
            DB.ReqMAJ("prestations", listeDonnees,"IDprestation",IDprestation,MsgBox=True)
        elif recree:
            listeDonnees.append(("IDprestation",IDprestation))
            DB.ReqInsert("prestations", listeDonnees,retourID = True,MsgBox=True)
        else:
            DB.ReqInsert("prestations", listeDonnees,retourID = True,MsgBox=True)
            IDprestation = DB.newID
        DB.Close()
        return IDprestation
        # fin AjoutPrestation

    def AjoutPrestation999(self,parent,dictDonnees,modif = False) :
        # origine : DLG_Appliquer_forfait.Applique_forfait(self, selectionIDcategorie_tarif=None, selectionIDtarif=None, inscription=False, selectionIDactivite=None, labelTarif=None)
        montant = 0.00
        montantInit = 0.00
        for item in dictDonnees["lignes_piece"]:
            montantInit += item["quantite"] * item["prixUnit"]
            if item["montant"] != 0:
                montant += item["montant"]
            else: montant += (item["quantite"] * item["prixUnit"])
        if dictDonnees["nature"]=="AVO":
            montant = -montant
            montantInit = -montantInit
            modif = False
        # Sauvegarde de la prestation camp
        DB = aGestionDB.DB()
        listeDonnees = [
            ("IDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ("date", str(datetime.date.today())),
            ("categorie", "consommation"),
            ("label", "xxx Niveau familles payeur"),
            ("IDfacture", dictDonnees["noFacture"]),
            ("montant_initial", montantInit),
            ("montant", montant),
            ("forfait", 1),
            ("IDactivite",dictDonnees["IDactivite"]),
            ("IDfamille", dictDonnees["IDfamille"]),
            ("IDindividu", dictDonnees["IDindividu"]),
            ("IDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
            ("IDcontrat", dictDonnees["IDnumPiece"]),
            ]
        if modif :
            IDprestation = dictDonnees["IDprestation"]
            retour = DB.ReqMAJ("prestations", listeDonnees,"IDprestation",IDprestation)
        else:
            retour = DB.ReqInsert("prestations", listeDonnees,retourID = True)
            IDprestation = DB.newID
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
        DB.Close()
        return IDprestation
        # fin AjoutPrestation

    def AjoutFacture(self,dictDonnees,mode="FAC"):
        # Composition de l'enregistrement facture
        if mode == "FAC":
            numero = dictDonnees["noFacture"]
            type = "Origine Piece facture"
            datePiece = dictDonnees["dateFacturation"]
        else:
            numero = dictDonnees["noAvoir"]
            type = "Origine Piece Avoir"
            datePiece = dictDonnees["dateAvoir"]
        listeDonnees = [
            ("numero",numero),
            ("date_edition", datePiece),
            ("date_echeance", dictDonnees["dateEcheance"]),
            ("IDutilisateur", self.user),
            ("IDlot", 1),
            ("prestations", type),
            ("IDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ("activites",dictDonnees["IDactivite"]),
            ("individus",dictDonnees["IDindividu"]),
            ("date_debut",dictDonnees["dateCreation"]),
            ("date_fin",dictDonnees["dateModif"]),
            ("total",dictDonnees["total"]),
            ("regle",0),
            ("solde",dictDonnees["total"]),
           ]
        DB = aGestionDB.DB()
        retour = DB.ReqInsert("factures", listeDonnees,retourID = True,MsgBox=True)
        IDnumFacture = DB.newID
        # Modif de la prestation associée à la piece
        if dictDonnees["IDprestation"] != None:
            listeDonnees = [
                ("IDfacture", IDnumFacture),
                ]
            DB.ReqMAJ("prestations", listeDonnees,"IDprestation",dictDonnees["IDprestation"],MsgBox=True)
        #fin AjoutFacture

    def GetPieceModif(self,parent,IDindividu,IDactivite,IDnumPiece = None):
        dicoDB = aDATA_Tables.DB_DATA
        listeChamps = []
        for descr in dicoDB["matPieces"]:
            nomChamp = descr[0]
            #typeChamp = descr[1]
            listeChamps.append(nomChamp)
        if IDnumPiece== None:
            #la recherche se fait prioritairement sur le IDnumPiece s'il est connu
            conditions = "pieIDindividu= %d AND pieIDactivite = %d;" % (IDindividu,IDactivite)
        else: conditions = "pieIDnumPiece= %d" % (IDnumPiece)
        req =  "SELECT * FROM matPieces WHERE " + conditions
        DB = aGestionDB.DB()
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
            return False
        retour = DB.ResultatReq()
        self.nbPieces = len(retour)
        if self.nbPieces == 0 :
            aGestionDB.MessageBox(parent,"Anomalie : Rien dans matPieces pour cette inscription => pas de modif possible")
            return False
        if self.nbPieces == 1:
            self.dictPiece = self.DictTrack(listeChamps,retour[0])
        else:
            retour = self.ChoixPiece(retour)
            if retour == None:
                return False
            self.dictPiece = self.DictTrack(listeChamps,retour)
        # Appel des lignes de la pièce pour ajouter dans le dictPiece
        listeChamps = []
        for descr in dicoDB["matPiecesLignes"]:
            nomChamp = descr[0]
            listeChamps.append(nomChamp)
        conditions = "ligIDnumPiece= %d ;" % (self.dictPiece["IDnumPiece"])
        req =  "SELECT * FROM matPiecesLignes WHERE " + conditions
        DB = aGestionDB.DB()
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
            return False
        retour = DB.ResultatReq()
        listeLignes = []
        total = 0.00
        for ligne in retour:
            dicLigne = self.DictTrack(listeChamps,ligne,prefixe="lig")
            listeLignes.append(dicLigne)
            total += dicLigne["montant"]
        self.dictPiece["lignes_piece"] = listeLignes
        self.dictPiece["total"] = total
        self.dictPiece["nom_individu"] = DB.GetNomIndividu(self.dictPiece["IDindividu"])
        self.dictPiece["nom_famille"] = DB.GetNomIndividu(self.dictPiece["IDfamille"])
        self.dictPiece["nom_payeur"] = DB.GetNomIndividu(self.dictPiece["IDcompte_payeur"])
        self.dictPiece["nom_activite"] = DB.GetNomActivite(self.dictPiece["IDactivite"])
        self.dictPiece["nom_groupe"] = DB.GetNomGroupe(self.dictPiece["IDgroupe"])
        if self.dictPiece["IDcategorie_tarif"] == None:
            self.dictPiece["nom_categorie_tarif"]="Famille"
        else: self.dictPiece["nom_categorie_tarif"] = DB.GetNomCategorieTarif(self.dictPiece["IDcategorie_tarif"])
        DB.Close()
        return True
        #fin GetPieceModif

    def GetPieceModif999(self,parent,IDpayeur,saison, IDnumPiece = None):
        self.IDpayeur = IDpayeur
        dicoDB = aDATA_Tables.DB_DATA
        listeChamps = []
        for descr in dicoDB["matPieces"]:
            nomChamp = descr[0]
            listeChamps.append(nomChamp)
        if IDnumPiece == None:
            if parent.facture==True:
                conditions = "(pieNoFacture IS NOT Null) AND (pieIDcompte_payeur= %d AND pieIDinscription = %d);" % (IDpayeur,saison)
            else: conditions = "pieNoFacture IS Null AND pieIDcompte_payeur= %d AND pieIDinscription = %d;" % (IDpayeur,saison)
        else:
            conditions = " pieIDnumPiece = %d ; " % IDnumPiece
        req =  "SELECT * FROM matPieces WHERE " + conditions
        DB = aGestionDB.DB()
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            aGestionDB.MessageBox(self.parent,retour)
            return False
        retour = DB.ResultatReq()
        self.nbPieces = len(retour)
        if self.nbPieces == 0 :
            return False
        if self.nbPieces == 1:
            self.dictPiece = self.DictTrack(listeChamps,retour[0])
        else:
            retour = self.ChoixPiece(retour)
            if retour == None:
                return False
            self.dictPiece = self.DictTrack(listeChamps,retour)
        # Appel des lignes de la pièce pour ajouter dans le dictPiece
        listeChamps = []
        for descr in dicoDB["matPiecesLignes"]:
            nomChamp = descr[0]
            listeChamps.append(nomChamp)
        conditions = "ligIDnumPiece= %d ;" % (self.dictPiece["IDnumPiece"])
        req =  "SELECT * FROM matPiecesLignes WHERE " + conditions
        DB = aGestionDB.DB()
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
            return False
        retour = DB.ResultatReq()
        listeLignes = []
        for ligne in retour:
            listeLignes.append(self.DictTrack(listeChamps,ligne,prefixe="lig"))
        self.dictPiece["lignes_piece"] = listeLignes
        self.dictPiece["nom_payeur"] = DB.GetNomIndividu(self.IDpayeur)
        DB.Close()
        return True
        #fin GetPieceModif999

    def ModifiePieceCree(self,parent,dictDonnees):
        DB = aGestionDB.DB()
        listeDonnees = [
            ("pieIDinscription", dictDonnees["IDinscription"]),
            ("pieIDprestation", dictDonnees["IDprestation"]),
            ("pieNature", dictDonnees["nature"]),
            ("pieEtat",dictDonnees["etat"]),
            ("pieIDtranspAller", dictDonnees["IDtranspAller"]),
            ("piePrixTranspAller", dictDonnees["prixTranspAller"]),
            ("pieIDtranspRetour", dictDonnees["IDtranspRetour"]),
            ("piePrixTranspRetour", dictDonnees["prixTranspRetour"]),
            ("pieIDparrain",dictDonnees["IDparrain"]),
            ("pieParrainAbandon",dictDonnees["parrainAbandon"]),
            ]
        retour = DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",dictDonnees["IDnumPiece"],MsgBox=True)
        DB.Close()
        return retour

    def ModifieInscription(self,parent,dictDonnees):
        if dictDonnees["nature"]=="AVO":
            return
        DB = aGestionDB.DB()
        listeDonnees = [
            ("IDindividu", dictDonnees["IDindividu"] ),
            ("IDfamille", dictDonnees["IDfamille"] ),
            ("IDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ("IDactivite", dictDonnees["IDactivite"]),
            ("IDgroupe", dictDonnees["IDgroupe"]),
            ("IDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
            ]
        retour = DB.ReqMAJ("inscriptions", listeDonnees,"IDinscription",dictDonnees["IDinscription"])
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
        DB.Close()
        return retour

    def ModifiePiece(self,parent,dictDonnees):
        # Recherche des paramétres de l'activité
        if dictDonnees["nature"]=="FAC":
            dd = None
            dictActivites = self.GetForfaits(dictDonnees["IDactivite"])
            for IDact, dictActivite in dictActivites.iteritems() :
                dd = dictActivite["date_debut"]
            dictDonnees["dateEcheance"] = dd
            dictDonnees["dateFacturation"] = str(datetime.date.today())
        else:
            if dictDonnees["nature"]!="AVO":
                dictDonnees["dateFacturation"] = None
                dictDonnees["noFacture"] = None
                dictDonnees["echeance"] = None
        listeDonnees = [
            ("pieIDinscription", dictDonnees["IDinscription"]),
            ("pieIDprestation", dictDonnees["IDprestation"]),
            ("pieIDindividu", dictDonnees["IDindividu"]),
            ("pieIDfamille", dictDonnees["IDfamille"]),
            ("pieIDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ("pieIDactivite", dictDonnees["IDactivite"]),
            ("pieIDgroupe", dictDonnees["IDgroupe"]),
            ("pieIDcategorie_tarif", dictDonnees["IDcategorie_tarif"]),
            ("pieDateModif",str(datetime.date.today())),
            ("pieUtilisateurModif",self.user),
            ("pieNature", dictDonnees["nature"]),
            ("pieEtat",dictDonnees["etat"]),
            ("pieDateFacturation", dictDonnees["dateFacturation"]),
            ("pieNoFacture", dictDonnees["noFacture"]),
            ("pieDateEcheance", dictDonnees["dateEcheance"]),
            ("pieCommentaire", dictDonnees["commentaire"]),
            ("pieIDtranspAller", dictDonnees["IDtranspAller"]),
            ("piePrixTranspAller", dictDonnees["prixTranspAller"]),
            ("pieIDtranspRetour", dictDonnees["IDtranspRetour"]),
            ("piePrixTranspRetour", dictDonnees["prixTranspRetour"]),
            ("pieIDparrain",dictDonnees["IDparrain"]),
            ("pieParrainAbandon",dictDonnees["parrainAbandon"]),
            ]
        if dictDonnees["nature"]=="AVO":
            listeDonnees.append(("pieNoAvoir",dictDonnees["noAvoir"]))
            listeDonnees.append(("pieDateAvoir",datetime.date.today()))
        DB = aGestionDB.DB()
        retour = DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",dictDonnees["IDnumPiece"])
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
            DB.Close()
            return None
        if dictDonnees["nature"]=="AVO":
            return None
        # Purge les lignes précédentes
        ret = DB.ReqDEL("matPiecesLignes", "ligIDNumPiece",dictDonnees["IDnumPiece"])
        # Enregistre dans PiecesLignes
        listeInit = [
            ("ligIDnumPiece", dictDonnees["IDnumPiece"]),
            ("ligDate",str(datetime.date.today())),
            ("ligUtilisateur", self.user),
            ]
        # recalcul du montant non forcé pour stockage avec valeur
        for item in dictDonnees["lignes_piece"]:
            if item["montant"] == 0:
                item["montant"] = (item["quantite"] * item["prixUnit"])

        listeLignesPiece = dictDonnees["lignes_piece"]
        if listeLignesPiece != None:
            for ligne in listeLignesPiece:
                listeDonnees = listeInit[:]
                listeDonnees.append(("ligCodeArticle",ligne["codeArticle"]))
                listeDonnees.append(("ligLibelle",ligne["libelle"]))
                listeDonnees.append(("ligQuantite",ligne["quantite"]))
                listeDonnees.append(("ligPrixUnit",ligne["prixUnit"]))
                listeDonnees.append(("ligMontant",ligne["montant"]))
                retour = DB.ReqInsert("matPiecesLignes", listeDonnees,retourID = False)
                if retour != "ok" :
                    aGestionDB.MessageBox(parent,retour)
                    DB.Close()
                    return None
        DB.Close()
        return retour
        #fin ModifiePiece

    def MajNoAvoir(self,parent, dictDonnees):
        #modif  de la piece facture qui devient avoir
        DB = aGestionDB.DB()
        listeDonnees = [
            ("pieDateModif",datetime.date.today()),
            ("pieUtilisateurModif",DB.UtilisateurActuel()),
            ("pieNature","AVO"),
            ("pieEtat",dictDonnees["etat"]),
            ("pieDateAvoir", datetime.date.today()),
            ("pieNoAvoir",dictDonnees["noAvoir"]),
            ("pieCommentaire",dictDonnees["commentaire"]),
            ]
        retour = DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",dictDonnees["IDnumPiece"])
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
        DB.Close()
        return

    def MajNoFact(self,parent, piece, listeDonneesFacture, IDnumFacture):
        #transformation de la liste de tuples en dictionnaire
        listeChampsFacture = []
        listeValeursFacture = []
        for champ, valeur in listeDonneesFacture:
            listeChampsFacture.append(champ)
            listeValeursFacture.append(valeur)
        dictFacture = self.DictTrack(listeChampsFacture,listeValeursFacture,"xxx")
        # modif de la pièce facturée
        etat = piece.etat[:3]+"1"+piece.etat[4:]
        DB = aGestionDB.DB()
        listeDonnees = [
            ("pieDateModif",dictFacture["date_edition"]),
            ("pieUtilisateurModif",DB.UtilisateurActuel()),
            ("pieNature","FAC"),
            ("pieEtat",etat),
            ("pieDateFacturation", dictFacture["date_edition"]),
            ("pieNoFacture",dictFacture["numero"]),
            ("pieDateEcheance", dictFacture["date_echeance"]),
            ]
        retour = DB.ReqMAJ("matPieces", listeDonnees,"pieIDnumPiece",piece.IDnumPiece)
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
            DB.Close()
            return None
        # Modif de la prestation associée à la piece
        if piece.IDprestation == None:
            if not piece.nature in ("DEV","RES"):
                aGestionDB.MessageBox(parent,"la piece %d est sans prestation associée" % piece.IDnumPiece)
            DB.Close()
            return None
        listeDonnees = [
            ("IDfacture", IDnumFacture),
            ]
        retour = DB.ReqMAJ("prestations", listeDonnees,"IDprestation",piece.IDprestation)
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
            DB.Close()
            return None
        DB.Close()
        return True
        #fin MajNoFact

    def ModifieConsommations(self,parent,dictDonnees):
        DB = aGestionDB.DB()
        DB.ReqDEL("consommations", "IDinscription", dictDonnees["IDinscription"])
        DB.Close()
        if dictDonnees["nature"]=="AVO":
            return
        self.AjoutConsommations(parent,dictDonnees)
        return retour

    def ModifieConsoCree(self,parent,dictDonnees):
        DB = aGestionDB.DB()
        listeDonnees = [
            ("IDprestation", dictDonnees["IDprestation"]),
            ("IDcompte_payeur", dictDonnees["IDcompte_payeur"]),
            ]
        retour = DB.ReqMAJ("consommations", listeDonnees,"IDinscription",dictDonnees["IDinscription"])
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
        return retour

    def PieceModifiable(self,parent,dictDonnees) :
        if len(dictDonnees["etat"])<4 : return True
        etatFacture = int(dictDonnees["etat"][3])
        if dictDonnees["nature"] in ("FAC"):
            if etatFacture > 2:return False
            return True
        if dictDonnees["nature"] in ("AVO"):
            if etatFacture > 2:return False
            return True
        return True

    def PieceSuppressible(self,parent,dictDonnees) :
        if len(dictDonnees["etat"])<4 : return True
        etatFacture = int(dictDonnees["etat"][3])
        if dictDonnees["nature"] in ("FAC"):
            if etatFacture > 2:
                return False
            return True
        if dictDonnees["nature"] in ("AVO"):
            if etatFacture > 2:return False
        return True

    def SuppressionInscription(self,dictDonnees):
        DB = aGestionDB.DB()
        #pour chaque inscription suppression des consos et des inscriptions
        conditions = "IDindividu = %d AND IDactivite = %d;" % (dictDonnees ["IDindividu"] ,dictDonnees ["IDactivite"])
        req =  "SELECT * FROM inscriptions WHERE " + conditions
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            aGestionDB.MessageBox(self.parent,retour)
            return False
        retour = DB.ResultatReq()
        for ligne in retour :
            IDinscription = ligne[0]
            if IDinscription != None:
                DB.ReqDEL("consommations", "IDinscription", IDinscription)
                DB.ReqDEL("inscriptions", "IDinscription", IDinscription)
        #supression de toutes les prestations de cet individu activité
        req =  "SELECT * FROM prestations WHERE " + conditions
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            aGestionDB.MessageBox(self.parent,retour)
            return False
        retour = DB.ResultatReq()
        for ligne in retour :
            IDprestation = ligne[0]
            DB.ReqDEL("deductions", "IDprestation", IDprestation)
            DB.ReqDEL("ventilation", "IDprestation", IDprestation)
            DB.ReqDEL("prestations", "IDprestation", IDprestation)
        DB.Close()

    def GetPieceSupprime(self,parent,IDinscription,IDindividu,IDactivite):
        #retourne False pour abandon, True pour suppresion sans piece, None pour self.dictPiece alimentée
        self.dictPiece = {}
        DB = aGestionDB.DB()
        listeChamps = ["pieIDnumPiece", "pieIDinscription", "pieIDprestation", "pieIDfamille","pieDateCreation", "pieUtilisateurCreateur", "pieNature", "pieNature", "pieEtat", "pieCommentaire"]
        champs=" "
        for item in listeChamps :
            champs = champs + item +","
        champs = champs[:-1]
        conditions = "pieIDindividu= %d AND pieIDactivite = %d;" % (IDindividu,IDactivite)
        req =  "SELECT" + champs + " FROM matPieces WHERE " + conditions
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
            return False
        retour = DB.ResultatReq()
        self.nbPieces = len(retour)
        if self.nbPieces == 0 :
            aGestionDB.MessageBox(parent,"Anomalie : Rien dans matPieces pour cette inscription, pas de suppression de prestation")
            return True
        if self.nbPieces == 1:
            if IDinscription == retour[0][1]:
                reqPiece = self.GetPieceModif(self.parent,IDindividu,IDactivite)
                if reqPiece: return None
                else: return False
            #la piece ne correspond pas à l'inscription
            else:
                reqPiece = self.GetPieceModif(retour[0][1],IDindividu,IDactivite)
                if reqPiece:
                    dlg = aGestionDB.MessageBox(parent, _(u"Confirmez_vous la suppression car NoInscription dans piece différent "), titre = "Confirmation")
                    if dlg:
                        self.nbPieces = 2
                        return None
                return False
        else:
            # On demande quelle piece supprimer  et on récupére l'IDinscription
            reqPiece = self.GetPieceModif(self.parent,IDindividu,IDactivite)
        return None
        #fin GetPieceSupprime

    def Suppression(self,parent,dictDonnees,nbPieces):
        IDinscription = dictDonnees["IDinscription"]
        IDprestation = dictDonnees["IDprestation"]
        IDnumPiece = dictDonnees["IDnumPiece"]
        DB = aGestionDB.DB()
        DB.ReqDEL("matPiecesLignes", "ligIDNumPiece", IDnumPiece)
        DB.ReqDEL("matPieces", "pieIDNumPiece", IDnumPiece)
        # stockage du numéro de facture et d'avoir
        if dictDonnees["noFacture"] != None:
            DB.SetParam(param = str(dictDonnees["noFacture"]),value= dictDonnees["noFacture"],user = "NoLibre")
            DB.ReqDEL("factures", "numero", dictDonnees["noFacture"])
        if dictDonnees["noAvoir"] != None:
            DB.SetParam(param = str(dictDonnees["noFacture"]),value= dictDonnees["noAvoir"],user = "NoLibre")
            DB.ReqDEL("factures", "numero", dictDonnees["noAvoir"])
        if IDinscription != None:
            DB.ReqDEL("consommations", "IDinscription", IDinscription)
        if IDprestation != None:
            DB.ReqDEL("deductions", "IDprestation", IDprestation)
            DB.ReqDEL("ventilation", "IDprestation", IDprestation)
            DB.ReqDEL("prestations", "IDprestation", IDprestation)
        if nbPieces == 1:
            DB.ReqDEL("inscriptions", "IDinscription", IDinscription)
        DB.Close()

    def GetDictDonnees(self,parent,listeDonnees):
        DB = aGestionDB.DB()
        nom_individu = DB.GetNomIndividu(parent.IDindividu)
        nom_famille = DB.GetNomIndividu(parent.IDfamille)
        DB.Close()
        listeDonnees2 = [
            ("nom_individu", nom_individu),
            ("nom_famille", nom_famille),
            ]
        dictDonnees = {}
        for donnee in listeDonnees + listeDonnees2 :
            champ = donnee[0]
            valeur = donnee[1]
            dictDonnees[champ] = valeur
        return dictDonnees
        #fin GetDictDonnees

    def ModifDictDonnees(self,parent,listeDonnees):
        dictDonnees = parent.dictDonnees
        for donnee in listeDonnees :
            champ = donnee[0]
            valeur = donnee[1]
            dictDonnees[champ] = valeur
        return dictDonnees
        #fin AjoutDictDonnees

    def GetPayeurFamille(self,parent, IDfamille = None) :
        #Récupère le compte_payeur par défaut de la famille
        DB = aGestionDB.DB()
        req = """SELECT IDfamille, IDcompte_payeur
        FROM familles
        WHERE IDfamille=%d;""" % IDfamille
        retour = DB.ExecuterReq(req)
        if retour != "ok" :
            aGestionDB.MessageBox(parent,retour)
            return None
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0 : return None
        IDcompte_payeur = listeDonnees[0][1]
        return IDcompte_payeur

    def GetFamille(self,parent):
        # Fixe IDfamille listeFamille (unique) listeNOms (des membres ) si l'individu est rattaché à d'autres familles
        parent.listeNoms = []
        parent.listeFamille = []
        # Vérifie que l'individu est rattaché comme REPRESENTANT ou ENFANT à une famille
        if parent.dictFamillesRattachees == None: return False
        valide = False
        self.nbreFamilles = 0
        msg = aGestionDB.Messages()
        lastIDfamille = None
        for parent.IDfamille, dictFamille in parent.dictFamillesRattachees.iteritems() :
            if dictFamille["IDcategorie"] in (1, 2) :
                self.nbreFamilles += 1
                lastIDfamille = parent.IDfamille
                valide = True
        if valide == False :
            msg.Box(message = u"Pour être inscrit à une activité, un individu doit obligatoirement être\nrattaché comme représentant ou enfant à une fiche famille !")
            return False
        if self.nbreFamilles == 1 :
            parent.IDfamille = lastIDfamille
            parent.listeFamille.append(lastIDfamille)
            parent.listeNoms.append(parent.dictFamillesRattachees[parent.IDfamille]["nomsTitulaires"])
        else:
            # Si rattachée à plusieurs familles
            listeTuplesFamilles = []
            for IDfamille, dictFamille in parent.dictFamillesRattachees.iteritems() :
                IDcategorie = dictFamille["IDcategorie"]
                if IDcategorie in (1, 2) :
                    parent.listeFamille.append(IDfamille)
                    parent.listeNoms.append(dictFamille["nomsTitulaires"])
                    listeTuplesFamilles.append((IDfamille,dictFamille["nomsTitulaires"]))
            # On demande à quelle famille rattacher cette inscription
            retour = aGestionDB.Messages().Choix(listeTuples=listeTuplesFamilles, titre = (u"Cet individu est rattaché à %d familles")% len(parent.listeNoms), intro = u"Double clic pour rattacher cette inscription à une famille !")
            ixChoix = retour[0]
            famille = retour[1]
            if  ixChoix != None:
                parent.IDfamille = ixChoix
                parent.nom_famille = famille
            else:
                return False
        return True
        #fin GetFamille

    def GetListeActivites(self,parent):
        """ Retourne la liste des activités sur lesquelles l'individu est inscrit """
        """ Sert pour le ctrl DLG_Individu_inscriptions (saisir d'un forfait daté)"""
        listeActivites = []
        for track in parent.listeListeView :
            listeActivites.append(track.parent.parent.IDactivite)
        listeActivites.sort()
        return listeActivites

    def CoherenceOrphelines(self,IDpayeur):
        DB = aGestionDB.DB()
        retourFin = True
        debut=DB.GetParam(param="DebutCoherence",type="string",user = "Any")
        if debut == None:
            debut = "2016-09-01"
            DB.SetParam(param="DebutCoherence", value=debut, type="string", user = "Any")

        # Recherche des pièces du payeur à tester
        #                       0           1           2               3           4               5             6            7       8       9           10       11          12                  13
        #lstChampsPiece = ["IDnumPiece","IDindividu","nomIndividu","IDactivite","nomActivite","IDprestation","IDinscription","nature","etat","noFacture","noAvoir","montant","PrixTranspAller","PrixTranspRetour"]
        req = """SELECT  matPieces.pieIDnumPiece,matPieces.pieIDindividu,individus.prenom,matPieces.pieIDactivite,activites.nom,matPieces.pieIDprestation,matPieces.pieIDinscription, matPieces.pieNature,matPieces.pieEtat,matPieces.pieNoFacture,matPieces.pieNoAvoir, SUM(matPiecesLignes.ligMontant),matPieces.piePrixTranspAller,matPieces.piePrixTranspRetour
                FROM matPieces
                LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece
                LEFT JOIN individus ON matPieces.pieIDindividu = individus.IDindividu
                LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
                WHERE matPieces.pieIDcompte_payeur = %s AND matPieces.pieDateCreation >= %s
                GROUP BY  matPieces.piedateCreation,matPieces.pieIDnumPiece, matPieces.pieIDindividu, individus.prenom, matPieces.pieIDactivite, activites.nom, matPieces.pieIDprestation,matPieces.pieNature,matPieces.pieEtat,matPieces.pieNoFacture,matPieces.pieNoAvoir
                ;""" % (IDpayeur,debut)
        DB.ExecuterReq(req,MsgBox=True)
        recordsetPieces = DB.ResultatReq()
        lstPieIndividus = []
        lstPieActivites = []
        lstPieInscriptions = []
        lstPiePrestations = []
        lstPieFactures = []
        for piece in recordsetPieces:
            lstPieIndividus.append(piece[1])
            lstPieActivites.append(piece[3])
            lstPieInscriptions.append(piece[6])
            lstPiePrestations.append(piece[5])
            if piece[9] != None:
                lstPieFactures.append(piece[9])
            if piece[10] != None:
                lstPieFactures.append(piece[10])
        texte = u"\n"

        # Recherche Inscriptions orphelines de pièce
        #           ["IDinscription","IDindividu","nomIndividu","IDactivite","nomActivite"]
        req = """SELECT inscriptions.IDinscription, inscriptions.IDindividu, individus.prenom, inscriptions.IDactivite, activites.nom
                FROM inscriptions
                INNER JOIN individus ON inscriptions.IDindividu = individus.IDindividu
                INNER JOIN activites ON inscriptions.IDactivite = activites.IDactivite
                WHERE inscriptions.IDcompte_payeur = %s AND inscriptions.date_inscription >= %s ;""" % (IDpayeur, debut)
        DB.ExecuterReq(req,MsgBox=True)
        recordset = DB.ResultatReq()
        lstIDinscriptionsOrphelines=[]

        for inscription in recordset:
            if not ((inscription[1] in lstPieIndividus) and (inscription[3] in lstPieActivites)):
                lstIDinscriptionsOrphelines.append(inscription[0])
                # composition du message pour les inscriptions orphelines
                if inscription[2] == None: txtInd = str(inscription[1])
                else: txtInd = str(inscription[1]) + " - " + inscription[2]
                if inscription[4] == None: txtAct = str(inscription[3])
                else: txtAct =  str(inscription[3]) + " - " + inscription[4]
                texte = texte + "Inscription : " + txtInd + u", activité : " + txtAct + "\n"

        # Recherche Consommations orphelines de pièce
        #       ["IDconsommation","IDindividu","nomIndividu","IDactivite","nomActivite","IDinscription]
        req = """SELECT consommations.IDconso, consommations.IDindividu, individus.prenom, consommations.IDactivite, activites.nom, consommations.IDinscription
                FROM consommations
                INNER JOIN individus ON consommations.IDindividu = individus.IDindividu
                INNER JOIN activites ON consommations.IDactivite = activites.IDactivite
                WHERE consommations.IDcompte_payeur = %s AND consommations.date_saisie >= %s ;""" % (IDpayeur, debut)
        DB.ExecuterReq(req,MsgBox=True)
        recordset = DB.ResultatReq()
        lstIDconsommationsOrphelines=[]
        lstIDindividus=[]
        for consommation in recordset:
            if not ((consommation[1] in lstPieIndividus) and (consommation[3] in lstPieActivites)and (consommation[5] in lstPieInscriptions)):
                lstIDconsommationsOrphelines.append(consommation[0])
                # regroupement des messages consommations
                if not consommation[1] in lstIDindividus:
                    lstIDindividus.append(consommation[1])
                    # composition du message pour les consommations orphelines
                    if consommation[2] == None: txtInd = str(consommation[1])
                    else: txtInd = str(consommation[1]) + " - " + consommation[2]
                    if consommation[4] == None: txtAct = str(consommation[3])
                    else: txtAct = str(consommation[3]) + " - " + consommation[4]
                    texte = texte + "Consommations : " + txtInd + u", activité : " + txtAct + "\n"

        # Recherche Prestations orphelines de pièce
        #       ["IDprestation","IDindividu","nomIndividu","IDactivite","nomActivite","montant","IDfacture"]
        req = """SELECT prestations.IDprestation, prestations.IDindividu, individus.prenom, prestations.IDactivite, activites.nom, prestations.montant,prestations.IDfacture
                FROM prestations
                INNER JOIN individus ON prestations.IDindividu = individus.IDindividu
                INNER JOIN activites ON prestations.IDactivite = activites.IDactivite
                WHERE prestations.forfait = 2 AND prestations.IDcompte_payeur = %s AND prestations.date >= %s ;""" % (IDpayeur, debut)
        DB.ExecuterReq(req,MsgBox=True)
        recordset = DB.ResultatReq()
        lstIDprestationsOrphelines=[]
        lstIDindividus=[]
        for prestation in recordset:
            if not ((prestation[1] in lstPieIndividus) and (prestation[3] in lstPieActivites)and (prestation[0] in lstPiePrestations)):
                lstIDprestationsOrphelines.append((prestation[0],prestation[6],prestation[5]))
                # regroupement des messages prestations
                if not prestation[1] in lstIDindividus:
                    lstIDindividus.append(prestation[1])
                    # composition du message pour les prestations orphelines
                    if prestation[2] == None: txtInd = "Famille"
                    else: txtInd = str(prestation[1]) + " - " + prestation[2]
                    texte = texte + "Prestation : " + txtInd + u", activité :" + txtAct + "\n"
            for piece in recordsetPieces:
                if prestation[0] == piece[5]:
                    if (prestation[5] != (piece[11] + piece[12] + piece[13])) or not(piece[7] in ["RES","COM","FAC","AVO"]):
                        texte = texte + "Pb Montant Prestation - Piece " + "\n"

        # Recherche Factures-Factures orphelines de pièce
        req = """SELECT factures.IDfacture, factures.numero, factures.total
                FROM factures
                LEFT JOIN matPieces ON factures.numero = matPieces.pieNoFacture
                WHERE matPieces.pieIDnumPiece Is Null
                    AND factures.IDcompte_payeur = %s
                    AND factures.date_edition >= %s ;""" % (IDpayeur, debut)
        DB.ExecuterReq(req,MsgBox=True)
        recordset = DB.ResultatReq()
        lstIDfacturesOrphelines=[]
        for facture in recordset:
            if not (facture[0] in lstIDfacturesOrphelines):
                if not (facture[1] in lstPieFactures):
                    lstIDfacturesOrphelines.append((facture[0],facture[1],facture[2]))
                    # composition du message pour les prestations orphelines
                    texte = texte + "Facture No : " + str(facture[1]) + " de "+ str(facture[2]) +" euros\n"
        # Recherche Factures-Avoir orphelines de pièce
        req = """SELECT factures.IDfacture, factures.numero, factures.total
                FROM factures
                LEFT JOIN matPieces ON factures.numero = matPieces.pieNoAvoir
                WHERE matPieces.pieIDnumPiece Is Null AND factures.prestations = "avoir"
                AND factures.IDcompte_payeur = %s AND factures.date_edition >= %s ;""" % (IDpayeur, debut)
        DB.ExecuterReq(req,MsgBox=True)
        recordset = DB.ResultatReq()
        for facture in recordset:
            if not (facture[0] in lstIDfacturesOrphelines):
                lstIDfacturesOrphelines.append((facture[0],facture[1]))
                # composition du message pour les prestations orphelines
                texte = texte + "Avoir No : " + str(facture[1]) + " de "+ str(facture[2]) +" euros\n"

        # Purge des lignes orphelines de pièce
        if texte != u"\n":
            retourFin = False
            # Confirmation de suppression
            dlg = wx.MessageDialog(self.parent, _(u"Les incohérences suivantes sont relevées !" + texte), _(u"Purge des lignes orphelines de pièce"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES :
                for ID in lstIDinscriptionsOrphelines:
                    DB.ReqDEL("inscriptions","IDinscription",ID,True,MsgBox=True)
                for ID in lstIDconsommationsOrphelines:
                    DB.ReqDEL("consommations","IDconso",ID,True,MsgBox=True)
                for ID,IDfacture,montant in lstIDprestationsOrphelines:
                    DB.ReqDEL("prestations","IDprestation",ID,True,MsgBox=True)
                    DB.ReqDEL("ventilations","IDprestation",ID,True,MsgBox=True)
                    if IDfacture != None:
                        #vérification du montant de la facture
                        req = """SELECT factures.Total,matPieces.pieIDnumPiece
                                FROM factures
                                INNER JOIN matPieces ON factures.numero = matPieces.pieNoFacture
                                WHERE facture.IDfacture = %s ;""" % (IDfacture)
                        DB.ExecuterReq(req,MsgBox=True)
                        lstPiecesFacture = DB.ResultatReq()
                        total = 0
                        mtt = 0.00
                        for mttFacture,IDnumPiece in lstPiecesFacture:
                            total = mttFacture
                            req= """SELECT SUM(ligMontant)
                                FROM matPiecesLignes
                                WHERE ligIDnumPiece = %s ;""" % (IDnumPiece)
                            DB.ExecuterReq(req,MsgBox=True)
                            retour = DB.ResultatReq()
                            if len(retour) >0:
                                mtt += float(retour[0][0])
                        if total != mtt:
                            listeDonnees = [("Total",mtt),]
                            DB.ReqMAJ("factures",listeDonnees,"IDfacture",IDfacture,MsgBox=True)
                for facture in lstIDfacturesOrphelines:
                    DB.ReqDEL("factures","IDfacture",facture[0],MsgBox=True)
                retourFin= True
        DB.Close()
        return retourFin
        #fin CoherenceOrphelines

    def CoherenceVeuves(self,IDpayeur):
        DB = aGestionDB.DB()
        retourFin = True
        debut=DB.GetParam(param="DebutCoherence",type="string",user = "Any")
        if debut == None:
            debut = "2016-09-01"
            DB.SetParam(param="DebutCoherence", value=debut, type="string", user = "Any")

        # Recherche des pièces du payeur à tester
        dicoDB = aDATA_Tables.DB_DATA
        lstChampsPiece = []
        for descr in dicoDB["matPieces"]:
            nomChamp = descr[0]
            lstChampsPiece.append(nomChamp)
        champs = aGestionDB.ListeToStr(lstChampsPiece)
        champs +=", individus.nom, activites.nom"
        lstChampsPiece.append("nomIndividu")
        lstChampsPiece.append("nomActivite")
        req = """SELECT %s
                FROM matPieces
                LEFT JOIN matPiecesLignes ON matPieces.pieIDnumPiece = matPiecesLignes.ligIDnumPiece
                LEFT JOIN individus ON matPieces.pieIDindividu = individus.IDindividu
                LEFT JOIN activites ON matPieces.pieIDactivite = activites.IDactivite
                WHERE matPieces.pieIDcompte_payeur = %s AND matPieces.pieDateCreation >= %s
                GROUP BY  matPieces.piedateCreation,matPieces.pieIDnumPiece, matPieces.pieIDindividu, individus.prenom, matPieces.pieIDactivite, activites.nom, matPieces.pieIDprestation,matPieces.pieNature,matPieces.pieEtat,matPieces.pieNoFacture,matPieces.pieNoAvoir
                ;""" % (champs,IDpayeur,debut)
        DB.ExecuterReq(req,MsgBox=True)
        recordsetPieces = DB.ResultatReq()
        lstPieInscriptions = []
        lstPieConsommations = []
        lstPiePrestations = []
        lstPieFactures = []
        lstDictPieces = []
        texte = u"\n"
        for piece in recordsetPieces:
            dictPiece = self.DictTrack(lstChampsPiece,piece)
            if dictPiece["nomActivite"] == None: dictPiece["nomActivite"]=" * "
            if dictPiece["nomIndividu"] == None: dictPiece["nomIndividu"]=" * "
            lstDictPieces.append(dictPiece)

        # Recherche Inscriptions manquantes
        for dictPiece in lstDictPieces:
            if dictPiece["nature"] != "AVO" and dictPiece["IDindividu"]!=0:
                condition = "IDinscription = %s" % dictPiece["IDinscription"]
                DB.ReqSelect("inscriptions",condition,MsgBox=True)
                recordset = DB.ResultatReq()
                if len(recordset) == 0:
                    if dictPiece["nomIndividu"] == None: dictPiece["nomIndividu"]= ""
                    if dictPiece["nomActivite"] == None: dictPiece["nomActivite"]= ""
                    lstPieInscriptions.append(dictPiece["IDinscription"])
                    texte += "Manque Inscription: " + str(dictPiece["IDinscription"]) + " - "  + dictPiece["nomIndividu"] + " - " + dictPiece["nomActivite"] + "\n"

        # Recherche Consommations manquantes
        for dictPiece in lstDictPieces:
            if (not dictPiece["nature"] in ["AVO","DEV"]) and dictPiece["IDindividu"]!=0:
                condition = "IDinscription = %s" % dictPiece["IDinscription"]
                DB.ReqSelect("consommations",condition,MsgBox=True)
                recordset = DB.ResultatReq()
                if len(recordset) == 0:
                    lstPieConsommations.append(dictPiece["IDinscription"])
                    texte += "Manque Conso/Inscription: " + str(dictPiece["IDinscription"]) + " - "  + dictPiece["nomIndividu"] + " - " + dictPiece["nomActivite"] + "\n"

        # Recherche Prestations manquantes
        for dictPiece in lstDictPieces:
            if not dictPiece["nature"] in ["AVO","DEV","RES"]:
                condition = "IDprestation = %s" % dictPiece["IDprestation"]
                DB.ReqSelect("prestations",condition,MsgBox=True)
                recordset = DB.ResultatReq()
                if len(recordset) == 0:
                    lstPiePrestations.append(dictPiece["IDprestation"])
                    texte += "Manque Prestation: " + str(dictPiece["IDprestation"]) + " - "  + dictPiece["nomIndividu"] + " - " + dictPiece["nomActivite"]  + "\n"

        # Recherche Factures manquantes
        for dictPiece in lstDictPieces:
            if dictPiece["nature"] in ["AVO","FAC"]:
                condition = "numero = %s " % (dictPiece["noFacture"])
                DB.ReqSelect("factures",condition,MsgBox=True)
                recordset = DB.ResultatReq()
                if len(recordset) == 0:
                    lstPieFactures.append(dictPiece["noFacture"])
                    texte += "Manque Facture: " + str(dictPiece["noFacture"]) + " - "  + dictPiece["nomIndividu"] + " - " + dictPiece["nomActivite"]  + "\n"
                if dictPiece["noAvoir"] != None:
                    condition = "numero = %s" % (dictPiece["noAvoir"])
                    DB.ReqSelect("factures",condition,MsgBox=True)
                    recordset = DB.ResultatReq()
                    if len(recordset) == 0:
                        lstPieFactures.append(dictPiece["noAvoir"])
                        texte += "Manque Avoir: " + str(dictPiece["noAvoir"]) + " - "  + dictPiece["nomIndividu"] + " - " + dictPiece["nomActivite"] + "\n"
        # Ajout des lignes pour pièces veuves
        if texte != u"\n":
            retourFin = False
            # Confirmation de correction par insertions
            dlg = wx.MessageDialog(self.parent, _(u"Les incohérences suivantes sont relevées !" + texte), _(u"Création des manques par leur pièce"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES :
                for dPiece in lstDictPieces:
                    # pour chaque pièce qu'on rappelle on ajoute les manquants
                    self.GetPieceModif(None,dPiece["IDindividu"],dPiece["IDactivite"],dPiece["IDnumPiece"])
                    oldID = dPiece["IDinscription"]
                    # création de l'inscription manquante
                    if dPiece["IDinscription"] in lstPieInscriptions:
                        IDinscription = self.AjoutInscription(self.dictPiece)
                        if IDinscription != None:
                            #modif dans la pièce
                            self.dictPiece["IDinscription"] = IDinscription
                            self.ModifiePieceCree(None,self.dictPiece)
                            # modifie les conso qui étaient avec l'ancien ID
                            DB.ReqMAJ("consommations",[["IDinscription",IDinscription],],"IDinscription",oldID,MsgBox=True)
                    # création des consommations
                    if oldID in lstPieConsommations:
                        self.AjoutConsommations(None,self.dictPiece)
                    # création des prestations...
                    if dPiece["IDprestation"] in lstPiePrestations:
                        IDprestation = self.AjoutPrestation(None,self.dictPiece,modif=False,recree=True)
                    # création des factures...
                    if dPiece["noFacture"] in lstPieFactures:
                        self.AjoutFacture(self.dictPiece,mode="FAC")
                    if dPiece["noAvoir"] in lstPieFactures:
                        self.AjoutFacture(self.dictPiece,mode="AVO")
                retourFin = True
        DB.Close()
        return retourFin
        #fin CoherenceVeuves
# --------------------Lancement de test ----------------------
if __name__ == "__main__":
    app = wx.App(0)
    listeDonnees = [
        ("IDinscription", None),
        ("IDindividu", 6163),
        ("IDfamille", 6163),
        ("IDactivite", 221),
        ("IDgroupe", 442),
        ("IDcategorie_tarif", 795),
        ("IDcompte_payeur", 6163),
        ("date_inscription", str(datetime.date.today())),
        ("parti", False),
        ("nature", "COM"),
        ("nom_activite", "Sejour 41"),
        ("nom_groupe", "Groupe Pasto Plus"),
        ("nom_categorie", "Tarif Normal"),
        ("nom_individu", "nom de  l'individu"),
        ("nom_famille", "nom de la famille"),
        ("lignes_piece", [("art","test article",150.70),]),
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
    f = Forfaits(None)
    #retour = f.AjoutPrestation(dictDonnees)
    #retour = DebutActivite(217)
    #retour = f.DictTrack(listeChamps,listeValeurs)
    retour = GetNoFactureMin()
    print retour
    app.MainLoop()
