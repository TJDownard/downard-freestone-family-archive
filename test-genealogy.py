"""Regression tests for the genealogy build. Run with python3 test-genealogy.py."""
import json
from pathlib import Path
import runpy
import unittest

archive = runpy.run_path(str(Path(__file__).with_name('build-archive.py')))

class GenealogyAudit(unittest.TestCase):
    def setUp(self):
        self.people = archive['people']
        self.rels = archive['relatives']
        self.groups = archive['child_groups']

    def test_tree_and_directory_cover_all_ids(self):
        root = archive['ROOT']
        tree = (root / 'archive-branches.js').read_text().split('const treePeople = ',1)[1].split(';\n',1)[0]
        self.assertEqual(set(json.loads(tree)),set(self.people))
        directory = (root / 'people.html').read_text()
        for key in self.people:
            path = archive['person_path'](key)
            if path.startswith('people.html#'):
                self.assertIn(f'id="{key}"',directory)
            else:
                self.assertTrue((root/path).is_file())
        self.assertFalse(archive['removed_edges'])

    def test_all_edges_display_in_both_directions(self):
        for (a,b,kind), record in archive['edges'].items():
            if record.get('status') == 'Unverified':
                self.assertTrue(any(k == b for k,_ in archive['open_edges'][a]))
                self.assertTrue(any(k == a for k,_ in archive['open_edges'][b]))
            else:
                side_a,side_b = {'Parent':('children','parents'),'Partner':('spouses','spouses'),
                                'Stepchild':('stepchildren','stepparents'),'Twin':('twins','twins')}[kind]
                self.assertIn(b,self.rels[a][side_a])
                self.assertIn(a,self.rels[b][side_b])
        for k, groups in self.groups.items():
            self.assertCountEqual([c for group in groups for c in group['children']],self.rels[k]['children'])
            for group in groups:
                for child in group['children']:
                    self.assertEqual(set(group['coParents']),set(self.rels[child]['parents'])-{k})

    def test_two_marriages_and_stepchildren(self):
        children = {tuple(g['coParents']):set(g['children']) for g in self.groups['george-freestone']}
        self.assertEqual(len(children[('alice-carlisle',)]),4)
        self.assertEqual(len(children[('jennie-lind',)]),11)
        self.assertIn('reuben-freestone',children[('jennie-lind',)])
        self.assertNotIn('reuben-freestone',children[('alice-carlisle',)])
        self.assertEqual(len(self.rels['george-freestone']['stepchildren']),3)
        self.assertNotIn('george-freestone',self.rels['richard-joseph-carlisle']['parents'])
        self.assertEqual(len(self.rels['walter']['stepchildren']),3)
        self.assertEqual(next(s['label'] for s in self.rels['reuben-freestone']['siblings']
                              if s['id']=='alice-jane-freestone'),'Half-sibling')

    def test_peterson_roster_and_privacy(self):
        self.assertEqual(len(self.rels['hilmer']['children']),9)
        self.assertCountEqual(self.rels['judy']['parents'],['tom-freestone','maurine-peterson'])
        self.assertCountEqual(self.rels['norma']['children'],['robert','glen','quinn'])
        self.assertCountEqual(self.rels['thomas']['children'],['robert','glen','quinn'])
        self.assertIn('maxine-peterson',self.rels['maurine-peterson']['twins'])
        self.assertNotIn('birth',self.people['judy'])
        self.assertNotIn('peterson-private-child',(archive['ROOT']/'search.html').read_text())
        self.assertNotIn('Anna Louise',(archive['ROOT']/'archive-branches.js').read_text())

if __name__ == '__main__':
    unittest.main()
