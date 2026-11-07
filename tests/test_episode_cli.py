import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]


class UnifiedCLI(unittest.TestCase):
    def run_cli(self,*args):
        return subprocess.run([sys.executable,'-B','-X','utf8',str(ROOT/'scripts/check_episode.py'),*map(str,args)],capture_output=True,encoding='utf-8',cwd=ROOT)

    def test_optional_combat_validate_via_same_entry(self):
        result=self.run_cli('--combat-json',ROOT/'examples/fight/sword-duel.json')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['structural_status'],'pass')
        self.assertEqual(report['semantic_status'],'needs_review')
        self.assertEqual(report['media_status'],'NOT_RUN')

    def test_export_all_six_items_and_snapshot_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=pathlib.Path(tmp)/'delivery'
            args=('--combat-json',ROOT/'examples/fight/illusion-counterplay.json','--export',out)
            first=self.run_cli(*args)
            self.assertEqual(first.returncode,0,first.stdout+first.stderr)
            self.assertEqual({p.name for p in out.iterdir()},{'project.json','01-design.md','02-assets.md','03-storyboard.md','04-keyframes.md','05-video-prompts.md','06-review.md'})
            saved={p.name:p.read_bytes() for p in out.iterdir()}
            second=self.run_cli(*args)
            self.assertEqual(second.returncode,2)
            self.assertEqual(saved,{p.name:p.read_bytes() for p in out.iterdir()})

    def test_faithful_fight_from_independent_user_simulation(self):
        result=self.run_cli(ROOT/'examples/faithful-fight-scene.md','--scope','visual','--require-visual','--source',ROOT/'examples/faithful-fight-source.md')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('V14',result.stdout)  # The raw source has no labeled dialogue; preserve that honest warning.
        self.assertNotIn('[FAIL]',result.stdout)

    def test_export_requires_json(self):
        result=self.run_cli('--export','unused')
        self.assertEqual(result.returncode,2)

    def test_plain_legacy_episode(self):
        result=self.run_cli(ROOT/'examples/screenplay-extended.md','--format','long')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertNotIn('V14',result.stdout)

    def test_rejects_extra_path_and_unknown_flags(self):
        self.assertEqual(self.run_cli(ROOT/'examples/storyboard-source.md','extra.md').returncode,2)
        self.assertEqual(self.run_cli('--invented-flag').returncode,2)


    def test_isolated_python_mode_finds_only_bundled_helpers(self):
        base=[sys.executable,'-I','-B','-X','utf8',str(ROOT/'scripts/check_episode.py')]
        for args in (['--self-test'],['--combat-json',str(ROOT/'examples/fight/sword-duel.json')],[str(ROOT/'examples/storyboard-scene.md'),'--scope','visual','--source',str(ROOT/'examples/storyboard-source.md')]):
            result=subprocess.run(base+args,cwd=ROOT.parent,capture_output=True,encoding='utf-8')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)



if __name__=='__main__':
    unittest.main()
