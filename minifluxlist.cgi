#!/usr/bin/python3

import os
import sys
import cgi
#import cgitb
#cgitb.enable(display=0, logdir="./")
import site
import re
from ownmodule.miniflux import miniflux,ctx_generic


def generer_liste_elem(ctx, tri_cat, cat, groupe_annee):
    with ctx.section:
        ctx.h2.alone(groupe_annee[0] if len(groupe_annee) == 1 else '{0}-{1}'.format(groupe_annee[0], groupe_annee[-1]))
        ctx.a.alone('Marquez comme lu', href='minifluxlist.cgi?action=read&id=%s' % ','.join([x['id'] for y in groupe_annee for x in tri_cat[cat][y]]))
        element_tries = {y['title']: y for x in groupe_annee for y in tri_cat[cat][x]}
        for cle in sorted(element_tries.keys()):
            elem = element_tries[cle]
            with ctx.article(id=elem['id']):
                with ctx.p:
                    ctx.a.alone(elem['title'], href=elem['url'])
                    ctx.text('(%s)' % (elem['Taille'] if 'Taille' in elem else 'Sans'), False)
                    ctx.button.alone('favoris', type='button', onclick='setfavoris(\'%s\')' % (elem['id']))


def generer_fichier_html_newsgroup(host_miniflux):
    mini = miniflux(host_miniflux)
    liste_element = mini.get_item()
    ctx = ctx_generic.ctx_html5('Miniflux Liste', javascript='script.js')

    tri_cat = {'Sans': {'0000': []}}

    for elem in liste_element:
        if elem['status'] != 'unread':
            continue
        if 'Catégorie' in elem:
                m = re.search('\(([0-9]+)\)', elem['title'])
                if m is not None:
                        annee = m.group(1)
                else:
                        annee = 'Sans'
                if elem['Catégorie'] in tri_cat:
                    if annee in tri_cat[elem['Catégorie']]:
                        tri_cat[elem['Catégorie']][annee].append(elem)
                    else:
                        tri_cat[elem['Catégorie']][annee] = [elem]
                else:
                    tri_cat[elem['Catégorie']] = {annee: [elem]}
        else:
                tri_cat['Sans'].append(elem)

    # passs d'optimisation
    cat_moins_5 = []
    for x in tri_cat:
        if type(tri_cat[x]) == dict:
            liste_a_plat = [(tri_cat[x][y], y) for y in tri_cat[x]]
            if sum([len(y[0]) for y in liste_a_plat]) < 5:
                cat_moins_5.append((x, liste_a_plat))

    tri_cat[','.join([x[0] for x in cat_moins_5])] = cat_moins_5
    for x in cat_moins_5:
        del tri_cat[x[0]]

    for cat in sorted(tri_cat.keys()):
        with ctx.section:
            ctx.h2.alone(cat)
            if type(tri_cat[cat]) == dict:
                ctx.a.alone('Marquez comme lu', href='minifluxlist.cgi?action=read&id=%s' % ','.join([x['id'] for y in tri_cat[cat] for x in tri_cat[cat][y]]))
                lnombre = 0
                groupe_annee = []
                for annee in sorted(tri_cat[cat].keys()):
                    lnombre = lnombre + len(tri_cat[cat][annee])
                    groupe_annee.append(annee)
                    if lnombre > 10:
                        generer_liste_elem(ctx, tri_cat, cat, groupe_annee)
                        lnombre = 0
                        groupe_annee = []
                if lnombre > 0:
                    generer_liste_elem(ctx, tri_cat, cat, groupe_annee)
            elif type(tri_cat[cat]) == list:
                ctx.a.alone('Marquez comme lu', href='minifluxlist.cgi?action=read&id=%s' % ','.join([elem['id'] for x in tri_cat[cat] for y in x[1] for elem in y[0]]))
                for x in tri_cat[cat]:
                    with ctx.ul:
                        ctx.h4.alone(x[0])
                        for y in x[1]:
                            for elem in y[0]:
                                with ctx.p:
                                    ctx.a.alone(elem['title'], href=elem['url'])
                                    ctx.text('(%s)' % (elem['Taille'] if 'Taille' in elem else 'Sans'), False)
                                    ctx.button.alone('favoris', type='button', onclick='setfavoris(\'%s\')' % (elem['id']))
    return ctx.close()


form = cgi.FieldStorage()

if 'action' in form.keys():
        mini = miniflux('192.168.0.8')
        mini.set_status_liste(form.getvalue('id').split(','))
buffer = generer_fichier_html_newsgroup('192.168.0.8')
sys.stdout.buffer.write(buffer.encode('utf-8'))

