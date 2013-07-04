# Create your views here.
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect

import re
import json
import copy
import datetime

from cc_mining.models import *
from novela.views import get_novelas, get_dates

def index(request):
    return render_to_response('index.html',
                            { 'novelas_list': get_novelas(), 'dates_list': get_dates()},
                              context_instance=RequestContext(request)
                              )

@csrf_protect
def Jornalismo(request):
    result = {"JN": "", "Bom Dia Brasil": "", "Jornal Hoje": ""}
    since = datetime.datetime.strptime(request.POST['date'], '%d/%m/%Y')
    until = since + datetime.timedelta(days=1)
    closed_captions = CC.objects.filter(tvshow__pid__name='JN', tvshow__date__lte=until, tvshow__date__gte=since)
    for cc in closed_captions:
        try:
            result["JN"] += cc.text.split(": ")[1]
        except IndexError:
            result["JN"] += cc.text

    closed_captions = CC.objects.filter(tvshow__pid__name='Bom Dia Brasil')
    for cc in closed_captions:
        try:
            result["Bom Dia Brasil"] += cc.text.split(": ")[1]
        except IndexError:
            result["Bom Dia Brasil"] += cc.text

    closed_captions = CC.objects.filter(tvshow__pid__name='Jornal Hoje')
    for cc in closed_captions:
        try:
            result["Jornal Hoje"] += cc.text.split(": ")[1]
        except IndexError:
            result["Jornal Hoje"] += cc.text
    return HttpResponse(json.dumps(result))

#http://esportes.terra.com.br/futebol/copa-das-confederacoes/de-neymar-a-balotelli-veja-todos-os-convocados-das-confederacoes,1a1fcbf274e1f310VgnVCM3000009acceb0aRCRD.html

players = {
        'brasil': {
            'players': {
                'JULIO CESAR': {
                    'setor': 'defesa'
                    },
                'DANIEL ALVES': {
                    'setor': 'neutro'
                    },
                'THIAGO SILVA': {
                    'setor': 'defesa'
                    },
                'DAVID LUIZ': {
                    'setor': 'defesa'
                    },
                'MARCELO' : {
                    'setor': 'neutro'
                    },
                'DANTE': {
                    'setor': 'defesa'
                    },
                'JEAN': {
                    'setor': 'neutro'
                    },
                'HERNANES': {
                    'setor': 'neutro'
                    },
                'LUIZ GUSTAVO': {
                    'setor': 'neutro'
                    },
                'PAULINHO': {
                    'setor': 'neutro'
                    },
                'OSCAR': {
                    'setor': 'ataque'
                    },
                'FRED': {
                    'setor': 'ataque'
                    },
                'NEYMAR': {
                    'setor': 'ataque'
                    },
                'HULK': {
                    'setor': 'ataque'
                    },
                'BERNARD': {
                    'setor': 'ataque'
                    },
                'JO': {
                    'setor': 'ataque'
                    }
                }
            },
        'italia': {
            'players': {
                'BUFFON': {
                    'setor': 'defesa'
                    },
                'MAGGIO': {
                    'setor': 'defesa'
                    },
                'CHIELLINI': {
                    'setor': 'defesa'
                    },
                'ASTORI': {
                    'setor': 'defesa'
                    },
                'DE SCIGLIO': {
                    'setor': 'defesa'
                    },
                'BARZAGLI': {
                    'setor': 'defesa'
                    },
                'BONUCCI': {
                    'setor': 'defesa'
                    },
                'ABATE': {
                    'setor': 'defesa'
                    },
                'CANDREVA': {
                    'setor': 'neutro'
                    },
                'AQUILANI': {
                    'setor': 'neutro'
                    },
                'MARCHISIO': {
                    'setor': 'neutro'
                    },
                'DE ROSSI': {
                    'setor': 'neutro'
                    },
                'MONTOLIVO': {
                    'setor': 'neutro'
                    },
                'PIRLO': {
                    'setor': 'neutro'
                    },
                'GIACCHERINI': {
                    'setor': 'neutro'
                    },
                'DIAMANTI': {
                    'setor': 'neutro'
                    },
                'BALOTELLI': {
                    'setor': 'ataque'
                    },
                'GIOVINCO': {
                    'setor': 'ataque'
                    },
                'GILARDINO': {
                    'setor': 'ataque'
                    },
                'EL SHAARAWY': {
                    'setor': 'ataque'
                    },
                'CERCI': {
                    'setor': 'ataque'
                    }
                }
            }
        }

def filter_cc(cc, fteam, steam):
    players_list = players[fteam]['players'].keys() + players[steam]['players'].keys()
    return " ".join([w for w in cc.split(" ") if w.upper() in players_list])

@csrf_protect
def Copa(request):
    # Copy dict
    result = copy.deepcopy(players)
    # Teams playing the match
    jogo = request.POST['match']
    jogoc = jogo.lower().replace(' ', '')
    fteam = jogoc.split('x')[0]
    steam = jogoc.split('x')[1]
    # Initialize stat
    for t in [fteam, steam]:
        for p in ['ataque', 'defesa', 'neutro']:
            result[t][p] = 0
    # Get CC correspondent to the match and filter
    closed_captions = "".join([cc.text for cc in CC.objects.filter(tvshow__pid__name=jogo)])
    final_cc = filter_cc(closed_captions, fteam, steam)
    # Count players
    for t in [fteam, steam]:
        for p in result[t]['players']:
            n = len(re.findall(p, final_cc))
            setor = result[t]['players'][p]['setor']
            result[t]['players'][p]['count'] = n
            result[t][setor] += n
    return HttpResponse(json.dumps(result))

