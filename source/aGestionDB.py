#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Auteur:           Ivan LUCAS, Jacques Brunel
# Licence:         Licence GNU GPL
# Ajout d'une gestion des Index Uniques et Création des tables 83
# Ouvre aDATA_Tables comme GestionDB ouvre DATA_Tables, acces SQL sans ID autoincrement
#------------------------------------------------------------------------

from UTILS_Traduction import _
import sqlite3
import wx
import os
import random
import aDATA_Tables
import aDLG_ChoixListe
#aDATA_Tables contient toutes les tables matthania
DICT_CONNEXIONS = {}

# Import MySQLdb
try :
    import MySQLdb
    from MySQLdb.constants import FIELD_TYPE
    from MySQLdb.converters import conversions
    IMPORT_MYSQLDB_OK = True
except Exception, err :
    IMPORT_MYSQLDB_OK = False

# import mysql.connector
try :
    import mysql.connector
    from mysql.connector.constants import FieldType
    from mysql.connector import conversion
    IMPORT_MYSQLCONNECTOR_OK = True
except Exception, err :
    IMPORT_MYSQLCONNECTOR_OK = False
# Interface pour Mysql = "mysql.connector" ou "mysqldb"
# Est modifié automatiquement lors du lancement de Noethys selon les préférences (Menu Paramétrage > Préférences)
# Peut être également modifié manuellement ici dans le cadre de tests sur des fichiers indépendamment de l'interface principale 
INTERFACE_MYSQL = "mysqldb"

def SetInterfaceMySQL(nom="mysqldb"):
    """ Permet de sélectionner une interface MySQL """
    global INTERFACE_MYSQL
    if nom == "mysqldb" and IMPORT_MYSQLDB_OK == True :
        INTERFACE_MYSQL = "mysqldb"
    if nom == "mysql.connector" and IMPORT_MYSQLCONNECTOR_OK == True :
        INTERFACE_MYSQL = "mysql.connector"

def ListeToStr(lst=[], separateur=", "):
    # Convertit une liste en texte
    chaine = separateur.join([str(x) for x in lst])
    if chaine == "": chaine = "*"
    return chaine

