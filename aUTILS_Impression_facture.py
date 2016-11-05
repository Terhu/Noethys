#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, Matthania
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS, Jacques BRUNEL
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
# Adaptation sur les tri des blocs, sur les noms au lieu des textes
#------------------------------------------------------------------------


from UTILS_Traduction import _
import wx
import CTRL_Bouton_image
import os
import datetime
import decimal
import FonctionsPerso
from UTILS_Decimal import FloatToDecimal as FloatToDecimal
import DLG_Noedoc

import UTILS_Config
SYMBOLE = UTILS_Config.GetParametre("monnaie_symbole", u"€")

from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, NextPageTemplate
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import ParagraphAndImage, Image
from reportlab.platypus.frames import Frame, ShowBoundaryValue
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics.barcode import code39, qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import DocAssign, Flowable


TAILLE_PAGE = A4
LARGEUR_PAGE = TAILLE_PAGE[0]
HAUTEUR_PAGE = TAILLE_PAGE[1]
CADRE_CONTENU = (5*cm, 5*cm, 14*cm, 17*cm)
    
DICT_VALEURS = {}
DICT_OPTIONS = {} 


def DateEngFr(textDate):
    text = str(textDate[8:10]) + u"/" + str(textDate[5:7]) + u"/" + str(textDate[:4])
    return text

def PeriodeComplete(mois, annee):
    listeMois = (_(u"Janvier"), _(u"Février"), _(u"Mars"), _(u"Avril"), _(u"Mai"), _(u"Juin"), _(u"Juillet"), _(u"Août"), _(u"Septembre"), _(u"Octobre"), _(u"Novembre"), _(u"Décembre"))
    periodeComplete = u"%s %d" % (listeMois[mois-1], annee)
    return periodeComplete

def ConvertCouleurWXpourPDF(couleurwx=(0, 0, 0)):
    return (couleurwx[0]/255.0, couleurwx[1]/255.0, couleurwx[2]/255.0)

def ConvertCouleurPDFpourWX(couleurpdf=(0, 0, 0)):
    return (couleurpdf[0]*255.0, couleurpdf[1]*255.0, couleurpdf[2]*255.0)

def Template(canvas, doc):
    """ Première page de l'attestation """
    doc.modeleDoc.DessineFond(canvas) 
    doc.modeleDoc.DessineFormes(canvas)

class MyPageTemplate(PageTemplate):
    def __init__(self, id=-1, pageSize=TAILLE_PAGE, doc=None):
        self.pageWidth = pageSize[0]
        self.pageHeight = pageSize[1]
        
        # Récupère les coordonnées du cadre principal
        cadre_principal = doc.modeleDoc.FindObjet("cadre_principal")
        x, y, l, h = doc.modeleDoc.GetCoordsObjet(cadre_principal)
        global CADRE_CONTENU
        CADRE_CONTENU = (x, y, l, h)
        
        frame1 = Frame(x, y, l, h, id='F1', leftPadding=0, topPadding=0, rightPadding=0, bottomPadding=0)
        PageTemplate.__init__(self, id, [frame1], Template) 

    def afterDrawPage(self, canvas, doc):
        IDcompte_payeur = doc._nameSpace["IDcompte_payeur"]
        dictValeur = DICT_VALEURS[IDcompte_payeur]
        
        # Dessin du coupon-réponse vertical
        coupon_vertical = doc.modeleDoc.FindObjet("coupon_vertical")
        if DICT_OPTIONS.has_key("afficher_coupon_reponse") and DICT_OPTIONS["afficher_coupon_reponse"] == True and coupon_vertical != None :
            x, y, largeur, hauteur = doc.modeleDoc.GetCoordsObjet(coupon_vertical)
            canvas.saveState() 
            # Ciseaux
            canvas.drawImage("Images/Special/Ciseaux.png", x+1*mm, y+hauteur-5*mm, 0.5*cm, 1*cm, preserveAspectRatio=True)
            # Rectangle
            canvas.setDash(3, 3)
            canvas.setLineWidth(0.25)
            canvas.setStrokeColorRGB(0, 0, 0)
            canvas.rect(x, y, largeur, hauteur, fill=0)
            # Textes
            canvas.rotate(90)
            canvas.setFont("Helvetica", 8)
            canvas.drawString(y+2*mm, -x-4*mm, _(u"Merci de joindre ce coupon à votre règlement"))
            canvas.setFont("Helvetica", 7)
            solde = dictValeur["total"] - dictValeur["ventilation"]
            if DICT_OPTIONS["integrer_impayes"] == True :
                solde += dictValeur["total_reports"]
            numero = dictValeur["numero"]
            nom = dictValeur["nomSansCivilite"]
            canvas.drawString(y+2*mm, -x-9*mm, u"%s - %.02f %s" % (numero, solde, SYMBOLE))
            canvas.drawString(y+2*mm, -x-12*mm, u"%s" % nom)
            # Code-barres
            if DICT_OPTIONS["afficher_codes_barres"] == True and dictValeur.has_key("{CODEBARRES_NUM_FACTURE}") :
                barcode = code39.Extended39(dictValeur["{CODEBARRES_NUM_FACTURE}"], humanReadable=False)
                barcode.drawOn(canvas, y+36*mm, -x-13*mm)
            canvas.restoreState()

        # Dessin du coupon-réponse horizontal
        coupon_horizontal = doc.modeleDoc.FindObjet("coupon_horizontal")
        if DICT_OPTIONS.has_key("afficher_coupon_reponse") and DICT_OPTIONS["afficher_coupon_reponse"] == True and coupon_horizontal != None :
            x, y, largeur, hauteur = doc.modeleDoc.GetCoordsObjet(coupon_horizontal)
            canvas.saveState() 
            # Rectangle
            canvas.setDash(3, 3)
            canvas.setLineWidth(0.25)
            canvas.setStrokeColorRGB(0, 0, 0)
            canvas.rect(x, y, largeur, hauteur, fill=0)
            # Textes
            canvas.setFont("Helvetica", 8)
            canvas.drawString(x+2*mm, y+hauteur-4*mm, _(u"Merci de joindre ce coupon à votre règlement"))
            canvas.setFont("Helvetica", 7)
            solde = dictValeur["total"] - dictValeur["ventilation"]
            if DICT_OPTIONS["integrer_impayes"] == True :
                solde += dictValeur["total_reports"]
            numero = dictValeur["numero"]
            nom = dictValeur["nomSansCivilite"]
            canvas.drawString(x+2*mm, y+hauteur-9*mm, u"%s - %.02f %s" % (numero, solde, SYMBOLE))
            canvas.drawString(x+2*mm, y+hauteur-12*mm, u"%s" % nom)
            # Code-barres
            if DICT_OPTIONS["afficher_codes_barres"] == True :
                barcode = code39.Extended39(dictValeur["{CODEBARRES_NUM_FACTURE}"], humanReadable=False)
                barcode.drawOn(canvas, x+36*mm, y+hauteur-13*mm)
            # Ciseaux
            canvas.rotate(-90)
            canvas.drawImage("Images/Special/Ciseaux.png", -y-hauteur+1*mm, x+largeur-5*mm, 0.5*cm, 1*cm, preserveAspectRatio=True)
            canvas.restoreState()

        canvas.saveState() 
        
        # Insertion du code39
        if DICT_OPTIONS.has_key("afficher_codes_barres") and DICT_OPTIONS["afficher_codes_barres"] == True :
            doc.modeleDoc.DessineCodesBarres(canvas, dictChamps=dictValeur)
        
        # Insertion des lignes de textes
        doc.modeleDoc.DessineImages(canvas, dictChamps=dictValeur)
        doc.modeleDoc.DessineTextes(canvas, dictChamps=dictValeur)
        
        canvas.restoreState()

