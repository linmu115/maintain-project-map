import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import map_catalog as catalog
import project_map as pm


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.registry = self.root / 'registry.json'

    def project(self, directory, identity, title='Example'):
        root = self.root / directory
        pm.init_project(root, title, kind='software')
        path = root / 'project.yaml'
        data = pm._mapping(path.read_text(encoding='utf-8'), str(path))
        data['project_id'] = identity
        path.write_text(json.dumps(data), encoding='utf-8')
        return path

    def research(self, directory, title='B题'):
        root = self.root / directory
        root.mkdir()
        (root / 'library').mkdir()
        (root / 'read.md').write_text('research body must not be loaded')
        path = root / '.mrs-project.json'
        path.write_text(json.dumps({'schema': 'mrs-project-navigation/v3', 'title': title,
                                   'formal_library': 'library', 'markdown': {'path': 'read.md'},
                                   'browser': {'status': 'ready', 'path': str(root / 'missing.html')}}), encoding='utf-8')
        return path

    def test_legacy_registration_alias_lookup_and_idempotence(self):
        path = self.project('p', 'one')
        pm.register_project(path, self.registry)
        catalog.register(path, self.registry, aliases=['别名', 'EXAMPLE'])
        previous = self.registry.read_bytes()
        self.assertFalse(catalog.register(path, self.registry, aliases=['别名'])['changed'])
        self.assertEqual(previous, self.registry.read_bytes())
        result = catalog.lookup('别名', self.registry)
        self.assertEqual(result['status'], 'resolved')
        self.assertFalse(result['content_loaded'])
        self.assertEqual(result['results'][0]['project_id'], 'one')
        self.assertEqual(pm.resolve_project('one', self.registry)['status'], 'resolved')

    def test_same_name_is_ambiguous_and_id_has_priority(self):
        for identity in ('one', 'two'):
            catalog.register(self.project(identity, identity), self.registry, aliases=['one'])
        self.assertEqual(catalog.lookup('Example', self.registry)['status'], 'ambiguous')
        self.assertEqual(catalog.lookup('one', self.registry)['results'][0]['project_id'], 'one')
        self.assertEqual(catalog.lookup('absent', self.registry)['status'], 'unresolved')

    @patch.object(pm, '_git_version', return_value={})
    def test_preferred_location_current_override_and_stale_default(self, _git):
        a = self.project('a', 'one')
        b = self.project('b', 'one')
        catalog.register(a, self.registry)
        catalog.register(b, self.registry)
        self.assertEqual(catalog.lookup('one', self.registry)['status'], 'ambiguous')
        catalog.register(a, self.registry, preferred=True)
        self.assertEqual(catalog.lookup('one', self.registry)['results'][0]['manifest_path'], str(a))
        self.assertEqual(pm.resolve_project('one', self.registry, current=self.root)['manifest_path'], str(a))
        self.assertEqual(catalog.lookup('one', self.registry, current=b.parent)['results'][0]['manifest_path'], str(b))
        a.unlink()
        self.assertEqual(catalog.lookup('one', self.registry)['status'], 'unresolved')
        self.assertEqual(pm.resolve_project('one', self.registry, current=self.root)['status'], 'unresolved')

    def test_corrupt_and_mismatched_locations_are_isolated(self):
        a = self.project('a', 'one')
        b = self.project('b', 'one')
        c = self.project('c', 'two')
        for path in (a, b, c):
            catalog.register(path, self.registry)
        a.write_text('broken: [', encoding='utf-8')
        b.write_text(json.dumps({'schema': 'project-map/v1', 'project_id': 'different', 'name': 'X'}))
        result = catalog.lookup(None, self.registry)
        entries = {r['project_id']: r for r in result['results']}
        self.assertEqual(entries['one']['status'], 'unresolved')
        self.assertEqual(entries['two']['status'], 'resolved')

    def test_research_map_is_outside_project_catalog(self):
        a = self.research('research')
        original = a.read_bytes()
        with self.assertRaises(pm.MapError):
            catalog.register(a, self.registry, aliases=['美赛B'])
        self.assertEqual(a.read_bytes(), original)
        self.assertFalse(self.registry.exists())

    def test_pagination_bounds_and_no_payload(self):
        for i in range(3):
            catalog.register(self.project(str(i), str(i), 'Map ' + str(i)), self.registry)
        page = catalog.lookup(None, self.registry, limit=2)
        self.assertEqual(page['next_offset'], 2)
        self.assertEqual(len(catalog.lookup(None, self.registry, limit=2, offset=2)['results']), 1)
        self.assertNotIn('records', json.dumps(page))
        for args in ({'limit': 0}, {'limit': 51}, {'offset': -1}):
            with self.assertRaises(pm.MapError):
                catalog.lookup(None, self.registry, **args)


if __name__ == '__main__':
    unittest.main()