class DB:
    def __init__(self, suffixe="DATA", nomFichier="", modeCreation=False, IDconnexion=None):
        """ Utiliser GestionDB.DB(suffixe="PHOTOS") pour accéder à un fichier utilisateur """
        """ Utiliser GestionDB.DB(nomFichier="Geographie.dat", suffixe=None) pour ouvrir un autre type de fichier """
        self.nomFichier = nomFichier
        self.modeCreation = modeCreation
        
        # Mémorisation de l'ouverture de la connexion et des requêtes
        if IDconnexion == None :
            self.IDconnexion = random.randint(0, 1000000)
        else :
            self.IDconnexion = IDconnexion
        DICT_CONNEXIONS[self.IDconnexion] = []
        
        # Si aucun nom de fichier n'est spécifié, on recherche celui par défaut dans le Config.dat
        if self.nomFichier == "" :
            self.nomFichier = self.GetNomFichierDefaut()
        
        # On ajoute le préfixe de type de fichier et l'extension du fichier
        if suffixe != None :
            self.nomFichier += u"_%s" % suffixe
        
        # Est-ce une connexion réseau ?
        if "[RESEAU]" in self.nomFichier :
            self.isNetwork = True
        else:
            self.isNetwork = False
            if suffixe != None :
                self.nomFichier = u"Data/%s.dat" % self.nomFichier
        
        # Ouverture de la base de données
        if self.isNetwork == True :
            self.OuvertureFichierReseau(self.nomFichier, suffixe)
        else:
            self.OuvertureFichierLocal(self.nomFichier)

    def GetNomPosteReseau(self):
        if self.isNetwork == False :
            return None
        return self.GetParamConnexionReseau()["user"]
        
    def OuvertureFichierLocal(self, nomFichier):
        """ Version LOCALE avec SQLITE """
        # Vérifie que le fichier sqlite existe bien
        if self.modeCreation == False :
            if os.path.isfile(nomFichier)  == False :
                #print "Le fichier SQLITE demande n'est pas present sur le disque dur."
                self.echec = 1
                return
        # Initialisation de la connexion
        try :
            self.connexion = sqlite3.connect(nomFichier.encode('utf-8'))
            self.cursor = self.connexion.cursor()
        except Exception, err:
            print "La connexion avec la base de donnees SQLITE a echouee : \nErreur detectee :%s" % err
            self.erreur = err
            self.echec = 1
        else:
            self.echec = 0
    
    def GetParamConnexionReseau(self):
        """ Récupération des paramètres de connexion si fichier MySQL """
        pos = self.nomFichier.index("[RESEAU]")
        paramConnexions = self.nomFichier[:pos]
        port, host, user, passwd = paramConnexions.split(";")
        nomFichier = self.nomFichier[pos:].replace("[RESEAU]", "")
        nomFichier = nomFichier.lower() 
        dictDonnees = {"port":int(port), "hote":host, "host":host, "user":user, "utilisateur":user, "mdp":passwd, "password":passwd, "fichier":nomFichier}
        return dictDonnees

    def OuvertureFichierReseau(self, nomFichier, suffixe):
        """ Version RESEAU avec MYSQL """
        try :
            # Récupération des paramètres de connexion
            pos = nomFichier.index("[RESEAU]")
            paramConnexions = nomFichier[:pos]
            port, host, user, passwd = paramConnexions.split(";")
            nomFichier = nomFichier[pos:].replace("[RESEAU]", "")
            nomFichier = nomFichier.lower() 
            
            # Info sur connexion MySQL
            #print "IDconnexion=", self.IDconnexion, "Interface MySQL =", INTERFACE_MYSQL
            
            # Connexion MySQL
            if INTERFACE_MYSQL == "mysqldb" :
                my_conv = conversions
                my_conv[FIELD_TYPE.LONG] = int
                self.connexion = MySQLdb.connect(host=host,user=user, passwd=passwd, port=int(port), use_unicode=True, conv=my_conv) # db=dbParam, 
                self.connexion.set_character_set('utf8')
                
            if INTERFACE_MYSQL == "mysql.connector" :
                self.connexion = mysql.connector.connect(host=host, user=user, passwd=passwd, port=int(port), use_unicode=True, pool_name="mypool2%s" % suffixe, pool_size=3)
    
            self.cursor = self.connexion.cursor()

            # Création
            if self.modeCreation == True :
                self.cursor.execute("CREATE DATABASE IF NOT EXISTS %s CHARSET utf8 COLLATE utf8_unicode_ci;" % nomFichier)
            
            # Utilisation
            if nomFichier not in ("", None, "_data") :
                self.cursor.execute("USE %s;" % nomFichier)
            
        except Exception, err:
            print "La connexion avec la base de donnees MYSQL a echouee. Erreur :"
            print (err,)
            self.erreur = err
            self.echec = 1
            #AfficheConnexionOuvertes() 
        else:
            self.echec = 0
    
    def GetNomFichierDefaut(self):
        nomFichier = ""
        try :
            topWindow = wx.GetApp().GetTopWindow()
            nomWindow = topWindow.GetName()
        except :
            nomWindow = None
        if nomWindow == "general" : 
            # Si la frame 'General' est chargée, on y récupère le dict de config
            nomFichier = topWindow.userConfig["nomFichier"]
        else:
            # Récupération du nom de la DB directement dans le fichier de config sur le disque dur
            import UTILS_Config
            nomFichierConfig = "Data/Config.dat"
            cfg = UTILS_Config.FichierConfig(nomFichierConfig)
            nomFichier = cfg.GetItemConfig("nomFichier")
        return nomFichier

    def ComposeListeChamps(self,listeDonnees, separateur):
        champs = ""
        valeurs = []
        for donnee in listeDonnees:
            if self.isNetwork == True :
                # Version MySQL
                champs = champs + donnee[0] + "=%s" + separateur
            else:
                # Version Sqlite
                champs = champs + donnee[0] + "=?" + separateur
            valeurs.append(donnee[1])
        champs = champs[:-2]
        # pour la  composition de clés, le séparateur peut être ' AND '
        if len(separateur) == 5 : champs = champs[:-3]
        return champs,valeurs

    def ReqInsert(self, nomTable="", listeDonnees=[], commit=True, retourID = False, MsgBox=False):
        """ Permet d'insérer des données dans une table """
        # Préparation des données
        champs = "("
        interr = "("
        valeurs = []
        for donnee in listeDonnees:
            champs = champs + donnee[0] + ", "
            if self.isNetwork == True :
                # Version MySQL
                interr = interr + "%s, "
            else:
                # Version Sqlite
                interr = interr + "?, "
            valeurs.append(donnee[1])
        champs = champs[:-2] + ")"
        interr = interr[:-2] + ")"
        req = "INSERT INTO %s %s VALUES %s" % (nomTable, champs, interr)
        self.retourReq = "ok"
        self.newID= 0
        try:
            # Enregistrement
            self.cursor.execute(req, tuple(valeurs))
            if commit == True :
                self.Commit()
            # Récupération de l'ID
            if retourID:
                if self.isNetwork == True :
                    # Version MySQL
                    self.cursor.execute("SELECT LAST_INSERT_ID();")
                else:
                    # Version Sqlite
                    self.cursor.execute("SELECT last_insert_rowid() FROM %s" % nomTable)
                self.newID = self.cursor.fetchall()[0][0]
        except Exception, err:
            self.retourReq= "Requete sql d'INSERT incorrecte :\n%s\nErreur detectee:\n%s" % (req, err)
            if MsgBox:
                msg = Messages()
                msg.Box(titre="Erreur aGestionDB",message=self.retourReq)
                return
        # Retourne le message
        return self.retourReq

    def ReqMAJ(self, nomTable, listeDonnees, nomChampID, ID, IDestChaine=False, MsgBox=False):
        """ Permet d'insérer des données dans une table """
        # Préparation des données
        champs, valeurs = self.ComposeListeChamps(listeDonnees,", ")
        if IDestChaine == False and type(ID)== int:
            req = "UPDATE %s SET %s WHERE %s=%d" % (nomTable, champs, nomChampID, ID)
        else:
            req = "UPDATE %s SET %s WHERE %s='%s'" % (nomTable, champs, nomChampID, ID)
        self.retourReq = "ok"
        # Enregistrement
        try:
            self.cursor.execute(req, tuple(valeurs))
            self.Commit()
        except Exception, err:
            self.retourReq= (u"Requete sql de mise a jour incorrecte :\n%s\nErreur detectee:\n%s") % (req, err)
            if MsgBox:
                msg = Messages()
                msg.Box(titre="Erreur aGestionDB",message=self.retourReq)
                return
        return self.retourReq

    def ReqMAJcles(self, nomTable, listeDonnees, listeCles):
        """ Permet d'insérer des données dans une table avec clés multiples """
        champs, valeurs = self.ComposeListeChamps(listeDonnees,", ")
        if isinstance(listeCles, (list, tuple)) :
            nomsCles, valeursCles =self.ComposeListeChamps(listeCles," and ")
            req = "UPDATE %s SET %s WHERE %s " % (nomTable, champs, nomsCles)
            for cle in valeursCles :
                valeurs.append(cle)
        else :
            print type(listeCles)
            self.retourReq = u"Liste clé n'est pas une liste"
            return self.retourReq
        self.retourReq = "ok"
        # Enregistrement
        try:
            self.cursor.execute(req, tuple(valeurs))
            self.Commit()
        except Exception, err:
            self.retourReq= (u"Requete sql de mise a jour incorrecte :\n%s\nErreur detectee:\n%s") % (req, err)
        return self.retourReq

    def ReqDEL(self, nomTable="", nomChampID="", ID="", commit=True, MsgBox = False):
        """ Suppression d'un enregistrement """
        self.retourReq = "ok"
        if type(ID) == int :
           req = "DELETE FROM %s WHERE %s=%d" % (nomTable, nomChampID, ID)
        else :
            ID = str(ID)
            if ID[1:] <> "'" :
                ID = "'"+ID+"'"
            req = "DELETE FROM %s WHERE %s=%s" % (nomTable, nomChampID, ID)
        try:
            self.cursor.execute(req)
            if commit == True :
                self.Commit()
        except Exception, err:
            self.retourReq =  _(u"Requete sql de suppression incorrecte :\n%s\nErreur detectee:\n%s") % (req, err)
            if MsgBox:
                msg = Messages()
                msg.Box(titre="Erreur aGestionDB",message=self.retourReq)
                return
        return self.retourReq

    def ReqSelect(self, nomTable, conditions, MsgBox=False):
        """ Permet d'appeler des données d'une seule table selon conditions """
        req = "SELECT *  FROM %s WHERE %s " % (nomTable, conditions)
        self.retourReq = "ok"
        # Enregistrement
        try:
            self.cursor.execute(req)
            self.Commit()
        except Exception, err:
            self.retourReq= (u"Requete sql select incorrecte :\n%s\nErreur detectee:\n%s") % (req, err)
            if MsgBox:
                msg = Messages()
                msg.Box(titre="Erreur aGestionDB",message=self.retourReq)
                return
        return self.retourReq

    def ExecuterReq(self, req, commit=False, MsgBox=False):
        # Pour parer le pb des () avec MySQL
        if self.isNetwork == True :
            req = req.replace("()", "(10000000, 10000001)")
        try:
            self.retourReq = "ok"
            self.cursor.execute(req)
            DICT_CONNEXIONS[self.IDconnexion].append(req)
            if commit: self.Commit()
        except Exception, err:
            self.retourReq =  _(u"Requete SQL incorrecte :\n%s\nErreur detectee:\n%s") % (req, err)
            if MsgBox:
                msg = Messages()
                msg.Box(titre="Erreur aGestionDB",message=self.retourReq)
                return
        # Retourne le message
        return self.retourReq

    def ResultatReq(self):
        if self.echec == 1 : return []
        resultat = self.cursor.fetchall()
        try :
            # Pour contrer MySQL qui fournit des tuples alors que SQLITE fournit des listes
            if self.isNetwork == True and type(resultat) == tuple :
                resultat = list(resultat)
        except :
            pass
        return resultat

    def AfficheErr(self,parent,retour):
        dlgErr = wx.MessageDialog(parent, _(retour), _(u"Retour SQL !"), wx.OK | wx.ICON_EXCLAMATION)
        dlgErr.ShowModal()
        dlgErr.Destroy()
        return

    def Commit(self):
        if self.connexion:
            self.connexion.commit()

    def Close(self):
        try :
            self.connexion.close()
            del DICT_CONNEXIONS[self.IDconnexion]
            #print "Fermeture connexion ID =", self.IDconnexion
        except :
            pass

    def IsTableExists(self, nomTable=""):
        """ Vérifie si une table donnée existe dans la base """
        tableExists = False
        for (nomTableTmp,) in self.GetListeTables() :
            if nomTableTmp == nomTable :
                tableExists = True
        return tableExists

    def IsIndexExists(self, nomTable=""):
        """ Vérifie si un index existe dans la base """
        indexExists = False
        for (nomTableTmp,) in self.GetListeIndex() :
            if nomTableTmp == nomTable :
                indexExists = True
        return indexExists
                        
    def GetListeTables(self):
        if self.isNetwork == False :
            # Version Sqlite
            req = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            self.ExecuterReq(req)
            listeTables = self.ResultatReq()
        else:
            # Version MySQL
            req = "SHOW TABLES;"
            self.ExecuterReq(req)
            listeTables = self.ResultatReq()
        return listeTables

    def GetListeChamps(self):
        """ Affiche la liste des champs de la précédente requête effectuée """
        liste = []
        for fieldDesc in self.cursor.description:
            liste.append(fieldDesc[0])
        return liste

    def GetListeChamps2(self, nomTable=""):
        """ Affiche la liste des champs de la table donnée """
        listeChamps = []
        if self.isNetwork == False :
            # Version Sqlite
            req = "PRAGMA table_info('%s');" % nomTable
            self.ExecuterReq(req)
            listeTmpChamps = self.ResultatReq()
            for valeurs in listeTmpChamps :
                listeChamps.append( (valeurs[1], valeurs[2]) )
        else:
            # Version MySQL
            req = "SHOW COLUMNS FROM %s;" % nomTable
            self.ExecuterReq(req)
            listeTmpChamps = self.ResultatReq()
            for valeurs in listeTmpChamps :
                listeChamps.append( (valeurs[0], valeurs[1]) )
        return listeChamps
                        
    def GetListeIndex(self):
        if self.isNetwork == False :
            # Version Sqlite
            req = "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;"
            self.ExecuterReq(req)
            listeIndex = self.ResultatReq()
        else:
            # Version MySQL
            req = "SHOW INDEX;"
            self.ExecuterReq(req)
            listeIndex = self.ResultatReq()
        return listeIndex

    def CreationTables(self, dicoDB={}, fenetreParente=None):
        for table in dicoDB:
            if not self.IsTableExists(table) :
                # Affichage dans la StatusBar
                if fenetreParente != None :
                    fenetreParente.SetStatusText(_(u"Création de la table de données %s...") % table)
                req = "CREATE TABLE %s (" % table
                for descr in dicoDB[table]:
                    nomChamp = descr[0]
                    typeChamp = descr[1]
                    # Adaptation à Sqlite
                    if self.isNetwork == False and typeChamp == "LONGBLOB" : typeChamp = "BLOB"
                    # Adaptation à MySQL :
                    if self.isNetwork == True and typeChamp == "INTEGER PRIMARY KEY AUTOINCREMENT" : typeChamp = "INTEGER PRIMARY KEY AUTO_INCREMENT"
                    if self.isNetwork == True and typeChamp == "FLOAT" : typeChamp = "REAL"
                    if self.isNetwork == True and typeChamp == "DATE" : typeChamp = "VARCHAR(10)"
                    if self.isNetwork == True and typeChamp.startswith("VARCHAR") :
                        nbreCaract = int(typeChamp[typeChamp.find("(")+1:typeChamp.find(")")])
                        if nbreCaract > 255 :
                            typeChamp = "TEXT(%d)" % nbreCaract
                        if nbreCaract > 20000 :
                            typeChamp = "MEDIUMTEXT"
                    # ------------------------------
                    req = req + "%s %s, " % (nomChamp, typeChamp)
                req = req[:-2] + ")"
                retour = self.ExecuterReq(req)
                if retour == "ok":
                        self.Commit()
                print table, "-----------/-------------",retour

    def CreationIndex(self,nomIndex="",listeIndex={}):
        """ Création d'un index """
        nomTable = listeIndex[nomIndex]["table"]
        nomChamp = listeIndex[nomIndex]["champ"]

        if self.IsTableExists(nomTable) :
            #print "Creation de l'index : %s" % nomIndex
            if nomIndex[:2] == "PK":
                req = "CREATE UNIQUE INDEX %s ON %s (%s);" % (nomIndex, nomTable, nomChamp)
            else :
                req = "CREATE INDEX %s ON %s (%s);" % (nomIndex, nomTable, nomChamp)
            retour = self.ExecuterReq(req)
            print nomIndex, "-----------/-------------",retour
            if retour == "ok":
                    self.Commit()

    def CreationTousIndex(self,dictIndex):
        """ Création de tous les index """
        for nomIndex, temp in dictIndex.iteritems() :
            if not self.IsIndexExists(nomIndex) :
                self.CreationIndex(nomIndex,dictIndex)

    def GetParam(self, param = None, type= "string",user= None):
        if user == None:
            user = self.UtilisateurActuel()
        if user == None : user = "NoName"
        self.type = "prm" + type[0].upper() + type[1:]
        if user == None : user = "NoName"
        req = "SELECT " + self.type + " FROM matParams WHERE prmUser = '" + user + "' and prmParam = '" + param +"';"
        retour = self.ExecuterReq(req)
        if retour <> "ok" :
            self.AfficheErr(self,retour)
        recordset = self.ResultatReq()
        value = None
        if len(recordset)>0 :
            if len(recordset[0])>0 :
                value = recordset[0][0]
        return value

    def SetParam(self, param = None, value= None, type= "string", user= None):
        if user == None:
            user = self.UtilisateurActuel()
        if user == None : user = "NoName"
        self.type = "prm" + type[0].upper() + type[1:]
        table = "matParams"
        listeDonnees = []
        listeDonnees.append(("prmUser",user))
        listeDonnees.append(("prmParam", param))
        listeDonnees.append((self.type, value))
        retour = self.ReqInsert(table, listeDonnees,False)
        if retour == "ok" :
            self.Commit()
        else :
            listeCles = []
            listeCles.append(("prmUser", user))
            listeCles.append(("prmParam", param))
            listeDonnees = []
            listeDonnees.append((self.type, value))
            retour = self.ReqMAJcles(table, listeDonnees, listeCles)
            if retour == "ok" :
                self.Commit()
        return retour

    def SetAnnee(self, annee = "2016"):
        retour= self.SetParam(param = "periodeAnnee",value=annee, type="string")
        return retour

    def GetAnnee(self):
        annee = str(self.GetParam("periodeAnnee","string"))
        debut= str(annee + "-01-01")
        fin = str(annee + "-12-31")
        return annee, debut, fin

    def UtilisateurActuel(self):
        utilisateur = "NoName"
        try :
            topWindow = wx.GetApp().GetTopWindow()
            nomWindow = topWindow.GetName()
        except :
            nomWindow = None
        if nomWindow == "general" :
            # Si la frame 'General' est chargée, on y récupère le dict de config
            dictUtilisateur = topWindow.dictUtilisateur
            utilisateur = dictUtilisateur["prenom"] + " " + dictUtilisateur["nom"]
        return utilisateur

    def GetNomIndividu(self,ID, first="prenom" ):
        if ID == None :
            value = " "
        else:
            if first == "prenom":
                select = "SELECT prenom, nom "
            else: select = "SELECT nom, prenom "
            form = "FROM individus "
            if type(ID) != str:
                where = """WHERE (individus.IDindividu = %s );""" % str(ID)
            else:
                where = """WHERE (individus.IDindividu = %s );""" % ID
            req = select + form + where

            retour = self.ExecuterReq(req)
            if retour <> "ok" :
                wx.MessageBox(str(retour))
            recordset = self.ResultatReq()
            value = " "
            if len(recordset)>0 :
                if len(recordset[0])>0 :
                    value = recordset[0][0] + " " + recordset[0][1]
        return value

    def GetNomActivite(self,ID):
        if ID == None :
            value = " "
        else:
            req = """SELECT nom
                    FROM activites
                    WHERE (IDactivite = %s );""" % ID
            retour = self.ExecuterReq(req)
            if retour <> "ok" :
                wx.MessageBox(str(retour))
            recordset = self.ResultatReq()
            value = " "
            if len(recordset)>0 :
                if len(recordset[0])>0 :
                    value = recordset[0][0]
        return value

    def GetNomGroupe(self,ID):
        if ID == None :
            value = " "
        else:
            req = """SELECT nom
                    FROM groupes
                    WHERE (IDgroupe = %s );""" % ID
            retour = self.ExecuterReq(req)
            if retour <> "ok" :
                wx.MessageBox(str(retour))
            recordset = self.ResultatReq()
            value = " "
            if len(recordset)>0 :
                if len(recordset[0])>0 :
                    value = recordset[0][0]
        return value

    def GetNomCategorieTarif(self,ID):
        if ID == None : Nom = "no name"
        req = """SELECT nom
                FROM categories_tarifs
                WHERE (IDcategorie_tarif = %s );""" % ID
        retour = self.ExecuterReq(req)
        if retour <> "ok" :
            wx.MessageBox(str(retour))
        recordset = self.ResultatReq()
        value = None
        if len(recordset)>0 :
            if len(recordset[0])>0 :
                value = recordset[0][0]
        return value