def Template_PagesSuivantes(canvas, doc):
    """ Première page de l'attestation """
    canvas.saveState()

    canvas.setFont('Times-Roman', 12)
    pageNumber = canvas.getPageNumber()
    canvas.drawCentredString(10*cm, cm, str(pageNumber))

    canvas.restoreState()

class Bookmark(Flowable):
    """ Utility class to display PDF bookmark. """
    def __init__(self, title, key):
        self.title = title
        self.key = key
        Flowable.__init__(self)

    def wrap(self, availWidth, availHeight):
        """ Doesn't take up any space. """
        return (0, 0)

    def draw(self):
        # set the bookmark outline to show when the file's opened
        self.canv.showOutline()
        # step 1: put a bookmark on the 
        self.canv.bookmarkPage(self.key)
        # step 2: put an entry in the bookmark outline
        self.canv.addOutlineEntry(self.title, self.key, 0, 0)

class Impression():
    def __init__(self, dictValeurs={}, dictOptions={}, IDmodele=None, mode="facture", ouverture=True, nomFichier=None, titre=None):
        """ Impression """
        global DICT_VALEURS, DICT_OPTIONS
        DICT_VALEURS = dictValeurs
        DICT_OPTIONS = dictOptions
        self.mode = mode
        
        detail = 0
        if dictOptions["affichage_prestations"] != None :
            detail = dictOptions["affichage_prestations"]
        
        # Initialisation du document
        if nomFichier == None :
            nomDoc = _(u"Temp/%ss_%s.pdf") % (mode, FonctionsPerso.GenerationIDdoc())
        else :
            nomDoc = nomFichier
        doc = BaseDocTemplate(nomDoc, pagesize=TAILLE_PAGE, showBoundary=False)
        
        # Mémorise le ID du modèle
        modeleDoc = DLG_Noedoc.ModeleDoc(IDmodele=IDmodele)
        doc.modeleDoc = modeleDoc

        # Vérifie qu'un cadre principal existe bien dans le document
        if doc.modeleDoc.FindObjet("cadre_principal") == None :
            raise Exception("Votre modèle de document doit obligatoirement comporter un cadre principal. Retournez dans l'éditeur de document et utilisez pour votre modèle la commande 'Insérer un objet spécial > Insérer le cadre principal'.")
        
        # Importe le template de la première page
        doc.addPageTemplates(MyPageTemplate(pageSize=TAILLE_PAGE, doc=doc))
        
        story = []
        styleSheet = getSampleStyleSheet()
        h3 = styleSheet['Heading3']
        styleTexte = styleSheet['BodyText'] 
        styleTexte.fontName = "Helvetica"
        styleTexte.fontSize = 9
        styleTexte.borderPadding = 9
        styleTexte.leading = 12

        # ----------- Insertion du contenu des frames --------------
        listeNomsSansCivilite = []
        for IDcompte_payeur, dictValeur in dictValeurs.iteritems() :
            listeNomsSansCivilite.append((dictValeur["nomSansCivilite"], IDcompte_payeur))
        listeNomsSansCivilite.sort()

        for nomSansCivilite, IDcompte_payeur in listeNomsSansCivilite :
            dictValeur = dictValeurs[IDcompte_payeur]
            if dictValeur["select"] == True :
                
                story.append(DocAssign("IDcompte_payeur", IDcompte_payeur))
                nomSansCivilite = dictValeur["nomSansCivilite"]
                story.append(Bookmark(nomSansCivilite, str(IDcompte_payeur)))
                
                # ------------------- TITRE -----------------
                if dictOptions["afficher_titre"] == True :
                    if titre == None :
                        if mode == "facture" : titre = _(u"Facture")
                        if mode == "attestation" : titre = _(u"Attestation de présence")
                        if mode == "devis" : titre = _(u"Devis")
                        #if dictValeur.has_key("texte_titre") :
                        #    titre = dictValeur["texte_titre"]
                    dataTableau = []
                    largeursColonnes = [ CADRE_CONTENU[2], ]
                    dataTableau.append((titre,))
                    texteDateDebut = DateEngFr(str(dictValeur["date_debut"]))
                    texteDateFin = DateEngFr(str(dictValeur["date_fin"]))
                    if dictOptions["afficher_periode"] == True :
                        dataTableau.append((_(u"Période du %s au %s") % (texteDateDebut, texteDateFin),))
                    styles = [
                            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), 
                            ('FONT',(0,0),(0,0), "Helvetica-Bold", dictOptions["taille_texte_titre"]), 
                            ('LINEBELOW', (0,0), (0,0), 0.25, colors.black), 
                            ('ALIGN', (0,0), (-1,-1), 'LEFT'), 
                            ]
                    
                    if dictOptions["afficher_periode"] == True :
                        styles.append(('FONT',(0,1),(0,1), "Helvetica", dictOptions["taille_texte_periode"]))
                    tableau = Table(dataTableau, largeursColonnes)
                    tableau.setStyle(TableStyle(styles))
                    story.append(tableau)
                    story.append(Spacer(0,20))
                
                # TEXTE D'INTRODUCTION pour Attestation
                #  if mode == "attestation" and dictValeur["intro"] != None :

                if dictOptions["texte_introduction"] != "" :
                    paraStyle = ParagraphStyle(name="introduction",
                                          fontName="Helvetica",
                                          fontSize=dictOptions["taille_texte_introduction"],
                                          leading=14,
                                          spaceBefore=0,
                                          spaceafter=0,
                                          leftIndent=5,
                                          rightIndent=5,
                                          alignment=dictOptions["alignement_texte_introduction"],
                                          backColor=ConvertCouleurWXpourPDF(dictOptions["couleur_fond_introduction"]),
                                          borderColor=ConvertCouleurWXpourPDF(dictOptions["couleur_bord_introduction"]),
                                          borderWidth=0.5,
                                          borderPadding=5,
                                        )
                    texte = dictValeur["texte_introduction"].replace("\\n", "<br/>")
                    if dictOptions["style_texte_introduction"] == 0 : texte = u"<para>%s</para>" % texte
                    if dictOptions["style_texte_introduction"] == 1 : texte = u"<para><i>%s</i></para>" % texte
                    if dictOptions["style_texte_introduction"] == 2 : texte = u"<para><b>%s</b></para>" % texte
                    if dictOptions["style_texte_introduction"] == 3 : texte = u"<para><i><b>%s</b></i></para>" % texte
                    story.append(Paragraph(texte, paraStyle))
                    story.append(Spacer(0,20))

                    
                couleurFond = ConvertCouleurWXpourPDF(dictOptions["couleur_fond_1"]) # (0.8, 0.8, 1)
                couleurFondActivite = ConvertCouleurWXpourPDF(dictOptions["couleur_fond_2"]) # (0.92, 0.92, 1)

                # ------------------- TABLEAU CONTENU -----------------
                montantPeriode = FloatToDecimal(0.0)
                montantVentilation = FloatToDecimal(0.0)

                # Recherche si TVA utilisée
                activeTVA = False
                for IDindividu, dictIndividus in dictValeur["individus"].iteritems() :
                    for IDactivite, dictActivites in dictIndividus["activites"].iteritems() :
                        for date, dictDates in dictActivites["presences"].iteritems() :
                            for dictPrestation in dictDates["unites"] :
                                if dictPrestation["tva"] != None and dictPrestation["tva"] != 0.0 :
                                    activeTVA = True

                # Remplissage
                listeIndividusTemp = []
                for IDindividu, dictIndividus in dictValeur["individus"].iteritems() :
                    listeIndividusTemp.append((dictIndividus["nom"], IDindividu, dictIndividus))
                listeIndividusTemp.sort()

                for texteTemp, IDindividu, dictIndividus in listeIndividusTemp :
                    
                    if dictIndividus["select"] == True :
                        
                        listeIndexActivites = []
                        montantPeriode += dictIndividus["total"]
                        montantVentilation += dictIndividus["ventilation"]
                        
                        # Initialisation des largeurs de tableau
                        largeurColonneDate = dictOptions["largeur_colonne_date"]
                        largeurColonneMontantHT = dictOptions["largeur_colonne_montant_ht"]
                        largeurColonneTVA = dictOptions["largeur_colonne_montant_tva"]
                        largeurColonneMontantTTC = dictOptions["largeur_colonne_montant_ttc"]
                        largeurColonneBaseTTC = largeurColonneMontantTTC
                        
                        if activeTVA == True and detail == 0 :
                            largeurColonneIntitule = CADRE_CONTENU[2] - largeurColonneDate - largeurColonneMontantHT - largeurColonneTVA - largeurColonneMontantTTC
                            largeursColonnes = [ largeurColonneDate, largeurColonneIntitule, largeurColonneMontantHT, largeurColonneTVA, largeurColonneMontantTTC]
                        else :
                            if detail != 0 :
                                largeurColonneIntitule = CADRE_CONTENU[2] - largeurColonneDate - largeurColonneBaseTTC - largeurColonneMontantTTC
                                largeursColonnes = [ largeurColonneDate, largeurColonneIntitule, largeurColonneBaseTTC, largeurColonneMontantTTC]
                            else :
                                largeurColonneIntitule = CADRE_CONTENU[2] - largeurColonneDate - largeurColonneMontantTTC
                                largeursColonnes = [ largeurColonneDate, largeurColonneIntitule, largeurColonneMontantTTC]
                        
                        # Insertion du nom de l'individu
                        paraStyle = ParagraphStyle(name="individu",
                                              fontName="Helvetica",
                                              fontSize=dictOptions["taille_texte_individu"],
                                              leading=dictOptions["taille_texte_individu"],
                                              spaceBefore=0,
                                              spaceafter=0,
                                            )
                        texteIndividu = Paragraph(dictIndividus["texte"], paraStyle)
                        dataTableau = []
                        dataTableau.append([texteIndividu,])
                        tableau = Table(dataTableau, [CADRE_CONTENU[2],])
                        listeStyles = [
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('FONT', (0, 0), (-1, -1), "Helvetica", dictOptions["taille_texte_individu"]), 
                                ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                                ('BACKGROUND', (0, 0), (-1, 0), couleurFond),
                                ]
                        tableau.setStyle(TableStyle(listeStyles))
                        story.append(tableau)
                        
                        # Insertion du nom de l'activité
                        listeIDactivite = []
                        for IDactivite, dictActivites in dictIndividus["activites"].iteritems() :
                            listeIDactivite.append((dictActivites["texte"], IDactivite, dictActivites))
                        listeIDactivite.sort() 
                        
                        for texteActivite, IDactivite, dictActivites in listeIDactivite :

                            texteActivite = dictActivites["texte"]
                            if texteActivite != None :
                                dataTableau = []
                                dataTableau.append([texteActivite,])
                                tableau = Table(dataTableau, [CADRE_CONTENU[2],])
                                listeStyles = [
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('FONT', (0, 0), (-1, -1), "Helvetica", dictOptions["taille_texte_activite"]),
                                    ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
                                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                    ('BACKGROUND', (0, 0), (-1, 0), couleurFondActivite),
                                    ]
                                tableau.setStyle(TableStyle(listeStyles))
                                story.append(tableau)

                            # Style de paragraphe normal
                            paraStyle = ParagraphStyle(name="prestation",
                                          fontName="Helvetica",
                                          fontSize=dictOptions["taille_texte_prestation"],
                                          leading=dictOptions["taille_texte_prestation"],
                                          spaceBefore=0,
                                          spaceAfter=0,
                                          )

                            paraLabelsColonnes = ParagraphStyle(name="paraLabelsColonnes",
                                          fontName="Helvetica",
                                          fontSize=dictOptions["taille_texte_noms_colonnes"],
                                          leading=dictOptions["taille_texte_noms_colonnes"],
                                          spaceBefore=0,
                                          spaceAfter=0,
                                          )

                            #if detail != 0 :
                            # -------------- MODE REGROUPE ----------------

                            # -------------- MODE DETAILLE ------------------------------------------------------------------
                            # Insertion de la date
                            listeDates = []
                            for date, dictDates in dictActivites["presences"].iteritems() :
                                listeDates.append(date)
                            listeDates.sort()

                            paraStyle = ParagraphStyle(name="prestation",
                                          fontName="Helvetica",
                                          fontSize=dictOptions["taille_texte_prestation"],
                                          leading=dictOptions["taille_texte_prestation"],
                                          spaceBefore=0,
                                          spaceAfter=0,
                                          )

                            dataTableau = []

                            if activeTVA == True :
                                dataTableau.append([
                                    Paragraph(_(u"<para align='center'>Date</para>"), paraLabelsColonnes),
                                    Paragraph(_(u"<para align='center'>Prestation</para>"), paraLabelsColonnes),
                                    Paragraph(_(u"<para align='center'>Montant HT</para>"), paraLabelsColonnes),
                                    Paragraph(_(u"<para align='center'>Taux TVA</para>"), paraLabelsColonnes),
                                    Paragraph(_(u"<para align='center'>Montant TTC</para>"), paraLabelsColonnes),
                                    ])

                            for date in listeDates :
                                dictDates = dictActivites["presences"][date]

                                date = dictDates["texte"]
                                prestations = dictDates["unites"]

                                # Insertion des unités de présence
                                listeIntitules = []
                                listeMontantsHT = []
                                listeTVA = []
                                listeMontantsTTC = []
                                texteIntitules = u""
                                texteMontantsHT = u""
                                texteTVA = u""
                                texteMontantsTTC = u""

                                # Tri par ordre alpha des prestations
                                listeDictPrestations = []
                                for dictPrestation in prestations :
                                    listeDictPrestations.append((dictPrestation["label"], dictPrestation))
                                #listeDictPrestations.sort()

                                for labelTemp, dictPrestation in listeDictPrestations :
                                    label = dictPrestation["label"]
                                    montant_initial = dictPrestation["montant_initial"]
                                    montant = dictPrestation["montant"]
                                    deductions = dictPrestation["deductions"]
                                    tva = dictPrestation["tva"]

                                    # Date
                                    #texteDate = Paragraph("<para align='center'>%s</para>" % date, paraStyle)
                                    texteDate = " "

                                    # recherche d'un commentaire
                                    if dictOptions.has_key("dictCommentaires") :
                                        key = (label, IDactivite)
                                        if dictOptions["dictCommentaires"].has_key(key) :
                                            commentaire = dictOptions["dictCommentaires"][key]
                                            label = "%s <i><font color='#939393'>%s</font></i>" % (label, commentaire)

                                    # Affiche le Label de la prestation
                                    if label == None:
                                        label = u"Pour l'ensemble de la famille"
                                    listeIntitules.append(Paragraph(label, paraStyle))

                                    # TVA
                                    if activeTVA == True :
                                        if tva == None : tva = 0.0
                                        montantHT = (100.0 * float(montant)) / (100 + float(tva)) #montant - montant * 1.0 * float(tva) / 100
                                        listeMontantsHT.append(Paragraph(u"<para align='center'>%.02f %s</para>" % (montantHT, SYMBOLE), paraStyle))
                                        listeTVA.append(Paragraph(u"<para align='center'>%.02f %%</para>" % tva, paraStyle))
                                    else :
                                        listeMontantsHT.append("")
                                        listeTVA.append("")

                                    # Affiche total
                                    if montant == 0.00:
                                        listeMontantsTTC.append(Spacer(10,dictOptions["taille_texte_prestation"]))
                                    else:
                                        listeMontantsTTC.append(Paragraph(u"<para align='right'>%.02f %s</para>" % (montant, SYMBOLE), paraStyle))

                                    # Déductions
                                    if len(deductions) > 0 :
                                        for dictDeduction in deductions :
                                            listeIntitules.append(Paragraph(u"<para align='left'><font size=5 color='#939393'>- %.02f %s : %s</font></para>" % (dictDeduction["montant"], SYMBOLE, dictDeduction["label"]), paraStyle))
                                            #listeIntitules.append(Paragraph(u"<para align='left'><font size=5 color='#939393'>%s</font></para>" % dictDeduction["label"], paraStyle))
                                            listeMontantsHT.append(Paragraph("&nbsp;", paraStyle))
                                            listeTVA.append(Paragraph("&nbsp;", paraStyle))
                                            listeMontantsTTC.append(Paragraph("&nbsp;", paraStyle))
                                            #listeMontantsTTC.append(Paragraph(u"<para align='center'><font size=5 color='#939393'>- %.02f %s</font></para>" % (dictDeduction["montant"], SYMBOLE), paraStyle))

                                if len(listeIntitules) == 1 :
                                    texteIntitules = listeIntitules[0]
                                    texteMontantsHT = listeMontantsHT[0]
                                    texteTVA = listeTVA[0]
                                    texteMontantsTTC = listeMontantsTTC[0]
                                if len(listeIntitules) > 1 :
                                    texteIntitules = listeIntitules
                                    texteMontantsHT = listeMontantsHT
                                    texteTVA = listeTVA
                                    texteMontantsTTC = listeMontantsTTC

                                if activeTVA == True :
                                    dataTableau.append([texteDate, texteIntitules, texteMontantsHT, texteTVA, texteMontantsTTC])
                                else :
                                    dataTableau.append([texteDate, texteIntitules, texteMontantsTTC])

                            # Style du tableau des prestations
                            tableau = Table(dataTableau, largeursColonnes)
                            listeStyles = [
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('FONT', (0, 0), (-1, -1), "Helvetica", dictOptions["taille_texte_prestation"]), 
                                ('GRID', (0, 0), (-1,-1), 0.25, colors.black), 
                                ('ALIGN', (0, 0), (-1, -1), 'CENTRE'),
                                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                                ('TOPPADDING', (0, 0), (-1, -1), 1), 
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 3), 
                                ]
                            tableau.setStyle(TableStyle(listeStyles))
                            story.append(tableau)
                        
                        # Insertion des totaux
                        dataTableau = []
                        if activeTVA == True and detail == 0 :
                            dataTableau.append(["", "", "", "", Paragraph("<para align='center'>%.02f %s</para>" % (dictIndividus["total"], SYMBOLE) , paraStyle)])
                        else :
                            if detail != 0 :
                                dataTableau.append(["", "", "", Paragraph("<para align='center'>%.02f %s</para>" % (dictIndividus["total"], SYMBOLE) , paraStyle)])
                            else :
                                dataTableau.append(["", "", Paragraph("<para align='center'>%.02f %s</para>" % (dictIndividus["total"], SYMBOLE) , paraStyle)])
                        
                        listeStyles = [
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('FONT', (0, 0), (-1, -1), "Helvetica", dictOptions["taille_texte_prestation"]), 
                                ('GRID', (-1, -1), (-1,-1), 0.25, colors.black), 
                                ('ALIGN', (-1, -1), (-1, -1), 'CENTRE'),
                                ('BACKGROUND', (-1, -1), (-1, -1), couleurFond), 
                                ('TOPPADDING', (0, 0), (-1, -1), 1), 
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 3), 
                                ]
                            
                        # Création du tableau
                        tableau = Table(dataTableau, largeursColonnes)
                        tableau.setStyle(TableStyle(listeStyles))
                        story.append(tableau)
                        story.append(Spacer(0, 10))
                
                # Intégration des messages, des reports et des qf
                listeMessages = []
                paraStyle = ParagraphStyle(name="message",
                                          fontName="Helvetica",
                                          fontSize=dictOptions["taille_texte_messages"],
                                          leading=dictOptions["taille_texte_messages"],
                                          #spaceBefore=0,
                                          spaceAfter=2,
                                        )
                
                # Date d'échéance
