from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.request import build_opener, ProxyHandler, HTTPRedirectHandler
from urllib.error import HTTPError

SCRIPTS = Path(__file__).resolve().parents[1] / 'maintain-project-map/scripts'
sys.path.insert(0, str(SCRIPTS))
from project_map import load_project, read_record, search_project, register_project
from render_map import export_reader
from serve_map import start_reader, stop_reader
from system_map import compose_system, query_system, module_records, open_project_target
from system_fixture import fixture, record, dump


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


class SystemMapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manifest = fixture(self.root)

    def tearDown(self):
        for entry in self.root.rglob('views/index.html'):
            stop_reader(entry)
        self.temp.cleanup()

    def test_single_contract_cycles_and_explicit_boundary(self):
        view = compose_system(load_project(self.manifest))
        self.assertEqual(view['coverage']['resolved'], 3)
        self.assertEqual(len(view['interfaces']), 2)
        contract = next(r for r in view['interfaces'] if r['id'] == 'IF-reference')
        self.assertEqual(len(contract['consumers']), 2)
        self.assertEqual(len(contract['providers']), 1)
        self.assertNotIn('body', contract)
        self.assertTrue(any(r['to']['project_id'] == 'example-host' and not r['to']['known'] for r in view['relations']))
        cycles = {(r['from']['project_id'],r['to']['project_id']) for r in view['relations'] if r['relation']=='depends_on'}
        self.assertIn(('example-board','example-graph'),cycles)
        self.assertIn(('example-graph','example-board'),cycles)
        second = self.root/'system-two'
        shutil.copytree(self.root/'system',second)
        cfg=json.loads((second/'project.yaml').read_text(encoding='utf-8'));cfg['project_id']='second-system';dump(second/'project.yaml',cfg)
        other=compose_system(load_project(second))
        self.assertEqual(contract['source_sha256'],other['interfaces'][0]['source_sha256'])

    def test_bounded_query_and_unknown_scope(self):
        result=query_system(load_project(self.manifest),'interfaces',limit=1)
        self.assertTrue(result['truncated'])
        self.assertEqual(result['next_offset'],1)
        self.assertEqual(len(result['results'][0]['consumers']),1)
        self.assertTrue(result['results'][0]['consumers_truncated'])
        reverse=query_system(load_project(self.manifest),'impact',project='example-core',record='IF-reference',limit=2)
        self.assertEqual(reverse['total'],3)
        self.assertTrue(reverse['truncated'])

    def test_no_recursive_members_and_missing_diagram(self):
        cfg=json.loads((self.root/'board/project.yaml').read_text(encoding='utf-8'))
        cfg.update(kind='system',system={'members':[{'project_id':'not-read','manifest':'missing/project.yaml'}]})
        dump(self.root/'board/project.yaml',cfg)
        view=compose_system(load_project(self.manifest))
        self.assertEqual(view['coverage']['declared'],3)
        self.assertNotIn('not-read',[m['project_id'] for m in view['members']])
        (self.root/'core/diagrams/architecture.json').unlink()
        view=compose_system(load_project(self.manifest))
        self.assertEqual(view['members'][0]['open_status'],'missing_diagram')
        self.assertEqual(len(view['interfaces']),2)

    def test_worktree_ambiguity_never_guesses(self):
        registry=self.root/'registry.json'
        shutil.copytree(self.root/'core',self.root/'core-copy')
        for name in ('core','core-copy'):register_project(self.root/name,registry)
        cfg=json.loads(self.manifest.read_text(encoding='utf-8'))
        del cfg['system']['members'][0]['manifest'];dump(self.manifest,cfg)
        member=compose_system(load_project(self.manifest),registry)['members'][0]
        self.assertEqual(member['status'],'ambiguous')
        self.assertNotIn('href',member)

    def test_module_scope_and_record_continuation(self):
        doc=load_project(self.root/'core')
        self.assertEqual(len(module_records(doc,'MOD-api')[0]),3)
        self.assertEqual(search_project(doc,'接口',module='MOD-api')['total'],2)
        first=read_record(doc,'IF-reference',max_chars=8)
        record(self.root/'core','unrelated.md','OTHER','note','无关说明','其它更新')
        changed=load_project(self.root/'core')
        read_record(changed,'IF-reference',offset=first['end_offset'],expected_record_fingerprint=first['record_fingerprint'])
        path=self.root/'core/records/api/reference.md';path.write_text(path.read_text(encoding='utf-8')+'\n接口已变更',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Record or its source changed'):
            read_record(load_project(self.root/'core'),'IF-reference',expected_record_fingerprint=first['record_fingerprint'])

    def test_native_passport_and_real_project_redirect(self):
        entry=self.root/'system/views/index.html'
        result=export_reader(load_project(self.manifest),entry)
        self.assertEqual(set(result['diagrams']),{'architecture'})
        self.assertTrue(result['diagrams']['architecture']['file'],result)
        payload=json.loads(entry.with_name('docs.json').read_text(encoding='utf-8'))
        self.assertEqual(len(payload['records']),1)
        adapted=entry.with_name('architecture.html').read_text(encoding='utf-8')
        self.assertIn('map-enter-project',adapted)
        self.assertIn('example-core',adapted)
        url=start_reader(entry)['url']
        opener=build_opener(ProxyHandler({}),NoRedirect())
        with self.assertRaises(HTTPError) as response:
            opener.open(url+'__project?project=example-core&diagram=architecture&node=module',timeout=45)
        self.assertEqual(response.exception.code,302)
        target=response.exception.headers['Location']
        self.assertIn('panel=architecture',target);self.assertIn('node=module',target)
        with build_opener(ProxyHandler({})).open(target,timeout=5) as page:
            self.assertIn('Reference Core',page.read().decode())
        for query in ('project=example-host','project=example-core&node=gone','project=example-core&path=private.txt'):
            with self.assertRaises(HTTPError) as bad:
                opener.open(url+'__project?'+query,timeout=5)
            self.assertEqual(bad.exception.code,409)
        self.assertEqual(json.loads(entry.with_name('docs.json').read_text(encoding='utf-8'))['project']['project_id'],'example-system')

    def test_cli_help_and_module_search(self):
        command=[sys.executable,'-X','utf8',str(SCRIPTS/'project_map.py')]
        help_=subprocess.run(command+['--help'],creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),capture_output=True,text=True,encoding='utf-8',check=True).stdout
        for word in ('members','interfaces','impact','modules'):self.assertIn(word,help_)
        out=subprocess.run(command+['search',str(self.root/'core'),'接口','--module','MOD-api','--limit','1'],creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),capture_output=True,text=True,encoding='utf-8',check=True).stdout
        self.assertTrue(json.loads(out)['truncated'])

    def test_passport_project_action_and_blocked_feedback(self):
        result = subprocess.run(['node', str(Path(__file__).with_name('passport-project.cjs'))],
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__=='__main__':unittest.main()
