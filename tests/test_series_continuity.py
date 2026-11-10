"""Series ledger regression tests; run with unittest discover (no third-party deps)."""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "check_series.py"
SPEC = importlib.util.spec_from_file_location("validate_series_under_test", VALIDATOR)
series = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(series)

LEGACY = """# 全剧台账
当前集: 30
## 伏笔账
| ID | 内容 | 埋于 | 拟收 | 状态 | 备注 |
|---|---|---|---|---|---|
| F01 | 旧怀表 | 3 | 28 | 收 | 已回收 |
| F02 | 神秘来电 | 12 | 31 | 养 | 敌方内讧 |
## 人物账
| 角色 | 首出 | 状态 | 关系 | 变动集 | 备注 |
|---|---|---|---|---|---|
| 林辰 | 1 | 存活 | 主角 | 30 | |
| 陈峰 | 1 | 死亡 | 敌 | 25 | 坠楼 |
## 道具账
| 道具 | 持有 | 状态 | 变动集 |
|---|---|---|---|
| 玄铁令 | 林辰 | 怀中 | 12 |
## 世界观规则账
| 规则 | 确立集 | 引用集 | 违反 |
|---|---|---|---|
| 龙王令只一次 | 12 | 25 | 否 |
付费墙落位: 一级墙 第12集 / 二级墙 第30集 / 三级墙 第56集
"""
BASELINE = """【视频画幅】：9:16
【全片风格】：写实仙侠，湿石与暗铜
【单次生成时长能力】：0–30秒之间任意时长
【分段策略】：按内容关联判断；不默认取上限，不均分。
【当前视觉版本】：v2
"""
ASSET_HEADERS = ("资产", "稳定锚点", "当前状态", "持有/所在", "适用集场", "提示词", "图片已读", "平台可用")
ASSET = ("玄铁令", "暗铜八角缺口", "边缘开裂", "林辰右手", "EP01-SC01", "暗铜八角令牌，右上角缺口", "未读", "未验证")
CHAIN_HEADERS = ("ID", "场次范围", "原文锚点", "事件事实", "起态", "结果", "关联镜头", "交接帧", "状态")
CHAIN = ("C01", "EP01-SC01", "亮令", "令牌拍桌", "林辰持令", "令牌落桌", "镜头1", "single@2秒", "活跃")
COMBAT_HEADERS = ("场次", "双方目标", "有效规则", "对手变招", "不可逆代价", "战场痕迹", "呼吸拍", "所知/实际", "数值复算")
COMBAT = ("EP01-SC01", "救人", "不能越阶", "改攻门侧", "符耗尽", "积水", "停步喘息", "误认退路畅通/门已封", "3米用1秒")
SCRIPT = "第【30】集\n林辰：停下。\n【本集断章卡点】：门开。（黑屏）\n"


def table(headers, rows):
    return "\n".join("| " + " | ".join(row) + " |" for row in (headers, ("---",) * len(headers), *rows)) + "\n"


def ledger(*, baseline=BASELINE, asset_headers=ASSET_HEADERS, assets=(ASSET,),
           chain_headers=CHAIN_HEADERS, chains=(CHAIN,), combat_headers=COMBAT_HEADERS,
           combats=(COMBAT,)):
    text = LEGACY + "\n## 视觉制作账\n" + baseline
    if assets is not None:
        text += "\n### 资产状态\n" + table(asset_headers, assets)
    if chains is not None:
        text += "\n### 稳定事件链与段界\n" + table(chain_headers, chains)
    if combats is not None:
        text += "\n### 斗法扩展（有战斗场时填写）\n" + table(combat_headers, combats)
    return text


def replace_cell(row, index, value):
    result = list(row)
    result[index] = value
    return tuple(result)


def warnings(text, code):
    fails, warns, _ = series.validate_ledger(text)
    assert not fails, fails
    return [message for message in warns if message.startswith(code + " ")]


