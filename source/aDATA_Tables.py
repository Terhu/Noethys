#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#-----------------------------------------------------------
# Application :    Matthania
# Auteur:          Jacques BRUNEL
# Licence:         Licence GNU GPL
# Cr�ation des tables compl�mentaires
#-----------------------------------------------------------

import wx
import aGestionDB

TABLES_IMPORTATION_OBLIGATOIRES = []

DB_DATA = {
        "matTarifs"   :    [
            ("trfIDactivite",   "integer",   u"noethys.activites.IDactivite"),
            ("trfIDgroupe",   "integer",   u"noethys.groupe.IDgroupe"),
            ("trfIDcategorieTarif",   "integer",   u"noethys.categorie_tarifs.IDcategorie_tarif"),
            ("trfCodeTarif",   "varchar(16)",   u"matTarifsNoms.trnCodeTarif"),
            ],   # fin de     matTarifs
        "matTarifsNoms"   :    [
            ("trnCodeTarif",   "varchar(16)",   u"matTarifs.trfCodeTarif"),
            ("trnLibelle",   "varchar(128)",   u"Nom du tarif"),
            ],   # fin de     matTarifsNoms
        "matTarifsLignes"   :    [
            ("trlCodeTarif",   "varchar(16)",   u"Code tarif"),
            ("trlNoLigne",   "integer",   u"Ordre"),
            ("trlCodeArticle",   "varchar(16)",   u"R�f�rence article"),
            ("trlPreCoche",   "integer",   u"Pr�coch� dans la proposition"),
            ],   # fin de     matTarifsLignes
        "matArticles"   :    [
            ("artCodeArticle",   "varchar(16)",   u"ID_Article"),
            ("artLibelle",   "varchar(128)",   u"Nom de l'article"),
            ("artConditions",   "varchar(16)",   u"Condition de blocage ou d'alerte"),
            ("artModeCalcul",   "varchar(16)",   u"Calcul pour g�n�rer des lignes, peut modifier le libell�, et propose une quantit� et un prix en fonction du context"),
            ("artPrix1",   "float",   u"Prix de base actualis� chaque ann�e"),
            ("artPrix2",   "float",   u"Pour les cas ou un deuxi�me prix est n�cessaire au calcul"),
            ("artCodeBlocFacture",   "varchar(16)",   u"matBlocsFactures.LFA_CodeBlocFacture      Pour Regroupement sur les lignes de facturation"),
            ("artCodeComptable",   "varchar(16)",   u"matPlanComptable.PCT_CodeComptable   Pour Regroupement dans la compta par l'interm�diaire d'une table naturecomptabl"),
            ("artNiveauFamille",   "integer",   u"Propos� au niveau famille"),
            ("artNiveauActivite",   "integer",   u"Propos� au niveau de l'inscription"),
            ],   # fin de     matArticles
        "matBlocsFactures"   :    [
            ("lfaCodeBlocFacture",   "varchar(16)",   u"Code du bloc regroupement sur ligne facture"),
            ("lfaTypeLigne",   "varchar(16)",   u"Comportement de la ligne"),
            ("lfaOrdre",   "integer",   u"Agencement des lignes sur la facture"),
            ("lfaLibelle",   "varchar(128)",   u"Libelle de la ligne sur la facture"),
            ("lfaFormat",   "varchar(16)",   u"Style de police"),
            ],   # fin de     matBlocsFactures
        "matPlanComptable"   :    [
            ("pctCodeComptable",   "varchar(16)",   u"Numero compte gescom"),
            ("pctLibelle",   "varchar(128)",   u"D�signation de la nature comptable"),
            ("pctCompte",   "varchar(16)",   u"Num�ro de compte dans la compa"),
            ],   # fin de     matPlanComptable
        "matPieces"   :    [
            ("pieIDnumPiece",   "integer primary key autoincrement",   u"Num�ro de pi�ce unique"),
            ("pieIDinscription",   "integer",   u"Ref inscription ou ann�e pour un niveau famille"),
            ("pieIDprestation",   "integer",   u"Ref prestation r�cap"),
            ("pieIDindividu",   "integer",   u"Participant ou 999 pour un niveau famille"),
            ("pieIDfamille",   "integer",   u"Famille qui demande l'inscription"),
            ("pieIDcompte_payeur",   "integer",   u"Famille qui paye"),
            ("pieIDactivite",   "integer",   u"activit� ou 1 pour la cotisation ou x pour autres pi�ces niveau famille"),
            ("pieIDgroupe",   "integer",   u"groupe"),
            ("pieIDcategorie_tarif",   "integer",   u"cat�gorie de tarification"),
            ("pieDateCreation",   "date",   u"Date de Premi�re action"),
            ("pieUtilisateurCreateur",   "varchar(16)",   u"Premier utilisateur"),
            ("pieDateModif",   "date",   u"Date de derni�re action"),
            ("pieUtilisateurModif",   "varchar(16)",   u"Dernier utilisateur"),
            ("pieNature",   "varchar(8)",   u"DEVis REServ� COMmande FACture AVOir"),
            ("pieEtat",   "varchar(8)",   u"1=cree, 2=imprim�, 3=transf�r� 9=supprim� pour 5 positions nature"),
            ("pieDateFacturation",   "date",   u"Date de la facture"),
            ("pieNoFacture",   "integer",   u"Num�ro de la facture"),
            ("pieDateEcheance",   "date",   u"date �ch�ance"),
            ("pieDateAvoir",   "date",   u"Date de l'annulation"),
            ("pieNoAvoir",   "integer",   u"Num�ro d'avoir"),
            ("pieIDtranspAller",   "integer",   u"Ref transport aller"),
            ("piePrixTranspAller",   "float",   u"Prix du transport aller"),
            ("pieIDtranspRetour",   "integer",   u"Ref transport retour"),
            ("piePrixTranspRetour",   "float",   u"Prix du transport retour"),
            ("pieIDparrain",   "integer",   u"Parrain prescripteur de l'inscription"),
            ("pieParrainAbandon",   "integer",   u"Le Parrain abondonne son cr�dit au profit du filleul"),
            ("pieCommentaire",   "blob",   u"Commentaire libre sur vie de la pi�ce"),
            ],   # fin de     matPieces
        "matPiecesLignes"   :    [
            ("ligIDnumLigne",   "integer primary key autoincrement",   u"Num�ro de ligne pi�ce unique"),
            ("ligIDnumPiece",   "integer",   u"r�f�rence de la pi�e"),
            ("ligDate",   "date",   u"date de l'entr�e de la ligne"),
            ("ligUtilisateur",   "varchar(16)",   u"dernier utilisateur"),
            ("ligCodeArticle",   "varchar(16)",   u"article"),
            ("ligLibelle",   "varchar(128)",   u"libell� article modifi�"),
            ("ligQuantite",   "float",   u"quantit�"),
            ("ligPrixUnit",   "float",   u"prix unitaire calcul� origine"),
            ("ligMontant",   "float",   u"Montant retenu"),
            ],   # fin de     matPiecesLignes
        "matParams"   :    [
            ("prmUser",   "varchar(16)",   u"Code de l'utilisateu"),
            ("prmParam",   "varchar(16)",   u"Code du param�tre pour l'appel"),
            ("prmInteger",   "integer",   u"Param�tre entier"),
            ("prmDate",   "date",   u"Param�tre date"),
            ("prmString",   "varchar(128)",   u"Param�tre cha�ne"),
            ("prmFloat",   "float",   u"Param�tre Num�rique r�el"),
            ],   # fin de     matParams
        }

