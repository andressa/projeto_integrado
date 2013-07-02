#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from datetime import datetime
from novela.tree import get_dates, camel_case
from novela import config

def get_novelas():
    novelas = []
    for novela_name, novela_dir in config.NOVELAS:
        novelas.append( {'name': novela_name, 'dir': novela_name.lower().replace(" ", "-")} )
    return novelas

def get_novela_dir(novela):
    for novela_name, novela_dir in config.NOVELAS:
        if novela_dir.endswith( novela ): return novela_dir

def index(request):
    return render_to_response('novelas.html',
                            { 'novelas_list': get_novelas(), 'dates_list': get_dates()},
                              context_instance=RequestContext(request)
                              )

def analysis(request, novela, date, atype):
    novela_dir = get_novela_dir(novela)
    analysis_name = '%s/%s-%s-%s.json' % (novela_dir, camel_case(novela).replace("-", ""), date, atype)
    if not os.path.isfile(analysis_name):
        return render_to_response('analysis404.html',
                {'name': analysis_name},
                            context_instance=RequestContext(request)
                            )

    return render_to_response('analysis.html',
                        {'json': open(analysis_name).read()},
                        context_instance=RequestContext(request)
                        )