class VisualLedgerTests(unittest.TestCase):
    def test_legacy_ledger_needs_no_visual_extension(self):
        self.assertEqual(series.validate_ledger(LEGACY), ([], [], 30))

    def test_valid_visual_values_do_not_need_header_keywords(self):
        self.assertEqual(series.validate_ledger(ledger()), ([], [], 30))

    def test_combat_extension_is_optional(self):
        self.assertEqual(series.validate_ledger(ledger(combats=None)), ([], [], 30))

    def test_old_capability_field_is_not_accepted(self):
        baseline = BASELINE.replace(
            "【单次生成时长能力】：0–30秒之间任意时长\n【分段策略】：按内容关联判断；不默认取上限，不均分。",
            "【单段时长上限】：12秒（项目决定）",
        )
        self.assertTrue(any("单次生成时长能力" in message for message in warnings(ledger(baseline=baseline), "S9")))

    def test_missing_strategy_warns_s9(self):
        baseline = BASELINE.replace("【分段策略】：按内容关联判断；不默认取上限，不均分。\n", "")
        self.assertTrue(any("分段策略" in message for message in warnings(ledger(baseline=baseline), "S9")))

    def test_empty_strategy_warns_s9(self):
        baseline = BASELINE.replace(
            "【分段策略】：按内容关联判断；不默认取上限，不均分。",
            "【分段策略】：",
        )
        self.assertTrue(any("分段策略" in message for message in warnings(ledger(baseline=baseline), "S9")))

    def test_empty_baseline_cannot_borrow_next_line(self):
        for value in ("", " ", "\t", "\u3000", "\u00a0", "\u200b"):
            with self.subTest(value=repr(value)):
                text = ledger(baseline=BASELINE.replace("：9:16", "：" + value))
                self.assertTrue(any("视频画幅" in message for message in warnings(text, "S9")))

    def test_every_baseline_field_must_be_filled(self):
        for line in BASELINE.splitlines():
            label = line.split("：", 1)[0]
            with self.subTest(label=label):
                text = ledger(baseline=BASELINE.replace(line, label + "："))
                self.assertTrue(any(label.strip("【】") in message for message in warnings(text, "S9")))

    def test_baseline_placeholders_are_not_values(self):
        for value in ("____", "---", "……", "待填", "待确认", "TODO", "TODO: later", "TBD（待定）", "<待填>", "__ 秒", "视频画幅", "视频画幅：", "**待填**"):
            with self.subTest(value=value):
                text = ledger(baseline=BASELINE.replace("9:16", value))
                self.assertTrue(any("视频画幅" in message for message in warnings(text, "S9")))

    def test_other_sections_cannot_supply_visual_baseline(self):
        text = LEGACY + BASELINE + "\n## 视觉制作账\n" + ledger(baseline="").split("## 视觉制作账\n", 1)[1]
        text += "\n## 附录\n" + BASELINE
        self.assertEqual(len([m for m in warnings(text, "S9") if "资产" not in m]), 5)

    def test_absent_or_empty_asset_table_warns(self):
        for rows in (None, ()):
            with self.subTest(rows=rows):
                self.assertTrue(any("资产" in message for message in warnings(ledger(assets=rows), "S9")))

    def test_asset_required_columns_are_checked_by_header(self):
        for index in range(6):
            with self.subTest(column=ASSET_HEADERS[index]):
                headers = ASSET_HEADERS[:index] + ASSET_HEADERS[index + 1:]
                row = ASSET[:index] + ASSET[index + 1:]
                self.assertTrue(any(ASSET_HEADERS[index] in m for m in warnings(ledger(asset_headers=headers, assets=(row,)), "S9")))

    def test_asset_required_cells_cannot_be_empty_or_placeholders(self):
        for index in range(6):
            for value in ("", "\u3000", "____", "待填", ASSET_HEADERS[index]):
                with self.subTest(column=ASSET_HEADERS[index], value=value):
                    self.assertTrue(warnings(ledger(assets=(replace_cell(ASSET, index, value),)), "S9"))

    def test_reordered_asset_columns_are_accepted(self):
        self.assertFalse(warnings(ledger(asset_headers=ASSET_HEADERS[::-1], assets=(ASSET[::-1],)), "S9"))

    def test_unknown_media_statuses_are_honest_valid_records(self):
        self.assertFalse(warnings(ledger(), "S9"))

    def test_missing_or_empty_chain_table_warns(self):
        for rows in (None, ()):
            with self.subTest(rows=rows):
                self.assertTrue(warnings(ledger(chains=rows), "S10"))

    def test_empty_and_placeholder_chain_ids_warn_even_with_valid_rows(self):
        for value in ("", "\t", "____", "C__", "待填", "ID", "编号"):
            with self.subTest(value=value):
                rows = (CHAIN, replace_cell(CHAIN, 0, value))
                self.assertTrue(warnings(ledger(chains=rows), "S10"))

    def test_missing_id_column_cannot_treat_first_cell_as_id(self):
        self.assertTrue(warnings(ledger(chain_headers=CHAIN_HEADERS[1:], chains=(CHAIN[1:],)), "S10"))

    def test_same_scene_duplicate_chain_id_warns(self):
        messages = warnings(ledger(chains=(CHAIN, CHAIN)), "S10")
        self.assertTrue(any("重复" in message and "C01" in message and "EP01-SC01" in message for message in messages))

    def test_chain_ids_can_be_reused_in_different_scenes(self):
        rows = (CHAIN, replace_cell(CHAIN, 1, "EP01-SC02"), replace_cell(CHAIN, 1, "EP02-SC01"))
        self.assertFalse(warnings(ledger(chains=rows), "S10"))

    def test_reordered_chain_columns_use_id_and_scope_headers(self):
        headers = CHAIN_HEADERS[1:] + CHAIN_HEADERS[:1]
        first = CHAIN[1:] + CHAIN[:1]
        second = replace_cell(first, 0, "EP01-SC02")
        self.assertFalse(warnings(ledger(chain_headers=headers, chains=(first, second)), "S10"))
        self.assertTrue(warnings(ledger(chain_headers=headers, chains=(first, first)), "S10"))

    def test_blank_declared_chain_scope_warns(self):
        for scope in ("", "SC__", "待填"):
            with self.subTest(scope=scope):
                self.assertTrue(warnings(ledger(chains=(replace_cell(CHAIN, 1, scope),)), "S10"))

    def test_separate_episode_and_scene_columns_scope_ids(self):
        headers = ("集数", "场次", "链ID")
        rows = (("EP01", "SC01", "C01"), ("EP02", "SC01", "C01"))
        self.assertFalse(warnings(ledger(chain_headers=headers, chains=rows), "S10"))
        self.assertTrue(warnings(ledger(chain_headers=headers, chains=rows + rows[:1]), "S10"))

    def test_scene_headings_scope_legacy_chain_tables(self):
        text = ledger(chains=None, combats=None)
        for scope in ("EP01-SC01", "EP01-SC02"):
            text += "\n### " + scope + "\n#### 稳定事件链与段界\n" + table(("ID",), (("C01",),))
        self.assertFalse(warnings(text, "S10"))
        text += "\n### EP01-SC01\n#### 稳定事件链与段界\n" + table(("ID",), (("C01",),))
        self.assertTrue(warnings(text, "S10"))

    def test_old_visual_chain_table_without_scope_is_compatible(self):
        headers = CHAIN_HEADERS[:1] + CHAIN_HEADERS[2:]
        row = CHAIN[:1] + CHAIN[2:]
        self.assertFalse(warnings(ledger(chain_headers=headers, chains=(row,)), "S10"))
        self.assertTrue(warnings(ledger(chain_headers=headers, chains=(row, row)), "S10"))

    def test_empty_combat_table_warns(self):
        self.assertTrue(warnings(ledger(combats=()), "S11"))

    def test_combat_column_names_alone_are_not_actual_values(self):
        values = ("SC01", "目标", "规则", "对手变招", "代价", "痕迹", "呼吸拍", "所知/实际", "复算")
        self.assertTrue(warnings(ledger(combats=(values,)), "S11"))

    def test_each_combat_field_and_scene_must_be_filled(self):
        for index in (0, 1, 2, 4, 5, 8):
            for value in ("", "\u3000", "____", "待填", COMBAT_HEADERS[index], COMBAT_HEADERS[index] + "："):
                with self.subTest(column=COMBAT_HEADERS[index], value=value):
                    self.assertTrue(warnings(ledger(combats=(replace_cell(COMBAT, index, value),)), "S11"))

    def test_combat_keywords_elsewhere_cannot_rescue_empty_value(self):
        bad = replace_cell(COMBAT, 1, "")
        bad = replace_cell(bad, 3, "目标/规则/代价/痕迹/复算")
        self.assertTrue(warnings(ledger(combats=(bad,)), "S11"))

    def test_missing_combat_columns_warn(self):
        for index in (0, 1, 2, 4, 5, 8):
            with self.subTest(column=COMBAT_HEADERS[index]):
                headers = COMBAT_HEADERS[:index] + COMBAT_HEADERS[index + 1:]
                row = COMBAT[:index] + COMBAT[index + 1:]
                self.assertTrue(any(COMBAT_HEADERS[index] in m for m in warnings(ledger(combat_headers=headers, combats=(row,)), "S11")))

    def test_reordered_combat_columns_are_accepted(self):
        self.assertFalse(warnings(ledger(combat_headers=COMBAT_HEADERS[::-1], combats=(COMBAT[::-1],)), "S11"))

    def test_short_combat_row_warns(self):
        self.assertTrue(warnings(ledger(combats=(COMBAT[:-1],)), "S11"))

    def test_every_combat_row_is_checked(self):
        for rows in ((COMBAT, replace_cell(COMBAT, 1, "")), (replace_cell(COMBAT, 1, ""), COMBAT)):
            with self.subTest(rows=rows):
                self.assertTrue(warnings(ledger(combats=rows), "S11"))


    def test_same_scene_duplicate_across_combined_and_split_scope_columns(self):
        text = ledger(combats=None)
        text += "\n### 稳定事件链补记\n" + table(("集数", "场次", "ID"), (("EP1", "SC1", "C01"),))
        self.assertTrue(warnings(text, "S10"))

    def test_same_scene_duplicate_across_heading_and_row_scopes(self):
        text = ledger(combats=None)
        text += "\n### EP01-SC01\n#### 稳定事件链补记\n" + table(("ID",), (("C01",),))
        self.assertTrue(warnings(text, "S10"))

    def test_same_scene_duplicate_with_chinese_scope_spelling(self):
        rows = (CHAIN, replace_cell(CHAIN, 1, "第1集第1场"))
        self.assertTrue(warnings(ledger(chains=rows), "S10"))

    def test_nested_combat_table_does_not_become_a_chain_table(self):
        text = ledger(combats=None)
        text += "\n#### 斗法扩展\n" + table(COMBAT_HEADERS, (COMBAT,))
        self.assertEqual(series.validate_ledger(text), ([], [], 30))

    def test_escaped_pipe_in_asset_value_keeps_columns_aligned(self):
        row = replace_cell(ASSET, 1, r"暗铜八角\|右上角缺口")
        self.assertEqual(series.validate_ledger(ledger(assets=(row,))), ([], [], 30))

    def test_short_combat_header_aliases_map_to_values(self):
        headers = ("场次", "目标", "规则", "代价", "痕迹", "复算")
        row = ("EP01-SC01", "救人", "不能越阶", "符耗尽", "积水", "3米用1秒")
        self.assertFalse(warnings(ledger(combat_headers=headers, combats=(row,)), "S11"))

    def test_structural_check_does_not_claim_to_verify_physics(self):
        row = replace_cell(COMBAT, 8, "100米用0秒")
        self.assertFalse(warnings(ledger(combats=(row,)), "S11"))

    def test_crlf_and_plain_ascii_baseline_fields(self):
        baseline = BASELINE.replace("【", "").replace("】", "").replace("：", ":")
        self.assertEqual(series.validate_ledger(ledger(baseline=baseline).replace("\n", "\r\n")), ([], [], 30))
        baseline = baseline.replace(":9:16", ": \t")
        self.assertTrue(any("视频画幅" in m for m in warnings(ledger(baseline=baseline).replace("\n", "\r\n"), "S9")))