##                if dictOptions["echeance"] != None :
##                    listeMessages.append(Paragraph(dictOptions["echeance"], paraStyle))

               # QF aux dates de facture
                if dictOptions["afficher_qf_dates"] == True :
                    dictQfdates = dictValeur["qfdates"]
                    listeDates = dictQfdates.keys() 
                    listeDates.sort() 
                    if len(listeDates) > 0 :
                        for dates in listeDates :
                            qf = dictQfdates[dates]
##                            texteQf = _(u"--- Votre QF %s : <b>%s</b> ---") % (dates, qf)
                            texteQf = _(u"<b>Votre quotient familial : </b>Votre QF est de %s sur la période %s.") % (qf, dates)
                            listeMessages.append(Paragraph(texteQf, paraStyle))
                
                
                # Reports
                if dictOptions["afficher_impayes"] == True :
                    dictReports = dictValeur["reports"]
                    listePeriodes = dictReports.keys() 
                    listePeriodes.sort() 
                    if len(listePeriodes) > 0 :
                        if dictOptions["integrer_impayes"] == True :
                            texteReport = _(u"<b>Détail des impayés : </b>")
                        else :
                            texteReport = _(u"<b>Impayés : </b>Merci de bien vouloir nous retourner également le règlement des prestations antérieures : ")
                        for periode in listePeriodes :
                            annee, mois = periode
                            nomPeriode = PeriodeComplete(mois, annee)
                            montant_impaye = dictReports[periode]
                            texteReport += u"%s (%.02f %s), " % (nomPeriode, montant_impaye, SYMBOLE)
                        texteReport = texteReport[:-2] + u"."
                        listeMessages.append(Paragraph(texteReport, paraStyle))
                
                # Règlements
                if dictOptions["afficher_reglements"] == True :
                    dictReglements = dictValeur["reglements"]
                    if len(dictReglements) > 0 :
                        listeTextesReglements = []
                        for IDreglement, dictTemp in dictReglements.iteritems() :
                            if dictTemp["emetteur"] not in ("", None) :
                                emetteur = u" (%s) " % dictTemp["emetteur"]
                            else :
                                emetteur = ""
                            if dictTemp["numero"] not in ("", None) :
                                numero = u" n°%s " % dictTemp["numero"]
                            else :
                                numero = ""
                                
                            montantReglement = u"%.02f %s" % (dictTemp["montant"], SYMBOLE)
                            montantVentilation = u"%.02f %s" % (dictTemp["ventilation"], SYMBOLE)
                            if dictTemp["ventilation"] != dictTemp["montant"] :
                                texteMontant = u"%s utilisés sur %s" % (montantVentilation, montantReglement)
                            else :
                                texteMontant = montantReglement
                                
                            texte = u"%s%s%s de %s (%s)" % (dictTemp["mode"], numero, emetteur, dictTemp["payeur"], texteMontant)
                            listeTextesReglements.append(texte)
                        
                        if dictValeur["solde"] > FloatToDecimal(0.0) :
                            intro = u"Partiellement réglé"
                        else :
                            intro = u"Réglé en intégralité"
                            
                        texteReglements = _(u"<b>Règlement : </b> %s") % (intro)
                        listeMessages.append(Paragraph(texteReglements, paraStyle))
                        for ligne in listeTextesReglements:
                            listeMessages.append(Paragraph(ligne, paraStyle))
                # Messages
                if dictOptions["afficher_messages"] == True :
                    for message in dictOptions["messages"] :
                        listeMessages.append(Paragraph(message, paraStyle))

                    for message_familial in dictValeur["messages_familiaux"] :
                        texte = message_familial["texte"]
                        if len(texte) > 0 and texte[-1] not in ".!?" :
                            texte = texte + u"."
                        texte = _(u"<b>Message : </b>%s") % texte
                        listeMessages.append(Paragraph(texte, paraStyle))

                if len(listeMessages) > 0 :
                    listeMessages.insert(0, Paragraph(_(u"<u>Informations :</u>"), paraStyle))
                
                # ------------------ CADRE TOTAUX ------------------------
                dataTableau = []
                largeurColonneLabel = 110
                largeursColonnes = [ CADRE_CONTENU[2] - largeurColonneMontantTTC - largeurColonneLabel, largeurColonneLabel, largeurColonneMontantTTC]

                dataTableau.append((listeMessages, _(u"Total période :"), u"%.02f %s" % (dictValeur["total"], SYMBOLE)))
                dataTableau.append(("", _(u"Montant déjà réglé :"), u"%.02f %s" % (dictValeur["ventilation"], SYMBOLE)))

                if dictValeur["total"] - dictValeur["ventilation"] > 0.0 :
                    if dictOptions["integrer_impayes"] == True :
                        dataTableau.append(("", _(u"Report impayés :"), u"%.02f %s" % (dictValeur["total_reports"], SYMBOLE) ))
                        dataTableau.append(("", _(u"Reste à régler :"), u"%.02f %s" % (dictValeur["solde"] + dictValeur["total_reports"], SYMBOLE) ))
                        rowHeights=[10, 10, 10, None]
                    else :
                        dataTableau.append(("", _(u"Reste à régler :"), u"%.02f %s" % (dictValeur["solde"], SYMBOLE) ))
                        rowHeights=[18, 18, None]
                else:
                        dataTableau.append(("", _(u"Facture acquittée "),"-"))

                style = [
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
##                        ('FONT', (1, 0), (1, -1), "Helvetica", 7),#dictOptions["taille_texte_labels_totaux"]), 
##                        ('FONT', (2, 0), (2, -1), "Helvetica-Bold", 7),#dictOptions["taille_texte_montants_totaux"]), 
                        
                        # Lignes Période, avoir, impayés
                        ('FONT', (1, 0), (1, -2), "Helvetica", 8),#dictOptions["taille_texte_labels_totaux"]), 
                        ('FONT', (2, 0), (2, -2), "Helvetica-Bold", 8),#dictOptions["taille_texte_montants_totaux"]), 
                        
                        # Ligne Reste à régler
                        ('FONT', (1, -1), (1, -1), "Helvetica-Bold", dictOptions["taille_texte_labels_totaux"]), 
                        ('FONT', (2, -1), (2, -1), "Helvetica-Bold", dictOptions["taille_texte_montants_totaux"]), 
                        
                        ('GRID', (2, 0), (2, -1), 0.25, colors.black),
                        
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                        ('ALIGN', (2, 0), (2, -1), 'CENTRE'), 
                        ('BACKGROUND', (2, -1), (2, -1), couleurFond),
                        
                        ('SPAN', (0, 0), (0, -1)), 
                        ]
                
                if len(listeMessages) > 0 :
                    #style.append( ('BACKGROUND', (0, 0), (0, 0), couleurFondActivite) )
                    style.append( ('FONT', (0, 0), (0, -1), "Helvetica", 8)  )
                    style.append( ('VALIGN', (0, 0), (0, -1), 'TOP') )
                    
                tableau = Table(dataTableau, largeursColonnes)#, rowHeights=rowHeights)
                tableau.setStyle(TableStyle(style))
                story.append(tableau)
                
                # ------------------------- PRELEVEMENTS --------------------
                if dictOptions.has_key("afficher_avis_prelevements") and dictValeur.has_key("prelevement") :
                    if dictValeur["prelevement"] != None and dictOptions["afficher_avis_prelevements"] == True :
                        paraStyle = ParagraphStyle(name="intro",
                              fontName="Helvetica",
                              fontSize=8,
                              leading=11,
                              spaceBefore=2,
                              spaceafter=2,
                              alignment=1,
                              backColor=couleurFondActivite,
                            )
                        story.append(Spacer(0,20))
                        story.append(Paragraph(u"<para align='center'><i>%s</i></para>" % dictValeur["prelevement"], paraStyle))
                
                # Texte conclusion
                if dictOptions["texte_conclusion"] != "" :
                    story.append(Spacer(0,20))
                    paraStyle = ParagraphStyle(name="conclusion",
                                          fontName="Helvetica",
                                          fontSize=dictOptions["taille_texte_conclusion"],
                                          leading=14,
                                          spaceBefore=0,
                                          spaceafter=0,
                                          leftIndent=5,
                                          rightIndent=5,
                                          alignment=dictOptions["alignement_texte_conclusion"],
                                          backColor=ConvertCouleurWXpourPDF(dictOptions["couleur_fond_conclusion"]),
                                          borderColor=ConvertCouleurWXpourPDF(dictOptions["couleur_bord_conclusion"]),
                                          borderWidth=0.5,
                                          borderPadding=5,
                                        )
            
                    texte = dictValeur["texte_conclusion"].replace("\\n", "<br/>")
                    if dictOptions["style_texte_conclusion"] == 0 : texte = u"<para>%s</para>" % texte
                    if dictOptions["style_texte_conclusion"] == 1 : texte = u"<para><i>%s</i></para>" % texte
                    if dictOptions["style_texte_conclusion"] == 2 : texte = u"<para><b>%s</b></para>" % texte
                    if dictOptions["style_texte_conclusion"] == 3 : texte = u"<para><i><b>%s</b></i></para>" % texte
                    story.append(Paragraph(texte, paraStyle))
                    
                # Image signature
                if dictOptions["image_signature"] != "" :
                    cheminImage = dictOptions["image_signature"]
                    if os.path.isfile(cheminImage) :
                        img = Image(cheminImage)
                        largeur, hauteur = int(img.drawWidth * 1.0 * dictOptions["taille_image_signature"] / 100.0), int(img.drawHeight * 1.0 * dictOptions["taille_image_signature"] / 100.0)
                        if largeur > CADRE_CONTENU[2] or hauteur > CADRE_CONTENU[3] :
                            raise Exception(_(u"L'image de signature est trop grande. Veuillez diminuer sa taille avec le parametre Taille."))
                        img.drawWidth, img.drawHeight = largeur, hauteur
                        if dictOptions["alignement_image_signature"] == 0 : img.hAlign = "LEFT"
                        if dictOptions["alignement_image_signature"] == 1 : img.hAlign = "CENTER"
                        if dictOptions["alignement_image_signature"] == 2 : img.hAlign = "RIGHT"
                        story.append(Spacer(0,20))
                        story.append(img)
                        


                # Saut de page
                story.append(PageBreak())

        # Finalisation du PDF
