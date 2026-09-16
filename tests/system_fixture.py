"""Portable example assets, also used by integration tests."""
import json
from pathlib import Path


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def record(root, filename, rid, kind, title, body, relations=None, **extra):
    meta = dict(id=rid, kind=kind, title=title, status='current', summary=body.split('\n')[0], **extra)
    if relations:
        meta['relations'] = relations
    path = root / 'records' / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('---\n' + json.dumps(meta, ensure_ascii=False) + '\n---\n\n# ' + title + '\n\n' + body + '\n', encoding='utf-8')


def fixture(base):
    base = Path(base)
    names = {'core': 'Reference Core · 示例', 'board': 'Note Board · 示例', 'graph': 'Graph View · 示例', 'system': '协作系统 · 示例'}
    projects = {}
    for name, title in names.items():
        root = base / name
        project = dict(schema='project-map/v1', project_id='example-' + name, name=title,
                       kind='system' if name == 'system' else 'software', map='map.md', sources=[], bindings=[])
        project['archify'] = {'architecture': {'source': 'diagrams/architecture.json', 'node_records': {}}}
        root.mkdir(parents=True, exist_ok=True)
        text = ('# ' + title + '\n\n演示资料，用于核对系统地图阅读与跨项目查询，不代表实际 DSH 插件的分组。\n\n')
        if name == 'system':
            text += '明确收录 Reference Core、Note Board 和 Graph View。两个消费者共享 Core 的引用接口，Board 与 Graph 也有相互关联。外部宿主只作为依赖，不递归纳入。\n'
        else:
            text += '这是独立项目地图。可直接阅读模块、接口和接入说明，也可以从一个或多个系统入口进入。\n'
        (root / 'map.md').write_text(text, encoding='utf-8')
        projects[name] = project
    def relation(kind, pid, rid, reason=''):
        return {'relation': kind, 'to': {'project_id': 'example-' + pid, 'record_id': rid}, 'reason': reason}
    record(base/'core', 'api/overview.md', 'MOD-api', 'module', '引用 API', '维护引用身份与提交边界。',
           [relation('provides', 'core', 'IF-reference'), relation('provides', 'core', 'IF-submit')])
    record(base/'core', 'api/reference.md', 'IF-reference', 'interface', '引用定位接口', '按稳定引用 ID 查询对象与来源。\n\n约束：不能把本次浏览器端口当作引用身份。', interface_family='lookup')
    record(base/'core', 'api/submit.md', 'IF-submit', 'interface', '上下文提交接口', '提交选定的引用上下文；查询接口与提交接口分别维护。', interface_family='submission')
    for name, other in [('board', 'graph'), ('graph', 'board')]:
        record(base/name, 'viewer/overview.md', 'MOD-view', 'module', '阅读模块', '展示本项目的对象和引用入口。',
               [relation('depends_on', other, 'MOD-view', '显式交叉关系示例，不表示固定执行顺序')])
        record(base/name, 'viewer/core.md', 'INT-reference', 'integration', '接入引用定位', '只在定位来源对象时调用 Core；不代表整个模块依赖全部 Core 接口。',
               [relation('consumes', 'core', 'IF-reference', '按引用 ID 定位来源')])
    record(base/'system', 'scope.md', 'DEC-scope', 'decision', '系统边界与接口归属', '收录三张独立地图；接口定义在 Core，消费者各自维护接入说明。',
           [relation('depends_on', 'host', 'IF-context', '外部宿主未收录，仅保留定位身份')])
    members = [dict(project_id='example-'+name, manifest='../'+name+'/project.yaml', role=role,
                    scope='示例中的明确收录项目', diagram='architecture') for name, role in
               [('core', '提供引用定位与上下文提交接口'), ('board', '以笔记卡片使用引用定位'), ('graph', '以图节点使用引用定位')]]
    projects['system']['system'] = {'members': members}
    projects['system']['archify']['architecture']['node_projects'] = {k:'example-'+k for k in ('core','board','graph')}
    for name, project in projects.items():
        if name == 'system':
            components = [dict(id=k, type='backend', label=names[k].split(' ·')[0], sublabel=role, pos=pos, size=[190,80]) for k, role, pos in
                          [('core','唯一的接口合同',[340,60]),('board','笔记引用',[60,300]),('graph','图节点引用',[620,300])]]
            connections = [dict(id='board-core', **{'from':'board','to':'core'}, label='引用定位', fromSide='top', toSide='left'),
                           dict(id='graph-core', **{'from':'graph','to':'core'}, label='引用定位', fromSide='top', toSide='right'),
                           dict(id='board-graph', **{'from':'board','to':'graph'}, label='相互关联', fromSide='right', toSide='left')]
        else:
            components = [dict(id='module',type='backend',label='引用 API' if name=='core' else '阅读模块',sublabel=names[name],pos=[90,80],size=[260,90])]
            connections = []
            project['archify']['architecture']['node_records'] = {'module': ['MOD-api', 'IF-reference', 'IF-submit'] if name=='core' else ['MOD-view','INT-reference']}
        ir = dict(schema_version=1,diagram_type='architecture',meta=dict(title=names[name],locale='zh-CN'),components=components,connections=connections)
        if name == 'system':
            ir['boundaries'] = [dict(kind='region',label='明确收录的项目',wraps=['core','board','graph'])]
        dump(base/name/'diagrams/architecture.json',ir)
        dump(base/name/'project.yaml',project)
    return base/'system'/'project.yaml'