DB_PK = {
        "PK_matArticles_artCodeArticle"  :  {"table"  :  "matArticles",  "champ" : "artCodeArticle", },
        "PK_matBlocsFactures_lfaCodeBlocFacture"  :  {"table"  :  "matBlocsFactures",  "champ" : "lfaCodeBlocFacture", },
        "PK_matPlanComptable_pctCodeComptable"  :  {"table"  :  "matPlanComptable",  "champ" : "pctCodeComptable", },
        "PK_matTarifs_trfActGroupCat"  :  {"table"  :  "matTarifs",  "champ" : "'trfIDactivite','trfIDgroupe','trfIDcategorieTarif'", },
        "PK_matTarifsLignes_trlTarLigArt"  :  {"table"  :  "matTarifsLignes",  "champ" : "'trlCodeTarif','trlNoLigne','trlCodeArticle'", },
        "PK_matTarifsNoms_trnCodeTarif"  :  {"table"  :  "matTarifsNoms",  "champ" : "trnCodeTarif", },
        "PK_matParams_param"  :  {"table"  :  "matParams",  "champ" : "'prmUser','prmParam'", },
        }
DB_INDEX = {
        "IX_matArticles_artCodeComptable"  :  {"table"  :  "matArticles",  "champ" : "artCodeComptable", },
        "IX_matArticles_artCodeBlocFacture"  :  {"table"  :  "matArticles",  "champ" : "artCodeBlocFacture", },
        "IX_matArticles_artConditions"  :  {"table"  :  "matArticles",  "champ" : "artConditions", },
        "IX_matArticles_artModeCalcul"  :  {"table"  :  "matArticles",  "champ" : "artModeCalcul", },
        "IX_matBlocsFactures_lfaTypeLigne"  :  {"table"  :  "matBlocsFactures",  "champ" : "lfaTypeLigne", },
        "IX_matBlocsFactures_lfaOrdre"  :  {"table"  :  "matBlocsFactures",  "champ" : "lfaOrdre", },
        "IX_matPieces_pieDateAvoir"  :  {"table"  :  "matPieces",  "champ" : "pieDateAvoir", },
        "IX_matPieces_pieDateEcheance"  :  {"table"  :  "matPieces",  "champ" : "pieDateEcheance", },
        "IX_matPieces_pieDateFacturation"  :  {"table"  :  "matPieces",  "champ" : "pieDateFacturation", },
        "IX_matPieces_pieDateModif"  :  {"table"  :  "matPieces",  "champ" : "pieDateModif", },
        "IX_matPieces_pieIDactivite"  :  {"table"  :  "matPieces",  "champ" : "pieIDactivite", },
        "IX_matPieces_pieIDcategorie_tarif"  :  {"table"  :  "matPieces",  "champ" : "pieIDcategorie_tarif", },
        "IX_matPieces_pieIDcompte_payeur"  :  {"table"  :  "matPieces",  "champ" : "pieIDcompte_payeur", },
        "IX_matPieces_pieIDfamille"  :  {"table"  :  "matPieces",  "champ" : "pieIDfamille", },
        "IX_matPieces_pieIDgroupe"  :  {"table"  :  "matPieces",  "champ" : "pieIDgroupe", },
        "IX_matPieces_pieIDindividu"  :  {"table"  :  "matPieces",  "champ" : "pieIDindividu", },
        "IX_matPieces_pieIDinscription"  :  {"table"  :  "matPieces",  "champ" : "pieIDinscription", },
        "IX_matPieces_pieNoAvoir"  :  {"table"  :  "matPieces",  "champ" : "pieNoAvoir", },
        "IX_matPieces_pieNoFacture"  :  {"table"  :  "matPieces",  "champ" : "pieNoFacture", },
        "IX_matPiecesLignes_ligCodeArticle"  :  {"table"  :  "matPiecesLignes",  "champ" : "ligCodeArticle", },
        "IX_matPiecesLignes_ligIDnumPiece"  :  {"table"  :  "matPiecesLignes",  "champ" : "ligIDnumPiece", },
        "IX_matTarifs_trfCodeTarif"  :  {"table"  :  "matTarifs",  "champ" : "trfCodeTarif", },
        "IX_matTarifs_trfIDactivite"  :  {"table"  :  "matTarifs",  "champ" : "trfIDactivite", },
        "IX_matTarifsLignes_trlCodeArticle"  :  {"table"  :  "matTarifsLignes",  "champ" : "trlCodeArticle", },
        "IX_matTarifsLignes_trlCodeTarif"  :  {"table"  :  "matTarifsLignes",  "champ" : "trlCodeTarif", },
        }

if __name__ == "__main__":
    """ Affichage de stats sur les tables """
    nbreChamps = 0
    for nomTable, listeChamps in DB_DATA.iteritems() :
        nbreChamps += len(listeChamps)
    print "Nbre de champs DATA =", nbreChamps
    print "Nbre de tables DATA =", len(DB_DATA.keys())

    app = wx.App()
    f = aGestionDB.Ajout_TablesMat()
    f = aGestionDB.Ajout_IndexMat()

