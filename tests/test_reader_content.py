"""Behavior across nested maps, source bindings and standard/Wiki links."""
from pathlib import Path
from html.parser import HTMLParser
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'maintain-project-map/scripts'))
from project_map import init_project, load_project, normalize_relations
from render_map import export_reader


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links, self.anchors = [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == 'a':
            self.links.append(attributes)
        if 'data-anchor' in attributes:
            self.anchors.append(attributes['data-anchor'])


class ReaderContentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.base = self.root / 'map'
        init_project(self.base, 'Publishing workflow', 'workflow-one', 'workflow')

    def record(self, path, identity, title, body='', **metadata):
        target = self.base / 'records' / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('---\n' + json.dumps({'id': identity, 'kind': 'module', 'title': title, **metadata}, ensure_ascii=False)
                          + '\n---\n' + body, encoding='utf8')
        return target

    def export(self):
        export_reader(load_project(self.base), self.base / 'views/index.html', diagrams=False)
        return json.loads((self.base / 'views/docs.json').read_text(encoding='utf8'))

    def test_recursive_directory_uses_module_titles_and_keeps_source_bindings(self):
        self.record('modules/publisher/overview.md', 'PUB', '发布器')
        self.record('modules/publisher/adapters/storage/overview.md', 'STORE', '存储扩展')
        self.record('modules/publisher/adapters/storage/contract.md', 'WRITE', '写入接口', kind='interface')
        self.record('modules/reviewer/overview.md', 'REVIEW', '人工审核')
        (self.base / 'spec.md').write_text('# 范围\n审核后发布。', encoding='utf8')
        manifest = json.loads((self.base / 'project.yaml').read_text(encoding='utf8'))
        manifest.update(sources=[{'source_id':'spec', 'path':'spec.md'}], bindings=[{'id':'R1', 'kind':'requirement', 'source_id':'spec', 'heading':'范围'}])
        (self.base / 'project.yaml').write_text(json.dumps(manifest), encoding='utf8')
        payload = self.export()
        def walk(nodes, ancestors=()):
            for node in nodes:
                if 'record_id' in node:
                    yield node['record_id'], ancestors
                else:
                    yield from walk(node['children'], (*ancestors, node['title']))
        paths = dict(walk(payload['navigation']))
        self.assertEqual(paths['WRITE'], ('模块', '发布器', '适配接口', '存储扩展'))
        self.assertEqual(paths['REVIEW'], ('模块', '人工审核'))
        self.assertEqual(paths['R1'], ('既有资料',))
        self.assertEqual(set(paths), {'PUB', 'STORE', 'WRITE', 'REVIEW', 'R1'})

    def test_markdown_and_wiki_links_resolve_identity_sections_and_escaped_paths(self):
        self.record('modules/publisher/overview.md', 'PUB', '发布器',
                    '[审核](../reviewer/overview.md#错误处理)\n\n[[WRITE#返回 值|写入结果]]\n\n[有空格](<../reviewer/extra file.md>)\n\n[参考写法][review]\n\n[review]: ../reviewer/overview.md\n\n`[[WRITE]]`\n\n```md\n[[WRITE]]\n```')
        self.record('modules/reviewer/overview.md', 'REVIEW', '人工审核', '# 人工审核\n\n## 错误处理\n保持编辑。')
        self.record('modules/reviewer/extra file.md', 'EXTRA', '更多说明')
        self.record('modules/storage.md', 'WRITE', '写入接口', '# 写入接口\n\n返回 值\n------\n写入身份。', kind='interface')
        payload = self.export()
        records = {r['id']:r for r in payload['records']}
        parser = Links(records['PUB']['body_html'])
        self.assertEqual([a.get('data-map-record') for a in parser.links], ['REVIEW', 'WRITE', 'EXTRA', 'REVIEW'])
        self.assertEqual(parser.links[0]['data-map-anchor'], '错误处理')
        self.assertIn(parser.links[1]['data-map-anchor'], Links(records['WRITE']['body_html']).anchors)
        self.assertIn('<code>[[WRITE]]</code>', records['PUB']['body_html'])

    def test_ambiguous_titles_do_not_choose_an_arbitrary_record(self):
        self.record('home.md', 'HOME', '入口', '[[合同]] [[B|明确合同]] [[writer]]')
        self.record('a.md', 'A', '合同')
        self.record('b.md', 'B', '合同')
        self.record('writer.md', 'W', 'Writer', aliases=['WRITER'])
        body = next(r['body_html'] for r in self.export()['records'] if r['id']=='HOME')
        self.assertEqual([a['data-map-record'] for a in Links(body).links], ['B', 'W'])
        self.assertIn('unresolved-link', body)

    def test_declared_source_opens_readable_snapshot_and_does_not_crawl(self):
        source = self.root / 'contract.ts'
        source.write_text('export interface Sink {\n  put(value: string): string;\n}\n// <script>bad()</script>\n', encoding='utf8')
        self.record('interface.md', 'SINK', '输出接口', '[原始合同](../../contract.ts#L2)\n\n[未声明](../../private.txt)',
                    sources=[{'path':'../contract.ts'}])
        (self.root / 'private.txt').write_text('not included', encoding='utf8')
        payload = self.export()
        documents = payload['linked_documents']
        self.assertEqual(len(documents), 1)
        body = payload['records'][0]['body_html']
        self.assertEqual(Links(body).links[0]['data-map-document'], documents[0]['id'])
        self.assertEqual(Links(body).links[0]['data-map-anchor'], 'L2')
        self.assertIn('L2', Links(documents[0]['body_html']).anchors)
        self.assertNotIn('<script>', documents[0]['body_html'])
        self.assertNotIn('not included', json.dumps(payload))

    def test_source_heading_binding_and_full_source_have_different_destinations(self):
        source = self.base / 'spec.md'
        source.write_text('# 原规格\n\n## 输出\n结果\n\n## 边界\n限制\n', encoding='utf8')
        manifest = json.loads((self.base / 'project.yaml').read_text(encoding='utf8'))
        manifest.update(sources=[{'source_id':'spec', 'path':'spec.md'}], bindings=[{'id':'OUT', 'kind':'requirement', 'source_id':'spec', 'heading':'输出'}])
        (self.base / 'project.yaml').write_text(json.dumps(manifest), encoding='utf8')
        self.record('home.md', 'HOME', '入口', '[输出](../spec.md#输出) [完整](../spec.md#边界)')
        data = load_project(self.base)
        export_reader(data, self.base / 'views/index.html', diagrams=False)
        payload = json.loads((self.base / 'views/docs.json').read_text(encoding='utf8'))
        links = Links(next(r['body_html'] for r in payload['records'] if r['id']=='HOME')).links
        self.assertEqual(links[0]['data-map-record'], 'OUT')
        self.assertIn('data-map-document', links[1])
        self.assertIn('边界', Links(payload['linked_documents'][0]['body_html']).anchors)
        source.write_text('changed after loading', encoding='utf8')
        export_reader(data, self.base / 'views/index.html', diagrams=False)
        payload = json.loads((self.base / 'views/docs.json').read_text(encoding='utf8'))
        self.assertIn('发生变化', payload['linked_documents'][0]['error'])

    def test_relations_merge_known_inverse_forms_not_distinct_roles_or_versions(self):
        def edge(a,b,kind,**extra):
            return {'from':{'record_id':a},'to':{'record_id':b},'relation':kind,**extra}
        rows = [edge('A','B','provides',reason='公开合同'),edge('B','A','provided_by',reason='唯一提供方'),
                edge('C','B','consumes',version='1'),edge('B','C','used_by',version='1'),
                edge('C','B','consumes',version='2'),edge('C','B','related'),
                edge('M','A','contains'),edge('A','M','part_of'),
                {**edge('C','B','consumes',version='1'),'to':{'project_id':'external','record_id':'B'}}]
        result = normalize_relations(rows, 'workflow-one')
        self.assertEqual(len(result), 6)
        self.assertEqual(result[0]['reasons'], ['公开合同','唯一提供方'])
        self.assertEqual(result[1]['declaration_count'], 2)
        self.assertEqual(normalize_relations(result, 'workflow-one'), result)
        self.assertEqual(rows[1]['relation'], 'provided_by')


if __name__ == '__main__':
    unittest.main()
