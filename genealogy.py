"""Normalize the archive's declared genealogy into a bidirectional view."""
from collections import defaultdict
import re
import unicodedata

FAMILY_BRANCHES = ('Downard', 'Freestone', 'Peterson', 'Lambson')
PARTNER_TYPES = {'Marriage', 'Marriage license reported', 'Partner'}
OPEN_STATUSES = {'Unverified', 'Probable', 'Conflicting'}

def normalize_name(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))

def edge_key(record):
    a, b, kind = record['from'], record['to'], record['type']
    if kind in PARTNER_TYPES | {'Twin'}:
        a, b = sorted((a, b))
    return a, b, 'Partner' if kind in PARTNER_TYPES else kind

def genealogy(people, explicit, sources):
    edges = {}
    def record(edge, strict=False):
        k = edge_key(edge)
        a, b, kind = k
        if a == b or a not in people or b not in people or kind not in {'Parent', 'Stepchild', 'Partner', 'Twin'}:
            raise ValueError(f'Invalid genealogy relationship: {edge}')
        if not edge.get('sources') or set(edge['sources']) - sources.keys():
            raise ValueError(f'Invalid relationship citations: {edge}')
        if strict and k in edges:
            raise ValueError(f'Duplicate explicit genealogy relationship: {k}')
        edges.setdefault(k, edge)
    for edge in explicit:
        record(edge, strict=True)
    for k, person in people.items():
        for parent in person['parents']:
            record({'from':parent,'to':k,'type':'Parent','sources':person['sources'],'status':'Existing archive record'})
        for spouse in person['spouses']:
            a,b=sorted((k,spouse))
            record({'from':a,'to':b,'type':'Partner','sources':person['sources'],'status':'Existing archive record'})
    relatives = {k: {group: [] for group in ('parents','grandparents','spouses','siblings','children','stepchildren','stepparents','twins')} for k in people}
    open_edges = defaultdict(list)
    for (a,b,kind), edge in edges.items():
        if edge.get('status') == 'Unverified':
            open_edges[a].append((b,edge))
            open_edges[b].append((a,edge))
            continue
        group_a, group_b = {'Parent':('children','parents'),'Stepchild':('stepchildren','stepparents'),
                            'Partner':('spouses','spouses'),'Twin':('twins','twins')}[kind]
        relatives[a][group_a].append(b)
        relatives[b][group_b].append(a)
    def name_order(k):
        return normalize_name(people[k]['name']),k
    def ancestor_walk(k, trail):
        if k in trail:
            raise ValueError(f'Parent cycle at {k}')
        for parent in relatives[k]['parents']:
            ancestor_walk(parent, trail | {k})
    groups = {}
    for k, rel in relatives.items():
        ancestor_walk(k,set())
        parents = set(rel['parents'])
        rel['grandparents'] = sorted({grand for p in parents for grand in relatives[p]['parents']} - parents,key=name_order)
        siblings = {s for p in parents for s in relatives[p]['children']} - {k}
        rel['siblings'] = []
        for sib in sorted(siblings,key=name_order):
            other = set(relatives[sib]['parents'])
            relation = ('Full sibling' if len(parents & other) > 1 else
                        'Half-sibling' if parents - other and other - parents else
                        'Sibling · other parent not established')
            rel['siblings'].append({'id':sib,'label':'Twin' if sib in rel['twins'] else relation})
        child_groups = defaultdict(list)
        for child in sorted(rel['children'],key=name_order):
            others = tuple(sorted(set(relatives[child]['parents']) - {k},key=name_order))
            child_groups[others].append(child)
        groups[k] = [{'coParents':others,'children':ids} for others,ids in child_groups.items()]
        for group in rel.keys() - {'siblings'}:
            rel[group].sort(key=name_order)
    return edges, relatives, groups, open_edges

def duplicate_candidates(people):
    by_name=defaultdict(list)
    for k,p in people.items():
        if not p.get('private'):
            by_name[normalize_name(p['name']).strip()].append(k)
    return [ids for ids in by_name.values() if len(ids)>1]
