#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Matthania
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# Fonctions calculs prix articles et application des conditions
# Contient aussi les listes descriptives des calculs et conditions
#-----------------------------------------------------------
import aGestionDB
import wx
import datetime

# Listes de parametres :
LISTEnaturesPieces = [
        ("DEV", "Devis", u"Le devis n'enregistre pas de consommation, seulement l'inscription", ),
        ("RES", "Reservation", u"La r�servation enregistre l'inscription, la consommation pas la prestation", ),
        ("COM", "Commande", u"La commande enregistre la prestation qui est due selon l'engagement re�u", ),
        ]
LISTEnaturesPiecesFac = [
        ("FAC", "Facture", u"La Facture se transf�re en compta, n'est plus modifiable, s'annule par un avoir", ),
        ("AVO", "Facture&Avoir", u"Facture annul�e par un Avoir se g�n�re par suppression d'une inscription factur�e ou par saisie libre", )
        ]

LISTEetatsPieces = [
        ("0", u"Non Fait", u"Probl�me : Pas d'�tat pour cette nature de pi�ce", ),
        ("1", u"Juste Cr��", u"Inscription nouvellement dans cette nature", ),
        ("2", u"Imprim�", u"Impression faite dans cette nature", ),
        ("3", u"Transf�r�", u"La Facture est transf�r�e en compta, s'annule par un avoir", ),
        ("4", u"cf Avoir", u"Cette Facture a fait l'objet d'un avoir", ),
        ]

LISTEconditions = [
        ("Sans", u"Pas de condition particuli�re", u"sans", None, ),
        ("AG11-13", u"Pr�ados 11-13 ans", u"Age >=11 et <=13", "CondAg1113", ),
        ("AG14-24", u"Jeunes 14-24 ans", u"Age >=14 et < 25 ", "CondAg1424", ),
        ("AG14-99", u"Plus de 14 ans", u"Age >=99",  "CondAg1499",),
        ("AG6-10", u"Enfant", u"Age >=6 et <11", "CondAg610", ),
        ("Annuelle", u"Une seule fois par ann�e civile et par individu", u"Test la pr�sence du m�me article dans l'ann�e pour l'individu",  "CondAnnuelle",),
        ("AnnuelleFam", u"Une seule fois par ann�e civile et par famille", u"Test la pr�sence du m�me article dans l'ann�e pour un individu de la famille",  "CondAnnuFam",),
        ("AvEnf", u"Avec un Enfant au moins", u"Teste la pr�sence d'un Enfant inscrit au moins", "CondAvEnf", ),
        ("NbEnf", u"Deux Enfants au moins", u"Teste la pr�sence de deux Enfants inscrit au moins", "CondNbEnf", ),
        ("ComboNeige", u"Un camp neige dans la famille", u"Test une inscription de la famille � Un camp neige", "CondComboNeige", ),
        ("Serviteur", u"Serviteur de Dieu", u"Teste l'appartenance au groupe Serviteurs", "CondServiteur", ),
        ]

LISTEmodeCalcul = [
        ("Sans", u"Pas de prix, article de type message", None,),
        ("Simple", u"Prix1, sans calul", None,),
        ("1S-2S", u"Prix 1 premi�re semaine Prix 2 les suivantes", "Cal1s2s", ),
        ("4J-8J", u"Prix 1 semaine 4 jours Prix 2 autres cas", "Cal4j8j", ),
        ("JOURS", u"Prix 1 par nombre de journ�es saisies",  "CalJours",),
        ("m-M", u"Prix 1 pour mineur prix 2 pour majeur", "CalmM", ),
        ("Reduction", u"Prix1 est le taux de r�duction en pourcent", "CalReduction",),
        ("RedNbEnf", u"Taux de r�duction, dans le code", "CalRedNbEnf",),
        ]

LISTEtypeLigne = [
        ("COTISATION", u"Ligne de COTISATION", ),
        ("SEJOUR", u"Ligne de type libelle s�jour et un prix global contenant toutes les options incluses dans le s�jour", ),
        ("OPTION_SEJ", u"Compl�ments de prix inclus dans le s�jour, faisant l'objet d'un simple descriptif sous forme message ", ),
        ("OPTION_DETAIL", u"Compl�ment de prix correspondant aux options d�taill�es, faisant l'objet de lignes distinctes sur la facture", ),
        ("VOYAGE", u"Facturation du voyage : le libell� comportera la ville de d�part Aller et celle du Retour ", ),
        ("MESSAGE", u"Message sans montant, seul le texte est pris en compte ", ),
        ]

