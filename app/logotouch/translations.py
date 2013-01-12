# -*- coding: utf-8 -*-
fr = {
    'help-gesture-toggleperson': u'Basculer l\'affichage du pronom / déterminant / possessif',
    'help-gesture-person': u'Changer le pronom / déterminant / possessif',
    'help-gesture-rotate': u'Afficher le contraire',
    'help-gesture-time': u'Changer le temps, du passé au futur',
    'help-gesture-scale': u'Changer le sens',
    'help-gesture-shake': u'Obtenir un synonyme',
}

def _(text):
    return fr.get(text, text)