class ScriptBoundaryTests(unittest.TestCase):
    def test_visual_layers_are_excluded_from_s3_s4_s5(self):
        for marker in ("【视觉制作包】", "## 视觉制作包", "【完整导演分镜】", "### 完整导演分镜", "【视频提示词母稿】", "## 视觉导演记录"):
            with self.subTest(marker=marker):
                visual = marker + "\n景别：近景\n起态：林辰持令\n陈峰：引用往集台词\n陌生人：提示词引用\n"
                fails, warns, _ = series.validate_ledger(LEGACY, scripts={30: SCRIPT + visual})
                self.assertEqual(fails, [])
                self.assertFalse(any(m.startswith("S4 ") for m in warns), warns)

    def test_visual_hook_cannot_supply_script_hook(self):
        text = "第【30】集\n林辰：停下。\n【视觉制作包】\n【本集断章卡点】：提示词中的黑屏\n"
        fails, _, _ = series.validate_ledger(LEGACY, scripts={30: text})
        self.assertTrue(any(m.startswith("S5 ") and "第30集" in m for m in fails))

    def test_real_dialogue_before_visual_marker_still_counts(self):
        text = SCRIPT + "陈峰：我回来了。\n陌生人：站住。\n陌生人：再说一次。\n【视觉制作包】\n景别：近景\n"
        fails, warns, _ = series.validate_ledger(LEGACY, scripts={30: text})
        self.assertEqual(sum(m.startswith("S3 ") for m in fails), 1)
        self.assertEqual(sum(m.startswith("S4 ") and "陌生人" in m for m in warns), 1)

    def test_inline_visual_marker_in_dialogue_is_not_a_boundary(self):
        text = "林辰：看【视觉制作包】。\n陈峰：我回来了。\n"
        fails, _, _ = series.validate_ledger(LEGACY, scripts={30: text})
        self.assertTrue(any(m.startswith("S3 ") for m in fails))
        self.assertTrue(any(m.startswith("S5 ") for m in fails))


