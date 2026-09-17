"""Small, local name-to-map catalog. Never loads records or research objects."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import project_map as pm


def metadata(value):
    path = Path(value).expanduser().resolve()
    if path.is_dir():
        path = path / 'project.yaml'
    data = pm._mapping(pm._text(path), str(path))
    if data.get('schema') == 'project-map/v1':
        if not data.get('project_id') or not data.get('name'):
            raise pm.MapError('Project manifest requires project_id and name')
        return path, 'project', data
    raise pm.MapError('Unsupported map manifest schema')


def register(value, registry=None, *, aliases=(), identity=None, preferred=False):
    manifest, kind, meta = metadata(value)
    path = pm.registry_file(registry)
    with pm._registry_writer_lock(path):
        data = pm._registry(path)
        before = copy.deepcopy(data)
        entries = data['projects']
        key = meta['project_id']
        if identity and identity != key:
            raise pm.MapError('Explicit ID differs from project manifest')
        entry = entries.setdefault(key, {'locations': []})
        entry['name'] = meta['name']
        entry['aliases'] = sorted(set(entry.get('aliases', [])) | {a.strip() for a in aliases if a.strip()})
        if not any(Path(loc['manifest_path']).resolve() == manifest for loc in entry['locations']):
            entry['locations'].append({'manifest_path': str(manifest)})
        if preferred:
            entry['preferred_manifest'] = str(manifest)
        changed = data != before
        if changed:
            pm._atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    return {'project_id': key, 'kind': kind, 'registry_path': str(path), 'changed': changed}


def _entry_paths(manifest, kind, meta):
    def local(value):
        return str((manifest.parent / value).resolve()) if isinstance(value, str) and value else None
    return {'reading_path': local(meta.get('map', 'map.md')), 'next_step': 'project_map.py search/read; render_map.py when a browser view is requested'}


def inspect_entry(key, kind, entry, current=None):
    locations = []
    for loc in entry.get('locations', []):
        name = loc.get('manifest_path', '')
        try:
            manifest, actual_kind, meta = metadata(name)
            if actual_kind != kind or (kind == 'project' and meta.get('project_id') != key):
                raise pm.MapError('Manifest identity or type mismatch')
            details = _entry_paths(manifest, kind, meta)
            missing = [v for k, v in details.items() if k.endswith('_path') and v and not Path(v).exists()]
            locations.append({'manifest_path': str(manifest), 'status': 'available',
                              'entrypoints': details, 'missing_entrypoints': missing})
        except (pm.MapError, OSError, ValueError, TypeError, AttributeError) as exc:
            locations.append({'manifest_path': name, 'status': 'unavailable', 'reason': str(exc)[:350]})
    live = [loc for loc in locations if loc['status'] == 'available']
    chosen, selection = None, None
    if current:
        target = Path(current).expanduser().resolve()
        matching = [loc for loc in live if target == Path(loc['manifest_path']) or target.is_relative_to(Path(loc['manifest_path']).parent)]
        if not matching and kind == 'project':
            root = pm._git_version(target if target.is_dir() else target.parent, include_dirty=False).get('git_root')
            if root:
                matching = [loc for loc in live if pm._git_version(Path(loc['manifest_path']).parent, include_dirty=False).get('git_root') == root]
        if len(matching) == 1:
            chosen, selection = matching[0], 'current_location'
        elif len(matching) > 1:
            return {'project_id': key, 'kind': kind, 'name': entry['name'], 'status': 'ambiguous', 'locations': locations}
    preferred = entry.get('preferred_manifest')
    if not chosen and preferred:
        chosen = next((loc for loc in live if Path(loc['manifest_path']) == Path(preferred)), None)
        selection = 'preferred_location' if chosen else None
        # A missing preferred working copy must not silently fall back to an old copy.
        if not chosen:
            return {'project_id': key, 'kind': kind, 'name': entry['name'], 'status': 'unresolved',
                    'reason': 'Preferred location unavailable; choose an explicit live location', 'locations': locations}
    if not chosen and len(live) == 1:
        chosen, selection = live[0], 'only_location'
    result = {'project_id': key, 'kind': kind, 'name': entry['name'], 'aliases': entry.get('aliases', []),
              'status': 'resolved' if chosen else ('ambiguous' if live else 'unresolved'), 'locations': locations}
    if chosen:
        result.update(manifest_path=chosen['manifest_path'], selection=selection, **chosen['entrypoints'])
    return result


def lookup(query=None, registry=None, *, current=None, limit=8, offset=0):
    if not 1 <= limit <= 50 or offset < 0:
        raise pm.MapError('Use 1 <= limit <= 50 and offset >= 0')
    data = pm._registry(pm.registry_file(registry))
    candidates = [(key, 'project', entry) for key, entry in data['projects'].items()]
    if query is not None:
        q = query.strip().casefold()
        if not q:
            raise pm.MapError('Use list for the catalog; lookup requires a nonempty name or ID')
        by_id = [item for item in candidates if item[0].casefold() == q]
        exact = [item for item in candidates if q in [str(s).casefold() for s in [item[2]['name'], *item[2].get('aliases', [])]]]
        candidates = by_id or exact or [item for item in candidates if any(q in str(s).casefold() for s in [item[2]['name'], *item[2].get('aliases', [])])]
    candidates.sort(key=lambda item: (item[2]['name'].casefold(), item[0]))
    total = len(candidates)
    page = [inspect_entry(*item, current=current) for item in candidates[offset:offset + limit]]
    return {'status': ('unresolved' if not total else 'ambiguous' if total > 1 else page[0]['status'] if page else 'page_empty') if query is not None else 'catalog',
            'query': query, 'total': total, 'offset': offset, 'limit': limit, 'results': page,
            'next_offset': offset + len(page) if offset + len(page) < total else None,
            'content_loaded': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    reg = sub.add_parser('register')
    reg.add_argument('manifest')
    reg.add_argument('--alias', action='append', default=[])
    reg.add_argument('--id', help='Optional expected project ID')
    reg.add_argument('--preferred', action='store_true', help='Explicitly make this the default working location')
    for cmd in ('locate', 'list'):
        p = sub.add_parser(cmd)
        if cmd == 'locate':
            p.add_argument('query')
        p.add_argument('--current', default=str(Path.cwd()))
        p.add_argument('--limit', type=int, default=8)
        p.add_argument('--offset', type=int, default=0)
    for p in (reg, *[sub.choices[c] for c in ('locate', 'list')]):
        p.add_argument('--registry')
    args = parser.parse_args()
    try:
        if args.command == 'register':
            result = register(args.manifest, args.registry, aliases=args.alias, identity=args.id, preferred=args.preferred)
        else:
            result = lookup(getattr(args, 'query', None), args.registry, current=args.current, limit=args.limit, offset=args.offset)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (pm.MapError, OSError, ValueError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
