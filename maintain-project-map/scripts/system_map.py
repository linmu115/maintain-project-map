"""Explicit, one-hop system composition. Records and contracts stay with owners."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode


def is_system(doc):
    return doc['project'].get('kind') == 'system'


def validate_system(doc):
    if not is_system(doc):
        return []
    errors = []
    config = doc['project'].get('system', {})
    if not isinstance(config, dict) or not isinstance(config.get('members', []), list):
        return [{'code': 'system_members_invalid', 'message': 'system.members must be a list'}]
    seen = set()
    for member in config.get('members', []):
        pid = member.get('project_id') if isinstance(member, dict) else None
        if not isinstance(pid, str) or not pid.strip() or pid in seen or pid == doc['project']['project_id']:
            errors.append({'code': 'system_member_identity', 'message': 'Members need unique, non-self project IDs'})
        if isinstance(pid, str):
            seen.add(pid)
        if isinstance(member, dict) and member.get('diagram', 'architecture') not in {'architecture', 'workflow'}:
            errors.append({'code': 'system_member_diagram', 'message': 'Member diagram must be architecture or workflow'})
        if isinstance(member, dict):
            for key in ('name', 'role', 'scope', 'manifest', 'node'):
                if key in member and not isinstance(member[key], str):
                    errors.append({'code': 'system_member_field', 'message': f'Member {key} must be a string'})
    diagrams = doc['project'].get('archify') or {}
    if not isinstance(diagrams, dict):
        return errors + [{'code': 'system_archify_invalid', 'message': 'archify must be an object'}]
    if 'workflow' in diagrams:
        errors.append({'code': 'system_workflow', 'message': 'System maps declare only architecture; workflows belong to project maps'})
    for kind, declaration in diagrams.items():
        targets = declaration.get('node_projects', {}) if isinstance(declaration, dict) else {}
        if not isinstance(targets, dict):
            errors.append({'code': 'system_node_projects', 'message': 'node_projects must map node IDs to project IDs'})
            continue
        source = doc.get('diagram_sources', {}).get(kind, {}).get('ir') or {}
        nodes = source.get('components' if kind == 'architecture' else 'nodes', [])
        ids = {n.get('id') for n in nodes if isinstance(n, dict) and isinstance(n.get('id'), str)} if isinstance(nodes, list) else set()
        for node, pid in targets.items():
            if not isinstance(pid, str) or pid not in seen or node not in ids:
                errors.append({'code': 'system_node_target', 'message': f'Unknown member or native node: {node}'})
    return errors


def _short(record, pid):
    summary = str(record.get('summary', ''))
    return {'project_id': pid, **{k: record.get(k) for k in ('id', 'title', 'kind', 'status', 'path', 'line', 'source_sha256', 'module_id', 'interface_family')},
            'summary': summary[:320], 'summary_truncated': len(summary) > 320, 'body_opened': False}


def _member_doc(doc, member, registry=None):
    from project_map import load_project, resolve_project
    explicit = member.get('manifest')
    if explicit:
        explicit = Path(doc['manifest_path']).parent / explicit
    resolved = resolve_project(member['project_id'], registry, manifest=explicit, current=Path(doc['manifest_path']).parent)
    if resolved['status'] != 'resolved':
        return resolved, None
    child = load_project(resolved['manifest_path'])
    if not child['validation']['valid']:
        return {'status': 'invalid', 'reason': '目标地图存在结构错误', 'errors': child['validation']['errors']}, None
    return resolved, child


def project_href(pid, *, diagram='architecture', record=None, node=None):
    args = {'project': pid, 'diagram': diagram}
    if record:
        args['record'] = record
    if node:
        args['node'] = node
    return '__project?' + urlencode(args)


def compose_system(doc, registry=None):
    """Resolve only explicitly listed maps; no recursive member expansion or bodies."""
    from project_map import normalize_relations
    errors = validate_system(doc)
    if errors:
        raise ValueError('; '.join(e['message'] for e in errors))
    members, records, relations, fingerprints = [], {}, list(doc.get('relations', [])), {}
    documents = [(doc['project']['project_id'], doc)]
    def record_href(pid, rid):
        if pid == doc['project']['project_id']:
            return '#' + urlencode({'mode': 'b', 'record': rid, 'angle': 'explain'})
        return project_href(pid, diagram='spec', record=rid)
    for definition in doc['project'].get('system', {}).get('members', []):
        pid = definition['project_id']
        member = {'project_id': pid, 'name': definition.get('name', pid), 'role': definition.get('role', ''),
                  'scope': definition.get('scope', 'included'), 'diagram': definition.get('diagram', 'architecture'),
                  'node': definition.get('node'), 'status': 'unresolved'}
        try:
            resolved, child = _member_doc(doc, definition, registry)
            member['status'] = resolved['status']
            if child is not None:
                member.update(name=child['project']['name'], manifest_path=child['manifest_path'],
                              fingerprint=child['fingerprint'], version=child['version'])
                graph = child.get('diagram_sources', {}).get(member['diagram'], {})
                nodes = (graph.get('ir') or {}).get('components' if member['diagram'] == 'architecture' else 'nodes', [])
                if not graph.get('ir') or graph.get('errors') or (member['node'] and member['node'] not in {n.get('id') for n in nodes}):
                    member['open_status'] = 'missing_diagram'
                    member['reason'] = '目标图或定位节点不可用；接口记录仍可查询'
                else:
                    member['open_status'] = 'ready'
                    member['href'] = project_href(pid, diagram=member['diagram'], node=member['node'])
                documents.append((pid, child))
                fingerprints[pid] = child['fingerprint']
            else:
                member['reason'] = resolved.get('reason', '目标地图不可用')
                member['locations'] = resolved.get('locations', [])
        except (OSError, ValueError) as exc:
            member.update(status='unavailable', reason=str(exc))
        members.append(member)
    for pid, child in documents:
        for record in child['records']:
            records[(pid, record['id'])] = record
        if child is not doc:
            relations.extend(child.get('relations', []))
    relations = normalize_relations(relations, doc['project']['project_id'])
    interfaces = []
    for (pid, rid), record in records.items():
        if record['kind'] != 'interface':
            continue
        interface = _short(record, pid)
        interface.update(providers=[], consumers=[], href=record_href(pid, rid))
        for rel in relations:
            if rel['to'].get('project_id') == pid and rel['to'].get('record_id') == rid and rel['relation'] in {'provides', 'consumes'}:
                origin = rel['from']
                owned = records.get((origin.get('project_id'), origin.get('record_id')))
                entry = {**origin, 'title': owned['title'] if owned else origin.get('record_id', origin.get('project_id')),
                         'known': owned is not None, 'reason': str(rel.get('reason', ''))[:320]}
                if owned:
                    entry['href'] = record_href(origin['project_id'], origin['record_id'])
                interface['providers' if rel['relation'] == 'provides' else 'consumers'].append(entry)
        interfaces.append(interface)
    member_by_id = {m['project_id']: m for m in members}
    declaration = doc['project'].get('archify', {}).get('architecture', {})
    node_projects = {node: member_by_id[pid] for node, pid in declaration.get('node_projects', {}).items()}
    # Include names for human relation browsing without copying record bodies.
    for rel in relations:
        for side in ('from', 'to'):
            ref = rel[side]
            record = records.get((ref.get('project_id'), ref.get('record_id')))
            ref['title'] = record['title'] if record else ref.get('record_id', ref.get('project_id'))
            ref['known'] = record is not None
            if record:
                ref['href'] = record_href(ref['project_id'], ref['record_id'])
    return {'members': members, 'interfaces': interfaces, 'relations': relations, 'node_projects': node_projects,
            'fingerprints': fingerprints,
            'coverage': {'scope': 'Explicit members only; no recursive traversal or inferred dependencies',
                         'resolved': sum(m['status'] == 'resolved' for m in members), 'declared': len(members),
                         'unresolved': [m['project_id'] for m in members if m['status'] != 'resolved']}}


def page(items, limit=8, offset=0):
    if limit < 1 or offset < 0:
        raise ValueError('limit must be positive and offset nonnegative')
    end = offset + limit
    return {'results': items[offset:end], 'total': len(items), 'offset': offset,
            'truncated': end < len(items), 'next_offset': end if end < len(items) else None}


def query_system(doc, command, *, registry=None, limit=8, offset=0, project=None, query='', record=None):
    view = compose_system(doc, registry)
    pid = project or doc['project']['project_id']
    if command == 'members':
        items = view['members']
    elif command == 'interfaces':
        items = [r for r in view['interfaces'] if (not project or r['project_id'] == project)
                 and (not query or query.casefold() in (r['title'] + ' ' + r['summary'] + ' ' + r['id']).casefold())]
    else:
        items = [r for r in view['relations'] if any(r[s].get('project_id') == pid and
                 (not record or r[s].get('record_id') == record) for s in ('from', 'to'))]
    result = page(items, limit, offset)
    # A single popular contract must not expand into an unbounded consumer list.
    for item in result['results']:
        if command == 'interfaces':
            for key in ('providers', 'consumers'):
                refs = item[key]
                item[key + '_total'] = len(refs)
                item[key + '_truncated'] = len(refs) > limit
                item[key] = refs[:limit]
            item['continue_with'] = {'command': 'read', 'project_id': item['project_id'], 'record_id': item['id']}
        if command == 'members':
            locations = item.get('locations', [])
            item['locations_total'] = len(locations)
            item['locations'] = locations[:limit]
    coverage = {**view['coverage'], 'unresolved_total': len(view['coverage']['unresolved']),
                'unresolved': view['coverage']['unresolved'][:limit],
                'notice': 'Only registered evidence is returned. Missing entries do not prove absence; inspect source when needed.'}
    return {'project_id': doc['project']['project_id'], **result, 'coverage': coverage}


def module_records(doc, module=None):
    """Explicit module_id wins; otherwise nearest module overview supplies identity."""
    modules = {r['id']: r for r in doc['records'] if r['kind'] == 'module'}
    if module is not None and module not in modules:
        raise ValueError(f'Unknown module ID: {module}')
    scopes = {}
    for record in doc['records']:
        explicit = record.get('module_id')
        if explicit:
            scopes[record['id']] = explicit
            continue
        path = Path(record['path'])
        candidates = [m for m in modules.values() if Path(m['path']).name in {'overview.md', 'index.md', 'README.md'}
                      and path.is_relative_to(Path(m['path']).parent)]
        scopes[record['id']] = max(candidates, key=lambda m: len(Path(m['path']).parts))['id'] if candidates else (record['id'] if record['id'] in modules else None)
    return [r for r in doc['records'] if module is None or scopes.get(r['id']) == module], scopes


def record_fingerprint(record):
    # Unrelated records or graph layout edits do not invalidate this read.
    # A bound source hash remains part of the scope to detect changed context.
    value = {k: v for k, v in record.items() if k not in {'path', 'line', 'end_line'}}
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


def open_project_target(entry, pid, diagram=None, record=None, node=None):
    """An explicit user click may prepare/reuse a declared member's local reader."""
    from project_map import load_project
    from render_map import export_reader, READER_VERSION
    from serve_map import start_reader, preview_lock
    payload = json.loads((Path(entry).parent / 'docs.json').read_text(encoding='utf-8'))
    owner = load_project(payload['manifest_path'])
    if not is_system(owner):
        raise ValueError('当前地图没有系统项目入口')
    member = next((m for m in owner['project'].get('system', {}).get('members', []) if m['project_id'] == pid), None)
    if member is None:
        raise ValueError('项目不在本系统明确登记的范围内')
    resolved, child = _member_doc(owner, member)
    if child is None:
        raise ValueError('地图尚不可用或存在多个工作树，请先明确项目位置：' + resolved.get('reason', resolved['status']))
    kind = diagram or member.get('diagram', 'architecture')
    params = {'mode': 'a', 'panel': kind}
    if record:
        if record not in {r['id'] for r in child['records']}:
            raise ValueError('目标记录已不存在')
        params.update(mode='b', record=record, angle='explain', panel='spec')
    elif kind in {'architecture', 'workflow'}:
        graph = child.get('diagram_sources', {}).get(kind, {})
        if not graph.get('ir') or graph.get('errors') or (is_system(child) and kind == 'workflow'):
            raise ValueError('目标图尚未登记或不可用')
        target_node = node or member.get('node')
        if target_node:
            ids = {n['id'] for n in graph['ir'].get('components' if kind == 'architecture' else 'nodes', [])}
            if target_node not in ids:
                raise ValueError('目标节点已不存在')
            params['node'] = target_node
    elif kind != 'spec':
        raise ValueError('未知图类型')
    output = Path(child['manifest_path']).parent / 'views' / 'index.html'
    output.parent.mkdir(parents=True, exist_ok=True)
    # Different system servers can open the same project concurrently. Serialize
    # publication per target across processes, independently of its service lock.
    with preview_lock(output.with_suffix('.build.html')):
        existing = {}
        try:
            existing = json.loads(output.with_name('docs.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            pass
        if not output.exists() or existing.get('fingerprint') != child['fingerprint'] or existing.get('reader_version') != READER_VERSION or is_system(child):
            exported = export_reader(child, output)
            if not record and kind != 'spec' and not exported['diagrams'].get(kind, {}).get('file'):
                raise ValueError('目标图未能生成，请核对原生图源；原地图仍保留')
        elif not record and kind != 'spec' and not existing.get('diagrams', {}).get(kind, {}).get('file'):
            raise ValueError('目标阅读页没有可用的图，请重新生成')
        return start_reader(output)['url'] + '#' + urlencode(params)
