#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

BUGS
o ccdb.py nao salva o range completo

TODO
Carregar ultima arvore
Nos nodes, criar atributo group
Translator

'''
import novela.config as config
import sys
import os.path
import glob
import logging
import pprint
import sqlite3
import json
import re
import networkx as nx
from collections import Counter
from cc_mining.models import TVShow, CC, Programa, Tree as TreeModel, Analysis

def camel_case(s):
    return "".join(s.title().split())

def get_novela_filename(novela_dir, novela_name, novela_date, extension, add=''):
    if add: add = '-%s' % add
    return '%s/%s-%s%s.%s' % ( novela_dir, camel_case(novela_name), novela_date, add, extension)

class CCParser(object):

    def _get_json_format(self):
        return {
        'action': '',
        'speaker': '',
        'text': '',
        'timestamp': ''
        }


    def parse(self, cc):
        '''
        Por amostragem, vi que o padrão não é respeitado.
        A regexp vislumbra CC com ou sem >> no início, com
        ou sem [] para identificar o speaker e com ou sem :
        separando speaker de texto
        '''

        # Get default format
        data = self._get_json_format()

        # Match action, i.e, [APLAUSOS]
        action = re.search(r'^\[(.*)\]$', cc)
        if action:
            data['action'] = action.group(1)
            return data

        # Match CC rule with speaker
        results = re.search(r'(>+ )\[?([a-zA-Z ]+)\]?: (.*)|(\[)([a-zA-Z ]+)\]:? (.*)', cc)

        # If it's not only text, fill speaker also
        if results:
            # Always the last 2
            data['speaker'], data['text'] = filter(None, results.groups())[1:]
        # If it's only text, filter >> in the begin
        else:
            data['text'] = re.search(r'^(>+)? ?(.*)', cc).group(2)

        return data

class Novela(object):

    def __init__(self, name, date, directory):
        super(Novela, self).__init__()
        self.name, self.date, self.dir = name, date, directory
        self.ccs = []
        self.get_id()
        if self.id is not None:
            self.ccs = self.get_cc()

    def get_id(self):
        try:
            tid = TVShow.objects.get(pid__name=self.name, date=self.date).id
        except TVShow.DoesNotExist:
            tid = None
        self.id = tid

    def get_cc(self):
        return [CCObj(c.text) for c in CC.objects.filter(tvshow__id=self.id)]

class CCObj(object):

    def __init__(self, cc):
        c = CCParser()
        self.ccp = c.parse(cc)

    def __getattr__(self, name):
        return self.ccp[name]

class Tree(object):

    def __init__(self, showid, analysis_id, logger):
        self.logger = logger
        self.tvshow, self.analysis_id = showid, analysis_id
        self.amodel = Analysis.objects.get(id=self.analysis_id)
        self.groups = [0]
        self.json = {}
        self.load_last_tree()
        if not self.json.has_key('nodes'):
            self.json['nodes'] = {}
        if not self.json.has_key('edges'):
            self.json['edges'] = {}
        self.nodes = self.json['nodes']
        self.edges = self.json['edges']
        self.logger.debug("JSON inicial:\n%s" % str(self.json) )

    def load_last_tree(self):

        self.logger.debug("Recuperando ultima arvore")
        try:
            t = TVShow.objects.get(id=self.tvshow)
            a = Analysis.objects.filter(id__lt=self.amodel.id, tvshow__pid=t.pid)
            self.logger.debug(a.query)
            a = a.latest('id')
        except Analysis.DoesNotExist:
            self.logger.debug("Nao existem outras analises")
            return
        try:
            json = TreeModel.objects.get(aid=a.id).json
        except TreeModel.DoesNotExist:
            json = {}
        self.json = json

    def add_node(self, node):
        if self.nodes.has_key(node): return
        self.nodes[node] = {}
        #new_group = self.groups[-1] + 1
        #self.nodes[node] = { 'group': new_group }
        #self.logger.debug("Added node %s with group %d" % (node, new_group))
        #self.groups.append(new_group)

    def add_edge(self, first, second, n):
        if not self.edges.has_key(first):
            self.logger.debug("Arvore nao contem %s" % first)
            self.edges[first] = {}
        old_value = 0
        self.logger.debug("Pesquisando relacionamento entre %s e %s..." % (first, second))
        self.logger.debug("O %s tem os seguintes relacionamentos: %s" % (first, str(self.edges[first])))
        if self.edges[first].has_key(second):
            old_value = self.edges[first][second]['n']
            self.logger.debug("Incrementando relacionamento entre %s e %s: de %d para %d" % (first, second, old_value, n+old_value))
        self.edges[first][second] = {'n': n + old_value}
        #self.logger.debug("# CLUSTER #")
        #self.nodes[second]['group'] = self.nodes[first]['group']

    def save(self):
        a, acreated = Analysis.objects.get_or_create(tvshow=self.tvshow)
        t, created = TreeModel.objects.get_or_create(aid=a)
        t.json = self.json
        t.save()

class Matrix(object):

    def __init__(self, treeobj, speakers, logger):
        self.logger = logger
        self.treeobj, self.speakers = treeobj, speakers
        self.create()

    def create(self):
        # Graph creation
        G = nx.Graph()
        # Nodes
        for n in self.treeobj.nodes: G.add_node(n)
        # Edges
        for e in self.treeobj.edges:
            for i in self.treeobj.edges[e].keys():
                G.add_edge(e, i, weight=self.treeobj.edges[e][i]['n'])
        self.graph = G
        self.save()
        # Clustering
        relations = nx.connected_components(G)
        self.logger.debug("Clusterizacao:\n%s" % str(relations))
        # Update JSON with clustering info
        for n in self.json['nodes']:
            for i, a in enumerate(relations):
                if n in a:
                    self.logger.debug("Node %s go to group #%d" % (n, i))
                    self.json['nodes'][n]['group'] = i
        self.process()

    def save(self):
        # Saida do grafo para formato JSON
        novela = {}
        novela['nodes'] = {}
        nodes = self.graph.nodes()
        for node in nodes:
            novela['nodes'][node] = {}
        novela['links'] = []
        for p_1, p_2, data in self.graph.edges_iter(data=True):
            if data['weight'] == 1:
                continue
            i_1 = nodes.index(p_1)
            i_2 = nodes.index(p_2)
            novela['links'].append({'source': i_1, 'target': i_2, 'value': data['weight']})
        self.json = novela

    def process(self):
        novela = {}
        novela['nodes'] = []
        for n in self.json['nodes']:
            novela['nodes'].append({'name': n, 'group': self.json['nodes'][n]['group']})
        novela['links'] = self.json['links']
        self.json = novela

class NovelaAnalysis(object):

    def __init__(self, novela_obj, logger):
        self.logger = logger
        self.novela = novela_obj
        self.load_analysis()
        self.speakers = []
        self.load_speakers()
        self.counter = Counter()
        self.tree = Tree(self.novela.id, self.id, self.logger)
        self.load_tree()
        self.matrix = Matrix(self.tree, self.speakers, self.logger)

    def load_analysis(self):
        t = TVShow.objects.get(id=self.novela.id)
        a, created = Analysis.objects.get_or_create(tvshow=t)
        self.id = a.id

    def load_speakers(self):
        # Iterate over CCs
        for cc in self.novela.ccs:
            # Save speaker
            if cc.speaker:
                self.speakers.append(cc.speaker)
            # Log
            if ( ('[' in cc.text or ']' in cc.text or ':' in cc.text) and (not cc.speaker and not cc.action) ):
                self.logger.warning('''
                CC: %s
                Parsed: %s''' % (cc.text.encode('latin1'), str(cc.ccp)))

    def load_tree(self):
        # Iterate over speakers to count their relations
        for begin in range(2):
            speakers_list = self.speakers[begin:]
            for i, s in enumerate(speakers_list):
                if i == len(speakers_list) - 1: continue
                self.counter[ tuple(sorted((speakers_list[i], speakers_list[i+1]))) ] += 1
                # Update JSON
                if begin == 0:
                    self.tree.add_node(s.encode('latin1').upper())
        for rel, n in self.counter.items():
            per1, per2 = rel
            per1, per2 = per1.encode('latin1').upper(), per2.encode('latin1').upper()
            if n <= 2 or (per1 == per2): continue
            self.tree.add_edge(per1, per2, n)
        self.tree.save()

    def save(self):
        f = open(get_novela_filename(self.novela.dir, self.novela.name, self.novela.date, 'json', add='tree'), 'w')
        f.write(json.dumps(self.tree.json))
        f.close()
        f = open(get_novela_filename(self.novela.dir, self.novela.name, self.novela.date, 'json', add='matrix'), 'w')
        f.write(json.dumps(self.matrix.json, separators=(',', ':')))
        f.close()

def get_dates():
    return ['2013-06-18', '2013-06-19', '2013-06-20', '2013-06-21', '2013-06-22', '2013-06-24']

def analysis_exists(novela_name, novela_date, novela_dir):
    logfile = get_novela_filename(novela_dir, novela_name, novela_date, 'log')
    print 'Verificando se existe o log: %s' % logfile
    return os.path.isfile(logfile)

def main():

    logger = logging.getLogger('MyLogger')
    logger.setLevel(logging.DEBUG)
    log_handler = None

    for novela_date in get_dates():

        print
        print 'Dia %s' % novela_date

        for novela_name, novela_dir in config.NOVELAS:

            print 'Novela: %s' % novela_name

            # Load novela
            novela = Novela(novela_name, novela_date, novela_dir)
            if novela.id is None:
                print 'Novela nao encontrada'
            else:
                print 'Novela com id %d encontrada' % novela.id

            if analysis_exists(novela_name, novela_date, novela_dir):
                print 'Ignorando: as analises ja foram feitas'
                continue

            if len(novela.ccs) == 0:
                print 'Ignorando: nao existe Closed Caption para ser analisada'
                continue

            sys.stdout.write('Analisando...')

            # Log

            formatter = logging.Formatter('%(levelname)s: %(message)s')

            if log_handler is not None:
                log_handler.close()
                logger.removeHandler(log_handler)

            filename=get_novela_filename(novela_dir, novela_name, novela_date, 'log')
            log_handler=logging.FileHandler(filename,'w')
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)

            # Load NovelaAnalysis object
            a = NovelaAnalysis(novela, logger)
            a.save()

            # Log
            #logger.info('Quantidade de linhas de CC: %d' % len(novela.ccs))
            #logger.info('Speakers list:\n%s' % pprint.pformat(a.speakers))
            logger.info('Relations:\n%s' % pprint.pformat(a.counter))
            logger.info('Arvore:\n%s' % pprint.pformat(a.tree.json, width=10))

            sys.stdout.write('Feito!\n')

def clean():

    print
    for novela_name, novela_dir in config.NOVELAS:
        files = glob.glob("%s/*" % novela_dir)
        print 'Cleaning %s' % novela_dir
        for f in files:
            print 'rm %s' % f
            os.remove(f)
        print