LISTEformatLigne = [
        ("NORMAL", u"Ecriture style normal, taille moyenne", ),
        ("ITALIQUE", u"Ecriture en italique et �ventuellement de taille inf�rieure", ),
        ("GRAS", u"Ecriture avec un style appuy�", ),
        ("TRAIT", u"Le texte est prolong� d'un trait servant de guide ou de s�parateur", ),
        ]

# Fonctions param�trables
def FinActivite(IDactivite):
    #utilis�e dans Saison()
    DB = aGestionDB.DB()
    req = "SELECT date_fin FROM activites WHERE IDactivite = %d ;" % IDactivite
    retour = DB.ExecuterReq(req)
    if retour != "ok" :
        aGestionDB.MessageBox(retour)
        return None
    retour = DB.ResultatReq()
    if len(retour) == 0: date = None
    else: date = retour[0][0]
    return date

def Saison(IDactivite = None, annee= None):
    # Retourne les dates d�but et fin de la saison de l'activit�, ou de l'ann�e donn�e, ou de l'ann�e en cours
    if IDactivite == None:
        if annee == None:
            if datetime.date.today().month < 9 : annee= datetime.date.today().year
            else: annee= datetime.date.today().year + 1
        saisonDeb = datetime.date(annee-1,9,1)
        saisonFin = datetime.date(annee,8,31)
    else:
        dateEng = FinActivite(IDactivite)
        dateFinActivite = datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))
        if dateFinActivite.month < 9 : saison = dateFinActivite.year
        else: saison = dateFinActivite.year + 1
        saisonDeb = datetime.date(saison-1,9,1)
        saisonFin = datetime.date(saison,8,31)
    return saisonDeb, saisonFin

def DateEngEnDateDD(dateEng):
    return datetime.date(int(dateEng[:4]), int(dateEng[5:7]), int(dateEng[8:10]))

def DebutActivite(DB,IDactivite, IDgroupe):
    req = "SELECT MIN(date) FROM ouvertures WHERE IDactivite = %d  AND IDgroupe = %d;" % (IDactivite,IDgroupe)
    DB.ExecuterReq(req,MsgBox=True)
    recordset = DB.ResultatReq()
    if len(recordset) == 0: date = None
    else: date = recordset[0][0]
    return date

def Naissance(DB,IDindividu):
    req = """SELECT date_naiss FROM individus WHERE IDindividu= %s ;""" % (IDindividu)
    DB.ExecuterReq(req,MsgBox=True)
    recordset = DB.ResultatReq()
    if len(recordset) != 1: naissance = None
    else: naissance = recordset[0][0]
    return naissance

def Age(dictDonnees):
    DB = aGestionDB.DB()
    IDactivite = dictDonnees["IDactivite"]
    IDgroupe = dictDonnees["IDgroupe"]
    IDindividu = dictDonnees["IDindividu"]
    age = 0
    if IDactivite != None and IDgroupe != None and IDindividu != None:
        dateDeb = DebutActivite(DB,IDactivite,IDgroupe)
        naissance = Naissance(DB,IDindividu)
        if dateDeb != None and naissance != None:
            age = DateEngEnDateDD(dateDeb).year - DateEngEnDateDD(naissance).year
    DB.Close()
    return age

#Programmation de chacune des conditions sur articles
# Pr�ados 11-13 ans
def CondAg1113(dictDonnees) :
    age = Age(dictDonnees)
    if age >= 11 and age <= 13:
        return True
    else: return False

def CondAg1424(dictDonnees) :
    age = Age(dictDonnees)
    if age >= 14 and age <= 24:
        return True
    else: return False

# Plus de 14 ans
def CondAg1499(dictDonnees) :
    age = Age(dictDonnees)
    if age >= 14:
        return True
    else: return False

# Enfant
def CondAg610(dictDonnees) :
    age = Age(dictDonnees)
    if age >= 6 and age <= 10:
        return True
    else: return False

# Une seule fois par ann�e civile
def CondAnnuelle(dictDonnees) :
    return True
def CondAnnuFam(dictDonnees) :
    return True
# Avec un Enfant au moins
def CondAvEnf(dictDonnees) :
    return True
# Avec un Enfant au moins
def CondNbEnf(dictDonnees) :
    return True
