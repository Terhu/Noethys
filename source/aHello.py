#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
import wx
import aUTILS_Impression_facture
import datetime
from UTILS_Decimal import FloatToDecimal
from decimal import Decimal

#----------------------------------------------------------------------

if __name__ == "__main__":
    app = wx.App(False)

    facture1 = {'{FAMILLE_CP}': u'77230', '{ENFANT_RATTACHE_2_MAIL}': '', 'prelevement': None, '{ENFANT_1_SEXE}': 'M', 'texte_introduction': u'', '{ORGANISATEUR_MAIL}': u'noethys@gmail.com', 'texte_conclusion': u'', '{ENFANT_RATTACHE_1_CP}': u'77230', '{ENFANT_2_FAX_PRO}': '', '{REPRESENTANT_RATTACHE_1_NOM_COMPLET}': u'DARDE Iselande', '{ENFANT_2_ANNEE_DECES}': '', '{ENFANT_RATTACHE_2_RUE}': u'0023\nrue des amarantes\n\n', '{REPRESENTANT_RATTACHE_1_MEMO}': '', '{REPRESENTANT_RATTACHE_1_TEL_MOBILE}': u'06.78.62.06.04', '{MERE_NOM_COMPLET}': u'DARDE Iselande', '{ENFANT_RATTACHE_2_FAX_PRO}': '', '{TOTAL_DEDUCTIONS}': u'0.00 \u20ac', '{REPRESENTANT_RATTACHE_1_LIENS}': u'Iselande est m\xe8re de Joshua et m\xe8re de Kameron', '{REPRESENTANT_RATTACHE_1_EMPLOYEUR}': '', 'prestations_familiales': [], 'IDfamille': 5577, '{REPRESENTANT_RATTACHE_1_SEXE}': 'F', '{ENFANT_RATTACHE_2_DATE_CREATION}': '', '{MERE_MEMO}': '', '{ENFANT_RATTACHE_1_SECTEUR}': '', '{ENFANT_2_NOM}': u'DARDE', '{NOM_LOT}': '', '{ENFANT_RATTACHE_2_CIVILITE_COURT}': '', '{FAMILLE_NOM_CAISSE}': None, '{ENFANT_RATTACHE_2_CP}': u'77230', '{FAMILLE_NOM_ALLOCATAIRE}': '', '{ENFANT_RATTACHE_1_CIVILITE_LONG}': u'Gar\xe7on', '{MERE_TEL_DOMICILE}': u'01.64.02.28.01', '{MERE_NOM}': u'DARDE', '{MERE_MAIL}': '', '{ENFANT_RATTACHE_1_RUE}': u'0023\nrue des amarantes\n\n', '{ENFANT_RATTACHE_2_PRENOM}': u'Kameron', '{MERE_FAX}': u'06.58.97.19.47', '{ENFANT_RATTACHE_1_TEL_MOBILE}': '', '{ORGANISATEUR_VILLE}': u'Lannilis', '{ENFANT_RATTACHE_2_NOM_COMPLET}': u'DARDE Kameron', '{SOLDE_DU}': u'410.00 \u20ac', '{ENFANT_RATTACHE_1_SEXE}': 'M', '{ENFANT_1_TEL_PRO}': '', 'total_reports': Decimal('1291.00'), '{ORGANISATEUR_APE}': u'923M', '{ENFANT_1_FAX}': '', '{ENFANT_2_NOM_COMPLET}': u'DARDE Kameron', '{REPRESENTANT_RATTACHE_1_CP}': u'77230', '{ENFANT_RATTACHE_1_CIVILITE_COURT}': '', '{MERE_RUE}': u'0023\nrue des amarantes\n\n', '{ENFANT_1_NUM_SECU}': '', '{ORGANISATEUR_RUE}': u'10 place des lilas', '{FAMILLE_MEMO}': None, '{REPRESENTANT_RATTACHE_1_PRENOM}': u'Iselande', '{ENFANT_RATTACHE_1_CATEGORIE_TRAVAIL}': '', 'listePrestations': [(0, 12661), (0, 12661), (0, 12661), (6163, 12662)], '{ENFANT_2_PROFESSION}': '', 'num_facture': 3, '{ENFANT_1_CIVILITE_LONG}': u'Gar\xe7on', '{ENFANT_2_TEL_DOMICILE}': '', '{ENFANT_RATTACHE_1_FAX_PRO}': '', '{ENFANT_RATTACHE_2_FAX}': '',
                'individus':
                    {0:  {'nom': u'Prestations familiales',
                         'texte': u'<b>Prestations familiales</b>',
                         'total_reports': Decimal('0.00'),
                         'ventilation': Decimal('0.00'),
                         'activites':
                            {222:
                                {'presences':
                                     {u'2014-09-30 00:00:00.000':
                                        {'total': Decimal('-10.00'),
                                        'unites':
                                            [{'categorie': u'cotisation', 'montant': Decimal('185.00'), 'nomTarif': None, 'deductions': [], 'listeDatesConso': [], 'montant_initial': 85.0, 'date': u'2014-09-30 00:00:00.000', 'IDprestation': 12661, 'tva': None, 'nomCategorieTarif': None, 'label': u'Cotisation annuelle', 'IDtarif': None, 'montant_ventilation': Decimal('0.00')},
                                             {'categorie': u'cotisation', 'montant': Decimal('5.00'), 'nomTarif': None, 'deductions': [], 'listeDatesConso': [], 'montant_initial': 20.0, 'date': u'2014-09-30 00:00:00.000', 'IDprestation': 12661, 'tva': None, 'nomCategorieTarif': None, 'label': u"R\xe9duction Nbre d'enfant", 'IDtarif': None, 'montant_ventilation': Decimal('0.00')},
                                             {'categorie': u'cotisation', 'montant': Decimal('-100.00'), 'nomTarif': None, 'deductions': [], 'listeDatesConso': [], 'montant_initial': 10.0, 'date': u'2014-09-30 00:00:00.000', 'IDprestation': 12661, 'tva': None, 'nomCategorieTarif': None, 'label': u'R\xe9duction Serviteur de Dieu', 'IDtarif': None, 'montant_ventilation': Decimal('0.00')}
                                            ],
                                        'texte': '30/09/2014'
                                        }
                                     },
                                'texte': u'12 CampPasto S2 - 2016'
                                }
                            },
                         'total': Decimal('-10.00'),
                         'select': True
                         },
                    6163:{'nom': u'ABALAIN Jessica', 'texte': u'<b>_ABALAIN Jessica</b><font size=7>, n\xe9e le 22/01/1993</font>', 'total_reports': Decimal('0.00'), 'ventilation': Decimal('0.00'),
                          'activites':
                              {0:
                                   {'presences':
                                        {u'2014-09-30 00:00:00.000':
                                             {'total': Decimal('420.00'),
                                              'unites':
                                                 [{'categorie': u'consommation', 'montant': Decimal('420.00'), 'nomTarif': None, 'deductions': [], 'listeDatesConso': [], 'montant_initial': 480.0, 'date': u'2014-09-30 00:00:00.000', 'IDprestation': 12662, 'tva': None, 'nomCategorieTarif': None, 'label': u'S\xe9jour Jeunes Corse S1', 'IDtarif': None, 'montant_ventilation': Decimal('0.00')}
                                                 ],
                                              'texte': '30/09/2014'
                                              }
                                         },
                                        'texte':  u'Texte ajouté présence'
                                    }
                               },
                          'total': Decimal('420.00'),
                          'select': True
                          }
                    },
                '{ENFANT_RATTACHE_2_AGE_INT}': 15,
                '{MERE_CP}': u'77230',
                '{MESSAGE_1_TEXTE}': u'Impay\xe9s depuis : 01/10/2014\nCL DOUTE DARDE ISABELLE\nCL DOUTE DARDE ISABELLE',
                '{REPRESENTANT_RATTACHE_1_DATE_CREATION}': '','{ENFANT_RATTACHE_1_ANNEE_DECES}': '','{MERE_DATE_CREATION}': '','{ENFANT_RATTACHE_1_MAIL_PRO}': '',
                '{MESSAGE_1_NOM}': None,
                '{ENFANT_RATTACHE_1_NOM_COMPLET}': u'DARDE Joshua',
                '{IDcompte_payeur}': 5577,
                'texte_titre': u'Facture',
                '{ENFANT_RATTACHE_2_TEL_DOMICILE}': '',
                'date_fin': datetime.date(2016, 12, 14),
                '{ENFANT_1_VILLE}': u'MOUSSY LE NEUF',
                '{DATE_ECHEANCE_LONG}': u'Mercredi 5 octobre 2016',
                '{REPRESENTANT_RATTACHE_1_CP_NAISS}': '','{FAMILLE_NOM_REGIME}': None,'{MERE_ANNEE_DECES}': '',
                '{REPRESENTANT_RATTACHE_1_TEL_DOMICILE}': u'01.64.02.28.01','{ENFANT_1_TEL_MOBILE}': '',
                '{SOLDE_AVEC_REPORTS}': u'1701.00 \u20ac',
                '{MERE_SECTEUR}': '','{ENFANT_2_MEMO}': '','{MERE_VILLE_NAISS}': '',
                '{FAMILLE_NOM}': u'DARDE Iselande',
                'ventilation': Decimal('0.00'),'{REPRESENTANT_RATTACHE_1_CATEGORIE_TRAVAIL}': '',
                '{ENFANT_2_DATE_NAISS}': '02/09/2001','{REPRESENTANT_RATTACHE_1_TITULAIRE}': u'Oui','{ENFANT_RATTACHE_2_ANNEE_DECES}': '',
                'num_codeBarre': '0000003',
                '{ENFANT_RATTACHE_2_AGE}': '15 ans','{ENFANT_2_AGE_INT}': 15,'{ENFANT_1_DATE_CREATION}': '',
                '{ORGANISATEUR_SIRET}': u'33215431810023',
                '{REPRESENTANT_RATTACHE_1_ANNEE_DECES}': '','{ENFANT_2_TEL_MOBILE}': '','{ENFANT_RATTACHE_2_TEL_MOBILE}': '',
                '{MERE_CIVILITE_COURT}': u'Mme','{ENFANT_1_MAIL_PRO}': '',
                '{SOLDE_LETTRES}': u'Cinq cent quatre-vingt euros',
                '{ENFANT_1_EMPLOYEUR}': '','{ENFANT_RATTACHE_1_TITULAIRE}': u'Non','{ENFANT_1_MEMO}': '',
                'nomSansCivilite': u'DARDE Iselande',
                '{FAMILLE_DATE_CREATION}': '30/09/2013','{DATE_DEBUT}': '01/07/2015','{DATE_ECHEANCE_COURT}': '05/10/2016',
                'solde_avec_reports': Decimal('1701.00'),
                '{ENFANT_RATTACHE_2_MEMO}': '','{MERE_MAIL_PRO}': '',
                '{TEXTE_ECHEANCE}': u'Ech\xe9ance du r\xe8glement : 05/10/2016',
                '{REPRESENTANT_RATTACHE_1_CIVILITE_COURT}': u'Mme',
                '{ENFANT_RATTACHE_1_CP_NAISS}': '','{ENFANT_RATTACHE_2_EMPLOYEUR}': '','{ENFANT_2_CIVILITE_COURT}': '',
                'reports': {(2014, 9): Decimal('645.50'),
                            (2014, 10): Decimal('645.50')
                            },
                '{IDallocataire}': None,
                '{REPRESENTANT_RATTACHE_1_NOM}': u'DARDE','{ENFANT_RATTACHE_1_PRENOM}': u'Joshua',
                '{ENFANT_RATTACHE_1_AGE}': '9 ans','{ORGANISATEUR_FAX}': u'02.98.02.02.02.','{ENFANT_1_CP_NAISS}': '',
                'date_echeance': datetime.date(2016, 10, 5),
                '{ENFANT_1_FAX_PRO}': '','{FAMILLE_SECTEUR}': None,'{MERE_TEL_MOBILE}': u'06.78.62.06.04','{ENFANT_RATTACHE_2_NUM_SECU}': '',
                'qfdates': {},
                '{ENFANT_RATTACHE_1_VILLE}': u'MOUSSY LE NEUF','{REPRESENTANT_RATTACHE_1_SECTEUR}': '','{ENFANT_2_CATEGORIE_TRAVAIL}': '',
                '{ENFANT_1_NOM_COMPLET}': u'DARDE Joshua','{ENFANT_1_SECTEUR}': '',
                '{NBRE_ENFANTS_RATTACHES}': 2,'total': Decimal('410.00'),'select': True,'{MERE_CP_NAISS}': '','{ENFANT_RATTACHE_1_VILLE_NAISS}': '','{ENFANT_2_CP_NAISS}': '', '{REPRESENTANT_RATTACHE_1_CIVILITE_LONG}': u'Madame', '{ENFANT_RATTACHE_2_PROFESSION}': '', '{ENFANT_2_VILLE}': u'MOUSSY LE NEUF', '{MERE_DATE_NAISS}': '', '{ENFANT_RATTACHE_1_TEL_PRO}': '', '{ENFANT_2_SEXE}': 'M', '{ENFANT_1_AGE}': '9 ans', '{ENFANT_RATTACHE_1_EMPLOYEUR}': '', '{NUMERO_FACTURE}': u'000003', '{ORGANISATEUR_NOM}': u'Fichier exemple par d\xe9faut avec ALSH + P\xe9riscolaire + S\xe9jour', '{ENFANT_RATTACHE_2_SECTEUR}': '', '{MERE_PROFESSION}': '', 'listeDeductions': [], '{ENFANT_2_PRENOM}': u'Kameron', '{ENFANT_RATTACHE_2_TEL_PRO}': '', '{ENFANT_1_AGE_INT}': 9, '{ENFANT_RATTACHE_2_DATE_NAISS}': '02/09/2001', '{MESSAGE_1_DATE_PARUTION}': '01/10/2014', '{ENFANT_RATTACHE_1_NOM}': u'DARDE', '{IDFAMILLE}': 5577, '{MESSAGE_1_CATEGORIE}': u'Probl\xe8me de facturation', '{MERE_CATEGORIE_TRAVAIL}': '', '{REPRESENTANT_RATTACHE_1_RUE}': u'0023\nrue des amarantes\n\n', '{ENFANT_2_NUM_SECU}': '', '{ENFANT_RATTACHE_1_PROFESSION}': '', '{DATE_ECHEANCE}': '05/10/2016', 'reglements': {}, '{FAMILLE_NUM_ALLOCATAIRE}': None, '{TOTAL_PERIODE}': u'410.00 \u20ac', '{REPRESENTANT_RATTACHE_1_MAIL}': '', '{ENFANT_RATTACHE_1_NUM_SECU}': '', '{REPRESENTANT_RATTACHE_1_DATE_NAISS}': '', '{ENFANT_RATTACHE_2_CP_NAISS}': '', '{ORGANISATEUR_SITE}': u'www.noethys.com', '{CODEBARRES_NUM_FACTURE}': 'F000003', '{REPRESENTANT_RATTACHE_1_PROFESSION}': '', '{ENFANT_RATTACHE_1_DATE_NAISS}': '14/07/2007', '{NBRE_CONTACTS_RATTACHES}': 0, '{MERE_EMPLOYEUR}': '', '{ENFANT_2_FAX}': '', '{MERE_AGE_INT}': '', '{ENFANT_1_PROFESSION}': '', '{ENFANT_2_TEL_PRO}': '', '{MESSAGE_1_DATE_SAISIE}': '01/10/2014', '{NUM_FACTURE}': u'000003', '{ENFANT_RATTACHE_2_VILLE_NAISS}': '', '{ORGANISATEUR_AGREMENT}': u'032ORG1234', '{ENFANT_RATTACHE_1_DATE_CREATION}': '', '{ENFANT_1_RUE}': u'0023\nrue des amarantes\n\n', '{ENFANT_RATTACHE_1_MAIL}': '', '{MERE_SEXE}': 'F', '{ENFANT_1_MAIL}': '', '{ENFANT_RATTACHE_2_MAIL_PRO}': '', '{REPRESENTANT_RATTACHE_1_VILLE_NAISS}': '', '{ENFANT_RATTACHE_1_TEL_DOMICILE}': '', '{REPRESENTANT_RATTACHE_1_FAX}': u'06.58.97.19.47', 'solde': Decimal('410.00'), '{REPRESENTANT_RATTACHE_1_FAX_PRO}': '', '{ORGANISATEUR_TEL}': u'02.98.01.01.01.', '{ENFANT_1_DATE_NAISS}': '14/07/2007', '{ENFANT_RATTACHE_2_SEXE}': 'M', '{ENFANT_1_CATEGORIE_TRAVAIL}': '', '{TOTAL_REGLE}': u'0.00 \u20ac', '{ENFANT_1_VILLE_NAISS}': '', '{NBRE_REPRESENTANTS_RATTACHES}': 1, '{ENFANT_2_MAIL}': '', '{ENFANT_RATTACHE_2_CATEGORIE_TRAVAIL}': '', '{MERE_NUM_SECU}': '', '{ORGANISATEUR_CP}': u'29870', '{ENFANT_2_CP}': u'77230', '{MERE_VILLE}': u'MOUSSY LE NEUF', 'messages_familiaux': [], '{ENFANT_RATTACHE_1_FAX}': '', '{ENFANT_RATTACHE_1_LIENS}': u'Joshua est fils de Iselande', '{ENFANT_2_SECTEUR}': '', '{ENFANT_RATTACHE_2_VILLE}': u'MOUSSY LE NEUF', 'date_debut': datetime.date(2015, 7, 1), '{ENFANT_RATTACHE_1_AGE_INT}': 9, '{SOLDE}': u'410.00 \u20ac', '{ENFANT_RATTACHE_2_NOM}': u'DARDE', '{DATE_EDITION_FACTURE}': '08/09/2016', '{ENFANT_2_CIVILITE_LONG}': u'Gar\xe7on', '{ENFANT_2_EMPLOYEUR}': '', 'date_edition': datetime.date(2016, 9, 8), 'liste_activites': [], '{MERE_FAX_PRO}': '', '{DATE_EDITION_LONG}': u'Jeudi 8 septembre 2016', '{REPRESENTANT_RATTACHE_1_AGE}': '', '{REPRESENTANT_RATTACHE_1_MAIL_PRO}': '', '{MERE_PRENOM}': u'Iselande', '{ENFANT_RATTACHE_2_CIVILITE_LONG}': u'Gar\xe7on', '{REPRESENTANT_RATTACHE_1_AGE_INT}': '', '{REPRESENTANT_RATTACHE_1_NUM_SECU}': '', '{ENFANT_2_MAIL_PRO}': '', '{SOLDE_AVEC_REPORTS_LETTRES}': u'Mille huit cent soixante et onze euros', 'numero': u'Facture n\xb00000003', '{FAMILLE_VILLE}': u'MOUSSY LE NEUF', '{MERE_CIVILITE_LONG}': u'Madame', '{ENFANT_RATTACHE_2_LIENS}': u'Kameron est fils de Iselande', '{ENFANT_2_VILLE_NAISS}': '', '{DATE_EDITION_COURT}': '08/09/2016', '{ENFANT_2_DATE_CREATION}': '', '{ENFANT_1_CP}': u'77230', '{ENFANT_1_CIVILITE_COURT}': '', '{ENFANT_1_ANNEE_DECES}': '', '{ENFANT_2_RUE}': u'0023\nrue des amarantes\n\n', '{REPRESENTANT_RATTACHE_1_VILLE}': u'MOUSSY LE NEUF', '{REPRESENTANT_RATTACHE_1_TEL_PRO}': '', '{ENFANT_1_NOM}': u'DARDE', '{MERE_TEL_PRO}': '', '{ENFANT_RATTACHE_1_MEMO}': '', '{ENFANT_RATTACHE_2_TITULAIRE}': u'Non', '{FAMILLE_RUE}': u'0023\nrue des amarantes\n\n', '{ENFANT_2_AGE}': '15 ans', '{DATE_FIN}': '14/12/2016', '{ENFANT_1_TEL_DOMICILE}': '', '{TOTAL_REPORTS}': u'1291.00 \u20ac', '{ENFANT_1_PRENOM}': u'Joshua', '{MERE_AGE}': ''}

    dictFactures = {79: facture1}

    dictOptions  = {u'texte_conclusion': u'', u'image_signature': u'', u'taille_texte_messages': 7, u'afficher_qf_dates': True, u'affichage_prestations': 0, u'taille_image_signature': 100, u'alignement_image_signature': 0, u'couleur_fond_conclusion': wx.Colour(255, 255, 255, 255), u'alignement_texte_introduction': 0, u'afficher_reglements': True, u'integrer_impayes': False, u'taille_texte_activite': 6, u'afficher_periode': True, u'couleur_fond_introduction': wx.Colour(255, 255, 255, 255), u'taille_texte_titre': 19, u'taille_texte_periode': 8, u'IDmodele': 5, u'couleur_fond_2': wx.Colour(234, 234, 255, 255), u'couleur_fond_1': wx.Colour(204, 204, 255, 255), u'afficher_impayes': True, u'afficher_messages': True, u'couleur_bord_conclusion': wx.Colour(255, 255, 255, 255), u'taille_texte_montants_totaux': 10, u'alignement_texte_conclusion': 0, u'largeur_colonne_montant_tva': 50, u'largeur_colonne_date': 50, u'texte_titre': u'Facture', u'taille_texte_prestation': 7, u'afficher_avis_prelevements': True, u'taille_texte_conclusion': 9, u'affichage_solde': 0, u'afficher_coupon_reponse': True, u'taille_texte_introduction': 9, u'intitules': 0, u'taille_texte_noms_colonnes': 5, u'texte_introduction': u'', u'taille_texte_individu': 9, u'taille_texte_labels_totaux': 9, u'couleur_bord_introduction': wx.Colour(255, 255, 255, 255), u'afficher_codes_barres': True, u'afficher_titre': True, u'largeur_colonne_montant_ht': 50, 'messages': [], u'memoriser_parametres': True, u'largeur_colonne_montant_ttc': 70, u'style_texte_introduction': 0, u'style_texte_conclusion': 0, u'repertoire_copie': u''}
    aUTILS_Impression_facture.Impression(dictFactures, dictOptions, IDmodele = 5, ouverture = True, nomFichier=None)

    app.MainLoop()