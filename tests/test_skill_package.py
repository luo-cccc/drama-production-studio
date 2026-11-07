import hashlib
import json
import pathlib
import re
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]


class PackageContracts(unittest.TestCase):
    def test_one_skill_entry_and_metadata(self):
        self.assertEqual([p.relative_to(ROOT).as_posix() for p in ROOT.rglob('SKILL.md')],['SKILL.md'])
        text=(ROOT/'SKILL.md').read_text(encoding='utf-8')
        front=text.split('---',2)[1]
        self.assertIn('name: drama-production-studio',front)
        self.assertNotRegex(front,r'(?m)^(version|updated):')
        meta=json.loads((ROOT/'package-manifest.json').read_text(encoding='utf-8'))
        self.assertIn('version: "'+meta['version']+'"',front)

    def test_all_runtime_local_links_exist(self):
        files=[*ROOT.glob('*.md'),*list((ROOT/'references').rglob('*.md')),*list((ROOT/'templates').glob('*.md')),*list((ROOT/'docs').glob('*.md')),*list((ROOT/'examples').rglob('*.md'))]
        problems=[]
        for file in files:
            text=file.read_text(encoding='utf-8')
            # Only markdown targets. External references and fragment-only anchors aren't files.
            for target in re.findall(r'\]\(([^\s)]+)\)',text):
                if re.match(r'(?:https?|mailto|app|skill):',target) or target.startswith('#'):
                    continue
                name=target.split('#',1)[0].strip('<>')
                if name and not (file.parent/name).exists():
                    problems.append(f'{file.relative_to(ROOT)} -> {target}')
        self.assertEqual(problems,[])

    def test_eight_existing_modes_no_new_user_commands(self):
        text=(ROOT/'SKILL.md').read_text(encoding='utf-8')
        rows=re.findall(r'^\| ([0-7]) [^\n]+$',text,re.M)
        self.assertEqual(rows,list('01234567'))
        self.assertNotRegex(text,r'(?m)^\|[^\n]*\|[ \t]*/(?:分镜|斗法导演)')

    def test_internal_tools_have_no_source_tree_runtime_dependency(self):
        for file in (ROOT/'scripts').glob('*.py'):
            code=file.read_text(encoding='utf-8')
            for line in code.splitlines():
                if re.search(r'open\(|read_text\(|import_module\(|sys.path',line):
                    self.assertNotIn('xianxia-fight-director-main',line)
                    self.assertNotIn('script-to-storyboard-prompts-main',line)

    def test_source_targets_exist_and_imported_fixtures_keep_bytes(self):
        manifest=json.loads((ROOT/'docs/source-manifest.json').read_text(encoding='utf-8'))
        for source in manifest['sources']:
            self.assertRegex(source['sha256'],r'^[0-9a-f]{64}$')
            self.assertTrue(source['targets'])
            for target in source['targets']:
                self.assertTrue((ROOT/target).is_file(),target)
            if source['method']=='unchanged JSON bytes':
                target=ROOT/source['targets'][0]
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),source['sha256'])

    def test_rename_map_resolves_new_files_without_old_paths(self):
        manifest=json.loads((ROOT/'docs/name-map.json').read_text(encoding='utf-8'))
        for old,new in manifest['renamed_files'].items():
            self.assertFalse((ROOT/old).exists(),old)
            self.assertTrue((ROOT/new).is_file(),new)
        package=json.loads((ROOT/'package-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(package['name'],ROOT.name)
        for target in package['tools'].values():
            self.assertTrue((ROOT/target).is_file(),target)


if __name__=='__main__':
    unittest.main()