# Un camp neige dans la famille
def CondComboNeige(dictDonnees) :
    return True
def CondServiteur(dictDonnees) :
    return True

class ActionsConditions() :
        def __init__(self, dictDonnees={}):
            self.dictDonnees= dictDonnees
        # Lancement de la fonction d�finie au dessus, retour du r�sultat
        def Condition(self,condition, codeArticle):
            result = True
            fonction= "KO"
            if condition != None:
                for item in LISTEconditions:
                    if item[0] == condition: fonction= item[3]
            else:
                fonction = None
            if fonction == "KO":
                aGestionDB.MessageBox(None, u"La fonction '%s' condition de l'article '%s' n'est pas pr�sente dans aGestionArticle.LISTEconditions!" % (condition, codeArticle) ,titre = u"Erreur Article atypique !")
            else:
                if fonction != None:
                    if fonction not in globals():
                        aGestionDB.MessageBox(None, u"La fonction '%s' est dans LISTEconditions mais non programm�e dans aGestionArticle.ActionsConditions!" % fonction ,titre = u"Erreur Programmation !")
                    else:
                        result = eval(fonction + '(self.dictDonnees)')
            return result

#Programmation de chacun des modes de calcul des articles, retourne les �l�ments de prix calcul�s
def Cal1s2s(track, tracks, dictDonnees) :
    qte,mtt = None,None
    return qte,mtt
def Cal4j8j(track, tracks, dictDonnees) :
    qte,mtt = None,None
    return qte,mtt
def CalJours(track, tracks, dictDonnees) :
    qte,mtt = None,None
    return qte,mtt
def CalmM(track, tracks, dictDonnees) :
    qte,mtt = None,None
    return qte,mtt
def CalReduction(track, tracks, dictDonnees) :
    qte = 0.00
    pu = (-float(track.prixUnit))/100
    for obj in tracks:
        if obj.typeLigne in ("SEJOUR","OPTION_DETAIL","OPTION_SEJ"):
            if obj.montant != None:
                qte += obj.montant
    mtt = pu * qte
    return qte,mtt
def CalRedNbEnf(track, tracks, dictDonnees) :
    qte,mtt = None,None
    return qte,mtt

class ActionsModeCalcul() :
        def __init__(self, dictDonnees={}):
            self.dictDonnees= dictDonnees
        # Lancement de la fonction d�finie ci-dessus, retour du r�sultat
        def ModeCalcul(self,track,tracks):
            qte,mtt= None,None
            modeCalcul = track.modeCalcul
            fonction = "KO"
            if modeCalcul != None:
                for item in LISTEmodeCalcul:
                    if item[0] == modeCalcul: fonction= item[2]
            else:
                fonction = None
            if fonction == "KO":
                aGestionDB.MessageBox(None, u"La fonction '%s' mode de calcul de l'article '%s' n'est pas pr�sente dans aGestionArticle.LISTEmodeCalcul!" % (modeCalcul, track.codeArticle) ,titre = u"Erreur Article atypique !")
            else:
                if fonction != None:
                    if fonction not in globals():
                        aGestionDB.MessageBox(None, u"La fonction '%s' est dans la liste des modes de calcul mais pas programm�e dans aGestionArticle.ActionsModeCalcul!" % fonction ,titre = u"Erreur Programmation !")
                    else:
                        qte,mtt= eval(fonction + '(track,tracks,self.dictDonnees)')
            return qte,mtt

#--------------------------------------------
class Track(object):
    # Cette classe ne sert que pour les tests et rappelle les attributs des tracks re�us
    def __init__(self):
        self.qte = 1
        self.prixUnit = 20
        self.prix2 = 18
        self.montant = 80
        self.typeLigne = "SEJOUR"
        self.conditions = None
        self.modeCalcul = "Reduction"
        self.force = "OUI"

def main():
    listeDonnees = [
        ("origine", "modif"),
        ("IDindividu", 6163),
        ("IDfamille", 6163),
        ("IDactivite", 221),
        ("IDgroupe", 442),
        ]
    dictDonnees = {}
    for donnee in listeDonnees:
        champ = donnee[0]
        valeur = donnee[1]
        dictDonnees[champ] = valeur
    action = ActionsModeCalcul(dictDonnees)

    track= Track()
    tracks = []
    tracks.append(track)
    print action.ModeCalcul(track, tracks).montant

if __name__ == "__main__":
    app = wx.App()
    main()