##        try :
        doc.build(story)
##        except Exception, err :
##            print "Erreur dans ouverture PDF :", err
##            if "Permission denied" in err :
##                dlg = wx.MessageDialog(None, _(u"Noethys ne peut pas créer le PDF.\n\nVeuillez vérifier qu'un autre PDF n'est pas déjà ouvert en arrière-plan..."), _(u"Erreur d'édition"), wx.OK | wx.ICON_ERROR)
##                dlg.ShowModal()
##                dlg.Destroy()
##                return
        
        # Ouverture du PDF
        if ouverture == True :
            FonctionsPerso.LanceFichierExterne(nomDoc)

def Decimal(texte):
    montant= decimal.Decimal(texte)
    return montant

if __name__ == u"__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()

    dictDonnees = {1: {'{FAMILLE_CP}': u'13001', '{ENFANT_RATTACHE_2_MAIL}': '', '{FAMILLE_SECTEUR}': None, '{ORGANISATEUR_MAIL}': u'matthania@gmail.com', 'texte_conclusion': u'', '{ENFANT_RATTACHE_1_CP}': '', 'num_codeBarre': '0000001', '{FAMILLE_MEMO}': u'', 'qfdates': {}, '{ENFANT_RATTACHE_1_VILLE}': '', '{ENFANT_RATTACHE_2_FAX_PRO}': '', '{NBRE_ENFANTS_RATTACHES}': 2, '{TOTAL_DEDUCTIONS}': u'0.00 \u20ac', 'total': Decimal('1935.80'), 'select': True, '{ENFANT_RATTACHE_1_EMPLOYEUR}': u'', '{ENFANT_RATTACHE_1_VILLE_NAISS}': '', '{ENFANT_RATTACHE_2_EMPLOYEUR}': '', 'prestations_familiales': [], '{DATE_ECHEANCE_COURT}': '14/10/2016', 'IDfamille': 5325, '{ENFANT_RATTACHE_1_TEL_PRO}': '', '{ENFANT_RATTACHE_2_DATE_CREATION}': '', '{ENFANT_RATTACHE_1_SECTEUR}': '', '{ORGANISATEUR_APE}': u'923M', '{DATE_EDITION_COURT}': '14/09/2016', '{ENFANT_RATTACHE_2_CIVILITE_COURT}': '', '{ORGANISATEUR_NOM}': u'MATTHANIA', '{FAMILLE_NOM_CAISSE}': None, '{ENFANT_RATTACHE_2_SECTEUR}': '', '{ENFANT_RATTACHE_2_CP}': '', '{FAMILLE_NOM_ALLOCATAIRE}': '', 'listeDeductions': [], '{ENFANT_RATTACHE_1_CIVILITE_LONG}': u'Fille', '{ENFANT_RATTACHE_1_MEMO}': u'', '{ENFANT_RATTACHE_2_DATE_NAISS}': '06/04/2006', '{IDFAMILLE}': 5325, '{SOLDE}': u'935.80 \u20ac', '{ENFANT_RATTACHE_1_NOM_COMPLET}': u'ABDELBARI Chaimaa', '{ENFANT_RATTACHE_2_PRENOM}': u'Ilan', '{ENFANT_RATTACHE_1_TEL_MOBILE}': '', '{ORGANISATEUR_VILLE}': u'Toulon', '{ENFANT_RATTACHE_1_PROFESSION}': u'', '{ENFANT_RATTACHE_2_NOM_COMPLET}': u'PEREZ Ilan', '{SOLDE_DU}': u'935.80 \u20ac', 'reglements': {13407: {'montant': Decimal('1000.00'), 'emetteur': u'L.C.L.', 'numero': u'0003476', 'payeur': u'ABDELBARI', 'ventilation': Decimal('1000.00'), 'mode': u'Ch\xe8que', 'date': datetime.date(2016, 9, 17)}}, '{FAMILLE_NUM_ALLOCATAIRE}': None, '{ENFANT_RATTACHE_1_SEXE}': 'F', '{TOTAL_PERIODE}': u'1935.80 \u20ac', 'total_reports': Decimal('0.00'), '{NOM_LOT}': '', 'date_echeance': datetime.date(2016, 10, 14), '{ENFANT_RATTACHE_1_NUM_SECU}': u'                     ', '{ENFANT_RATTACHE_1_CIVILITE_COURT}': '', '{ENFANT_RATTACHE_2_CP_NAISS}': '', '{ENFANT_RATTACHE_2_RUE}': '', '{ORGANISATEUR_SITE}': u'www.matthania.org', '{CODEBARRES_NUM_FACTURE}': 'F000001', '{ORGANISATEUR_RUE}': u'480, avenue Saint Claire Deville', '{ENFANT_RATTACHE_1_DATE_NAISS}': '26/07/2004', '{NBRE_CONTACTS_RATTACHES}': 0, 'prelevement': None, '{ENFANT_RATTACHE_1_CATEGORIE_TRAVAIL}': '', 'listePrestations': [(13481, None), (13481, None), (13481, None), (13481, None), (13481, None), (0, 13024), (0, 13024), (0, 13024), (13481, 13019), (13481, 13019), (11317, 13021), (11317, 13021), (11317, 13021), (11317, 13021), (11317, 13021)], '{DATE_ECHEANCE}': '14/10/2016', 'num_facture': 1, '{ENFANT_RATTACHE_2_AGE}': '10 ans', '{NUM_FACTURE}': u'000001', '{ENFANT_RATTACHE_1_FAX_PRO}': '', '{ENFANT_RATTACHE_2_VILLE_NAISS}': '', '{ORGANISATEUR_AGREMENT}': u'032ORG1234', '{ENFANT_RATTACHE_1_AGE}': '12 ans', '{ENFANT_RATTACHE_2_FAX}': '', 'individus': {0: {'nom': u'Prestations familiales', 'texte': u'<b>Prestations familiales</b>', 'total_reports': Decimal('0.00'), 'ventilation': Decimal('0.00'), 'activites': {0: {'presences': {u'2016-09-14': {'total': Decimal('35.00'), 'unites': [{'categorie': u'consommation', 'montant': Decimal('90.00'), 'nomTarif': None, 'deductions': [], 'montant_initial': 85.0, 'date': u'2016-09-14', 'IDprestation': 13024, 'tva': None, 'nomCategorieTarif': None, 'label': u'Cotisation annuelle', 'IDtarif': None, 'montant_ventilation': Decimal('0.00')}, {'categorie': u'consommation', 'montant': Decimal('5.00'), 'nomTarif': None, 'deductions': [], 'montant_initial': 5.0, 'date': u'2016-09-14', 'IDprestation': 13024, 'tva': None, 'nomCategorieTarif': None, 'label': u"R\xe9duction Nbre d'enfant", 'IDtarif': None, 'montant_ventilation': Decimal('0.00')}, {'categorie': u'consommation', 'montant': Decimal('-60.00'), 'nomTarif': None, 'deductions': [], 'montant_initial': -600.0, 'date': u'2016-09-14', 'IDprestation': 13024, 'tva': None, 'nomCategorieTarif': None, 'label': u'R\xe9duction Serviteur de Dieu', 'IDtarif': None, 'montant_ventilation': Decimal('0.00')}], 'texte': '14/09/2016'}}, 'texte': None}}, 'total': Decimal('35.00'), 'select': True}, 13481: {'nom': u'ABDELBARI Chaimaa', 'texte': u'<b>ABDELBARI Chaimaa</b><font size=7>, n\xe9e le 26/07/2004</font>', 'total_reports': Decimal('0.00'), 'ventilation': Decimal('420.00'), 'activites': {234: {'presences': {u'2016-09-14': {'total': Decimal('300.00'), 'unites': [{'categorie': u'consommation', 'montant': Decimal('300.00'), 'nomTarif': u'Formation BAFA', 'deductions': [], 'montant_initial': 300.0, 'date': u'2016-09-14', 'IDprestation': 13019, 'tva': None, 'nomCategorieTarif': u'Tarif Normal', 'label': u'test pasto', 'IDtarif': u'Formation BAFA', 'montant_ventilation': Decimal('420.00')}, {'categorie': u'consommation', 'montant': Decimal('0.00'), 'nomTarif': u'Formation BAFA', 'deductions': [], 'montant_initial': 0.0, 'date': u'2016-09-14', 'IDprestation': 13019, 'tva': None, 'nomCategorieTarif': u'Tarif Normal', 'label': u'message pied en gras', 'IDtarif': u'Formation BAFA', 'montant_ventilation': Decimal('0.00')}], 'texte': '14/09/2016'}}, 'texte': u'86 BAFA APPRO - 2016 - n\xb0 agr\xe9ment : 2016-83-0005'}, 221: {'presences': {u'2016-09-14': {'total': Decimal('800.40'), 'unites': [{'categorie': None, 'montant': Decimal('150.40'), 'nomTarif': u'Camps Corse -Jeunes-TarifNormal', 'deductions': [], 'montant_initial': 150.4, 'date': u'2016-09-14', 'IDprestation': None, 'tva': None, 'nomCategorieTarif': u'Tarif Normal', 'label': u'Deuxi\xe8me article bis', 'IDtarif': u'Camps Corse -Jeunes-TarifNormal', 'montant_ventilation': Decimal('0.00')}, {'categorie': None, 'montant': Decimal('0.00'), 'nomTarif': u'Camps Corse -Jeunes-TarifNormal', 'deductions': [], 'montant_initial': 0.0, 'date': u'2016-09-14', 'IDprestation': None, 'tva': None, 'nomCategorieTarif': u'Tarif Normal', 'label': u'Troisi\xe8me article', 'IDtarif': u'Camps Corse -Jeunes-TarifNormal', 'montant_ventilation': Decimal('0.00')}, {'categorie': None, 'montant': Decimal('480.00'), 'nomTarif': u'Camps Corse -Jeunes-TarifNormal', 'deductions': [], 'montant_initial': 480.0, 'date': u'2016-09-14', 'IDprestation': None, 'tva': None, 'nomCategorieTarif': u'Tarif Normal', 'label': u'S\xe9jour Jeunes Corse S1', 'IDtarif': u'Camps Corse -Jeunes-TarifNormal', 'montant_ventilation': Decimal('0.00')}, {'categorie': None, 'montant': Decimal('160.00'), 'nomTarif': u'Camps Corse -Jeunes-TarifNormal', 'deductions': [], 'montant_initial': 160.0, 'date': u'2016-09-14', 'IDprestation': None, 'tva': None, 'nomCategorieTarif': u'Tarif Normal', 'label': u'Voyage Bateau inclus', 'IDtarif': u'Camps Corse -Jeunes-TarifNormal', 'montant_ventilation': Decimal('0.00')}, {'categorie': None, 'montant': Decimal('10.00'), 'nomTarif': u'Camps Corse -Jeunes-TarifNormal', 'deductions': [], 'montant_initial': 10.0, 'date': u'2016-09-14', 'IDprestation': None, 'tva': None, 'nomCategorieTarif': u'Tarif Normal', 'label': u'Option lunettes de soleil', 'IDtarif': u'Camps Corse -Jeunes-TarifNormal', 'montant_ventilation': Decimal('0.00')}], 'texte': '14/09/2016'}}, 'texte': u'42 SEJOUR CORSE 2 - 2016 - n\xb0 agr\xe9ment : 2016-83-0001'}}, 'total': Decimal('1100.40'), 'select': True}, 11317: {'nom': u'PEREZ Ilan', 'texte': u'<b>PEREZ Ilan</b><font size=7>, n\xe9 le 06/04/2006</font>', 'total_reports': Decimal('0.00'), 'ventilation': Decimal('580.00'), 'activites': {221: {'presences': {u'2016-09-14': {'total': Decimal('800.40'), 'unites': [{'categorie': u'consommation', 'montant': Decimal('150.40'), 'nomTarif': u'Camps Corse -Jeunes-TarifNormal', 'deductions': [], 'montant_initial': 150.4, 'date': u'2016-09-14', 'IDprestation': 13021, 'tva': None, 'nomCategorieTarif': u'Tarif Normal', 'label': u'Deuxi\xe8me article bis', 'IDtarif': u'Camps Corse -Jeunes-TarifNormal', 'montant_ventilation': Decimal('580.00')}, {'categorie': u'consommation', 'montant': Decimal('0.00'), 'nomTarif': u'Camps Corse -Jeunes-TarifNormal', 'deductions': [], 'montant_initial': 0.0, 'date': u'2016-09-14', 'IDprestation': 13021, 'tva': None, 'nomCategorieTarif': u'Tarif Normal', 'label': u'Troisi\xe8me article', 'IDtarif': u'Camps Corse -Jeunes-TarifNormal', 'montant_ventilation': Decimal('0.00')}, {'categorie': u'consommation', 'montant': Decimal('480.00'), 'nomTarif': u'Camps Corse -Jeunes-TarifNormal', 'deductions': [], 'montant_initial': 480.0, 'date': u'2016-09-14', 'IDprestation': 13021, 'tva': None, 'nomCategorieTarif': u'Tarif Normal', 'label': u'S\xe9jour Jeunes Corse S1', 'IDtarif': u'Camps Corse -Jeunes-TarifNormal', 'montant_ventilation': Decimal('0.00')}, {'categorie': u'consommation', 'montant': Decimal('160.00'), 'nomTarif': u'Camps Corse -Jeunes-TarifNormal', 'deductions': [], 'montant_initial': 160.0, 'date': u'2016-09-14', 'IDprestation': 13021, 'tva': None, 'nomCategorieTarif': u'Tarif Normal', 'label': u'Voyage Bateau inclus', 'IDtarif': u'Camps Corse -Jeunes-TarifNormal', 'montant_ventilation': Decimal('0.00')}, {'categorie': u'consommation', 'montant': Decimal('10.00'), 'nomTarif': u'Camps Corse -Jeunes-TarifNormal', 'deductions': [], 'montant_initial': 10.0, 'date': u'2016-09-14', 'IDprestation': 13021, 'tva': None, 'nomCategorieTarif': u'Tarif Normal', 'label': u'Option lunettes de soleil', 'IDtarif': u'Camps Corse -Jeunes-TarifNormal', 'montant_ventilation': Decimal('0.00')}], 'texte': '14/09/2016'}}, 'texte': u'42 SEJOUR CORSE 2 - 2016 - n\xb0 agr\xe9ment : 2016-83-0001'}}, 'total': Decimal('800.40'), 'select': True}}, '{ENFANT_RATTACHE_2_AGE_INT}': 10, '{ENFANT_RATTACHE_1_MAIL}': '', '{ENFANT_RATTACHE_2_NUM_SECU}': u'10604', '{ENFANT_RATTACHE_1_ANNEE_DECES}': '', '{ENFANT_RATTACHE_2_MAIL_PRO}': '', '{ENFANT_RATTACHE_1_TEL_DOMICILE}': '', '{ENFANT_RATTACHE_1_MAIL_PRO}': '', 'solde': Decimal('935.80'), '{ENFANT_RATTACHE_1_NOM}': u'ABDELBARI', '{ORGANISATEUR_TEL}': u'04.94.27.02.77.', '{IDcompte_payeur}': 5325, '{ENFANT_RATTACHE_2_SEXE}': 'M', '{ENFANT_RATTACHE_2_TEL_DOMICILE}': '', 'date_fin': datetime.date(2017, 2, 28), '{TOTAL_REGLE}': u'1000.00 \u20ac', '{DATE_ECHEANCE_LONG}': u'Vendredi 14 octobre 2016', '{NBRE_REPRESENTANTS_RATTACHES}': 0, '{FAMILLE_NOM_REGIME}': None, '{ORGANISATEUR_CP}': u'83000', 'messages_familiaux': [], '{NUMERO_FACTURE}': u'000001', '{ENFANT_RATTACHE_1_FAX}': '', '{ENFANT_RATTACHE_1_LIENS}': '', '{ENFANT_RATTACHE_2_PROFESSION}': '', '{FAMILLE_NOM}': u'ABDELBARI Atika', 'ventilation': Decimal('1000.00'), '{ENFANT_RATTACHE_2_VILLE}': '', 'date_debut': datetime.date(2016, 7, 17), '{ENFANT_RATTACHE_1_AGE_INT}': 12, '{ENFANT_RATTACHE_2_NOM}': u'PEREZ', '{IDallocataire}': None, '{ENFANT_RATTACHE_2_TEL_PRO}': '', '{ENFANT_RATTACHE_2_ANNEE_DECES}': '', '{ENFANT_RATTACHE_1_RUE}': u'', 'date_edition': datetime.date(2016, 9, 14), 'liste_activites': [], 'texte_introduction': u'', '{DATE_EDITION_LONG}': u'Mercredi 14 septembre 2016', '{ORGANISATEUR_SIRET}': u'33215431810023', '{ENFANT_RATTACHE_2_CIVILITE_LONG}': u'Gar\xe7on', '{SOLDE_AVEC_REPORTS}': u'935.80 \u20ac', '{ENFANT_RATTACHE_2_TEL_MOBILE}': '', 'texte_titre': u'Facture', '{SOLDE_AVEC_REPORTS_LETTRES}': u'Deux mille cent quinze euros quatre-vingt centimes', 'numero': u'Facture n\xb00000001', '{ENFANT_RATTACHE_1_TITULAIRE}': u'Non', '{SOLDE_LETTRES}': u'Deux mille cent quinze euros quatre-vingt centimes', '{FAMILLE_VILLE}': u'MARSEILLE', 'nomSansCivilite': u'ABDELBARI Atika', '{FAMILLE_DATE_CREATION}': '30/09/2015', '{DATE_DEBUT}': '14/09/2016', '{ENFANT_RATTACHE_2_LIENS}': '', 'solde_avec_reports': Decimal('935.80'), '{ENFANT_RATTACHE_2_MEMO}': '', '{ENFANT_RATTACHE_1_DATE_CREATION}': '', '{ENFANT_RATTACHE_1_CP_NAISS}': '', '{ENFANT_RATTACHE_2_TITULAIRE}': u'Non', '{TEXTE_ECHEANCE}': u'Ech\xe9ance du r\xe8glement : 14/10/2016', 'reports': {}, '{ENFANT_RATTACHE_2_CATEGORIE_TRAVAIL}': '', '{ENFANT_RATTACHE_1_PRENOM}': u'Chaimaa', '{FAMILLE_RUE}': u'0030\nrue du baignoir\n\n', '{DATE_FIN}': '14/09/2016', '{ORGANISATEUR_FAX}': u'02.98.02.02.02.', '{TOTAL_REPORTS}': u'0.00 \u20ac', '{DATE_EDITION_FACTURE}': '14/09/2016'}}
    dictOptions = {u'texte_conclusion': u'', u'image_signature': u'', u'taille_texte_messages': 7, u'afficher_qf_dates': True, u'affichage_prestations': 0, u'taille_image_signature': 100, u'alignement_image_signature': 0, u'couleur_fond_conclusion': wx.Colour(255, 255, 255, 255), u'alignement_texte_introduction': 0, u'afficher_reglements': True, u'integrer_impayes': False, u'taille_texte_activite': 6, u'afficher_periode': True, u'couleur_fond_introduction': wx.Colour(255, 255, 255, 255), u'taille_texte_titre': 19, u'taille_texte_periode': 8, u'IDmodele': 5, u'couleur_fond_2': wx.Colour(234, 234, 255, 255), u'couleur_fond_1': wx.Colour(204, 204, 255, 255), u'afficher_impayes': True, u'afficher_messages': True, u'couleur_bord_conclusion': wx.Colour(255, 255, 255, 255), u'taille_texte_montants_totaux': 10, u'alignement_texte_conclusion': 0, u'largeur_colonne_montant_tva': 50, u'largeur_colonne_date': 50, u'texte_titre': u'Facture', u'taille_texte_prestation': 7, u'afficher_avis_prelevements': True, u'taille_texte_conclusion': 9, u'affichage_solde': 0, u'afficher_coupon_reponse': True, u'taille_texte_introduction': 9, u'intitules': 0, u'taille_texte_noms_colonnes': 5, u'texte_introduction': u'', u'taille_texte_individu': 9, u'taille_texte_labels_totaux': 9, u'couleur_bord_introduction': wx.Colour(255, 255, 255, 255), u'afficher_codes_barres': True, u'afficher_titre': True, u'largeur_colonne_montant_ht': 50, 'messages': [], u'memoriser_parametres': True, u'largeur_colonne_montant_ttc': 70, u'style_texte_introduction': 0, u'style_texte_conclusion': 0, u'repertoire_copie': u''}
    Impression(dictDonnees, dictOptions,IDmodele=dictOptions["IDmodele"])