# ------------- Fonctions de MAJ de la base de données ---------------------------------------------------------------

class Ajout_TablesMat(wx.Frame):
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, size=(550, 400))
        DB1 = DB(suffixe="DATA", modeCreation=False)
        DB1.CreationTables(aDATA_Tables.DB_DATA)
        if DB1.retourReq <> "ok" :
            dlg = wx.MessageDialog(self, _(u"Erreur base de données.\n\nErreur : %s") % DB1.retourReq, _(u"Erreur de création de fichier"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        DB1.Close()

class Ajout_IndexMat(wx.Frame):
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, size=(550, 400))
        DB1 = DB(suffixe="DATA", modeCreation=False)
        DB1.CreationTousIndex(aDATA_Tables.DB_PK)
        if DB1.retourReq <> "ok" :
            dlg = wx.MessageDialog(self, _(u"Erreur base de données.\n\nErreur : %s") % DB1.retourReq, _(u"Erreur de création d'index PK"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        DB1.CreationTousIndex(aDATA_Tables.DB_INDEX)
        if DB1.retourReq <> "ok" :
            dlg = wx.MessageDialog(self, _(u"Erreur base de données.\n\nErreur : %s") % DB1.retourReq, _(u"Erreur de création d'index IX"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        DB1.Close()

# ------------- Affichages --------------- ---------------------------------------------------------------
def MessageBox(self,mess,titre = u"Erreur Bloquante !"):
    dlg = wx.MessageDialog(self, _(mess),_(titre) , wx.OK | wx.ICON_EXCLAMATION)
    ret = dlg.ShowModal()
    dlg.Destroy()
    return ret

class Messages(wx.Frame):
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, size=(550, 400))

    def Box(self, titre= u"Erreur Bloquante", message= u"Avertissement" ):
        dlg = wx.MessageDialog(self, message, titre, wx.OK | wx.ICON_EXCLAMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def Choix(self,listeTuples=[(1,"a"),(2,"b")], titre = u"Choisissez", intro = u"Dans la liste"):
        dlg = aDLG_ChoixListe.Dialog(self,LargeurCode= 100,LargeurLib= 200,minSize = (500,300), listeOriginale=listeTuples, titre = titre, intro = intro)
        interroChoix = dlg.ShowModal()
        if interroChoix == wx.ID_OK :
            sel=dlg.choix
            return sel
        else:
            return None,None

def AppelDB(fonction,ID):
    result = "KO"
    if fonction != None and ID != None:
        db = DB()
        if type(ID)== int:
            f="db."+fonction + '(%d)'% ID
            result = eval(f)
        elif type(ID)== str:
            f="db."+fonction + '(%s)'% ID
            result = eval(f)
        else:
            print "Type de l'ID non géré : ",type(ID)
        db.Close()
    return result

if __name__ == "__main__":
    app = wx.App()
    #f = Ajout_TablesMat()
    #f = Ajout_IndexMat()
    DB1 = DB()
    #retour= DB.SetParam(param = "ParamTest2",value="2016/06/01", type="date")
    #retour= DB.GetParam("ParamTest","date")
    #retour = DB.SetAnnee("2015")
    retour = ListeToStr()
    #DB = Messages(None)
    DB1.Close()
    MessageBox(None,retour,titre="Résultat Test")