class LegacyChecksTests(unittest.TestCase):
    def test_existing_self_test_interface(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(series.self_test(), 0)
        self.assertIn("self-test PASSED", output.getvalue())

    def test_s1_overdue_and_s2_abandoned_reason_still_warn(self):
        text = LEGACY.replace("| F02 | 神秘来电 | 12 | 31 | 养 | 敌方内讧 |", "| F02 | 神秘来电 | 12 | 8 | 已埋 | |\n| F03 | 旧线索 | 1 | 2 | 废 | |")
        _, warns, _ = series.validate_ledger(text)
        self.assertTrue(any(m.startswith("S1 ") for m in warns))
        self.assertTrue(any(m.startswith("S2 ") for m in warns))

    def test_s6_long_profile_and_s7_required_tables(self):
        text = LEGACY.replace("第12集", "第6集").replace("第30集", "第15集").replace("第56集", "第28集")
        self.assertFalse(any(m.startswith("S6 ") for m in series.validate_ledger(text, total_eps=40)[1]))
        self.assertTrue(any(m.startswith("S6 ") for m in series.validate_ledger(LEGACY, total_eps=40)[1]))
        self.assertEqual(sum(m.startswith("S7 ") for m in series.validate_ledger("空台账")[0]), 4)

    def test_s7_requires_parseable_rows_not_only_headings(self):
        headings = """# 台账
当前集: 1
## 伏笔账
## 人物账
## 道具账
## 世界观规则账
"""
        fails, _, _ = series.validate_ledger(headings)
        self.assertEqual(sum(message.startswith("S7 ") for message in fails), 4)

    def test_s3_does_not_treat_un_death_as_dead(self):
        text = LEGACY.replace("| 林辰 | 1 | 存活 | 主角 | 30 | |", "| 林辰 | 1 | 未死亡 | 主角 | 30 | |")
        fails, _, _ = series.validate_ledger(text, scripts={31: "林辰：我还活着。\n【本集断章卡点】：黑屏"})
        self.assertFalse(any(message.startswith("S3 ") for message in fails), fails)

    def test_s4_requires_exact_roster_name(self):
        fails, warns, _ = series.validate_ledger(
            LEGACY,
            scripts={30: "林辰华：这是新角色。\n【本集断章卡点】：黑屏"},
        )
        self.assertFalse(fails, fails)
        self.assertTrue(any(message.startswith("S4 ") and "林辰华" in message for message in warns), warns)

    def test_s6_rejects_unsupported_episode_count_without_crashing(self):
        fails, _, _ = series.validate_ledger(LEGACY, total_eps=70)
        self.assertTrue(any(message.startswith("S6 ") and "不支持总集数 70" in message for message in fails), fails)

    def test_s8_reversal_window_still_warns_only_nearby_reuse(self):
        headers = ("集数", "反转标签", "核心冲突事件")
        close = (("EP1", "[F]", "夺令"), ("EP3", "[F]", "破门"))
        distant = (("EP1", "[F]", "夺令"), ("EP4", "[F]", "破门"))
        self.assertTrue(warnings(LEGACY + "\n## 反转手段轮换矩阵\n" + table(headers, close), "S8"))
        self.assertFalse(warnings(LEGACY + "\n## 反转手段轮换矩阵\n" + table(headers, distant), "S8"))


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.ledger_path = self.directory / "台账.md"
        self.ledger_path.write_text(LEGACY, encoding="utf-8-sig")

    def run_cli(self, *args, env=None):
        settings = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        if env:
            settings.update(env)
        return subprocess.run([sys.executable, "-B", str(VALIDATOR), *map(str, args)],
                              cwd=self.directory, env=settings, capture_output=True, timeout=20)

    def test_cli_self_test(self):
        result = self.run_cli("--self-test")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"self-test PASSED", result.stdout)

    def test_utf8_output_and_bom_input_with_ascii_stdio(self):
        result = self.run_cli(self.ledger_path, env={"PYTHONIOENCODING": "ascii"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("结果: PASSED", result.stdout.decode("utf-8"))

    def test_cli_reports_script_body_failures_and_ignores_visual_dialogue(self):
        script_dir = self.directory / "剧本"
        script_dir.mkdir()
        path = script_dir / "EP30.md"
        path.write_text(SCRIPT + "【视觉制作包】\n景别：近景\n起态：林辰持令\n陈峰：往集引用\n", encoding="utf-8-sig")
        result = self.run_cli(self.ledger_path, "--script-dir", script_dir)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn(b"S3 ", result.stdout)
        self.assertNotIn(b"S4 ", result.stdout)
        path.write_text("林辰：停下。\n【视觉制作包】\n【本集断章卡点】：黑屏\n", encoding="utf-8")
        result = self.run_cli(self.ledger_path, "--script-dir", script_dir)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(b"S5 ", result.stdout)

    def test_invalid_options_return_usage_error_without_traceback(self):
        for options in (("--episodes",), ("--episodes", "abc"), ("--episodes", "0"), ("--episodes", "-1"), ("--episodes", "70"), ("--script-dir",), ("--script-dir", "--episodes", "40"), ("--unknown",)):
            with self.subTest(options=options):
                result = self.run_cli(self.ledger_path, *options)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertNotIn(b"Traceback", result.stdout + result.stderr)

    def test_missing_or_invalid_utf8_ledger_is_usage_error(self):
        for path in (self.directory / "不存在.md", self.directory):
            with self.subTest(path=path):
                result = self.run_cli(path)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertNotIn(b"Traceback", result.stdout + result.stderr)
        self.ledger_path.write_bytes(b"\xff\xfe\x00")
        self.assertEqual(self.run_cli(self.ledger_path).returncode, 2)

    def test_unreadable_script_cannot_silently_pass(self):
        script_dir = self.directory / "剧本"
        script_dir.mkdir()
        (script_dir / "EP30.md").write_bytes(b"\xff\xfe\x00")
        result = self.run_cli(self.ledger_path, "--script-dir", script_dir)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn(b"PASSED", result.stdout)
        self.assertNotIn(b"Traceback", result.stderr)

    def test_visual_cli_pass_describes_structural_limit(self):
        self.ledger_path.write_text(ledger(), encoding="utf-8")
        result = self.run_cli(self.ledger_path)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn(b"WARN", result.stdout)
        self.assertIn("结构", result.stdout.decode("utf-8"))
        self.assertIn("媒体", result.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
