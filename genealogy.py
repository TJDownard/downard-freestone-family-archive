"""Normalize the archive's declared genealogy into a bidirectional view."""
from collections import defaultdict
from datetime import datetime
import re
import unicodedata

FAMILY_BRANCHES = ('Downard', 'Freestone', 'Peterson', 'Lambson')
PARTNER_TYPES = {'Marriage', 'Marriage license reported', 'Partner'}
OPEN_STATUSES = {'Unverified', 'Probable', 'Conflicting'}
# The owner supplied this birth sequence; living birth dates remain unpublished.
OWNER_SIBLING_ORDER = ('robert-todd', 'julie-maurine', 'kimberly-jo', 'stacie-lynn', 'thomas-john-child')

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
    def birth_order(k):
        person = people[k]
        birth = person.get('birth', '').split(' · ')[0]
        year = re.search(r'\b(\d{4})\b', birth)
        if not year:
            year = re.match(r'^(?:c\.\s*|about\s+|before\s+|after\s+|Born\s+)?(\d{4})', person['dates'])
        if not year:
            return (9999, 0, 0, *name_order(k))
        month, day = 0, 0
        for pattern in ('%B %d, %Y', '%Y-%m-%d'):
            try:
                parsed = datetime.strptime(birth, pattern)
                month, day = parsed.month, parsed.day
                break
            except ValueError:
                pass
        return (int(year[1]), month, day, *name_order(k))
    def family_order(keys):
        if keys and set(keys).issubset(OWNER_SIBLING_ORDER):
            return sorted(keys, key=OWNER_SIBLING_ORDER.index)
        return sorted(keys, key=birth_order)
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
        for sib in family_order(siblings):
            other = set(relatives[sib]['parents'])
            relation = ('Full sibling' if len(parents & other) > 1 else
                        'Half-sibling' if parents - other and other - parents else
                        'Sibling · other parent not established')
            rel['siblings'].append({'id':sib,'label':'Twin' if sib in rel['twins'] else relation})
        child_groups = defaultdict(list)
        for child in family_order(rel['children']):
            others = tuple(sorted(set(relatives[child]['parents']) - {k},key=name_order))
            child_groups[others].append(child)
        groups[k] = [{'coParents':others,'children':ids} for others,ids in child_groups.items()]
        for group in rel.keys() - {'siblings'}:
            rel[group] = family_order(rel[group]) if group in {'children', 'stepchildren'} else sorted(rel[group], key=name_order)
    return edges, relatives, groups, open_edges

def duplicate_candidates(people):
    by_name=defaultdict(list)
    for k,p in people.items():
        if not p.get('private'):
            by_name[normalize_name(p['name']).strip()].append(k)
    return [ids for ids in by_name.values() if len(ids)>1]
