"""Regression/adversarial tests against an actual complete three-segment example."""
import copy
import pathlib
import subprocess
import sys
import unittest

from scripts.check_episode import validate, collect_notes, net_chars
from scripts.check_storyboard import validate_visual_package

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOOD = (ROOT / "examples/storyboard-scene.md").read_text(encoding="utf-8")
GOOD12 = (ROOT / "examples/storyboard-content-segmented.md").read_text(encoding="utf-8")
SOURCE = (ROOT / "examples/storyboard-source.md").read_text(encoding="utf-8")


class VisualChecks(unittest.TestCase):
    def errors(self, text, source=SOURCE):
        return validate_visual_package(text, source)[0]

    def warnings(self, text, source=SOURCE):
        return validate_visual_package(text, source)[1]

    def assertCode(self, code, text, source=SOURCE):
        errors = self.errors(text, source)
        self.assertTrue(any(s.startswith(code + " ") for s in errors), errors)

    def assertWarn(self, code, text, source=SOURCE):
        warnings = self.warnings(text, source)
        self.assertTrue(any(s.startswith(code + " ") for s in warnings), warnings)

    def test_full_three_segment_package(self):
        self.assertEqual(validate_visual_package(GOOD, SOURCE), ([], []))

    def test_empty_package_not_success(self):
        self.assertCode("V1", "【视觉制作包】【视觉制作包结束】")

    def test_unclosed_package_not_success(self):
        self.assertCode("V1", GOOD.replace("【视觉制作包结束】", ""))

    def test_every_package_is_checked(self):
        self.assertCode("V1", GOOD + "\n【视觉制作包】【视觉制作包结束】")

    def test_empty_field_does_not_eat_next_line(self):
        self.assertCode("V2", GOOD.replace("【视频画幅】：9:16", "【视频画幅】：", 1))

    def test_placeholder_not_content(self):
        self.assertCode("V2", GOOD.replace("【视频画幅】：9:16", "【视频画幅】：____", 1))

    def test_shot_gap(self):
        self.assertCode("V3", GOOD.replace("S02｜FORMAL_2｜6–12", "S02｜FORMAL_2｜7–12"))

    def test_shot_overlap(self):
        self.assertCode("V3", GOOD.replace("S02｜FORMAL_2｜6–12", "S02｜FORMAL_2｜5–12"))

    def test_invalid_shot_is_not_silently_ignored(self):
        self.assertCode("V3", GOOD.replace("S02｜FORMAL_2｜6–12", "S02｜FORMAL_2｜NaN–12"))

    def test_total_matches_last_shot(self):
        self.assertCode("V3", GOOD.replace("【整场时长】：18秒", "【整场时长】：19秒"))

    def test_last_shot_cannot_borrow_prompt_field(self):
        left, right = GOOD.split("#### 镜头 S03", 1)
        board, later = right.split("【逐镜关键帧】", 1)
        board = board.replace("【运镜及拍摄主体】", "【删除字段】", 1)
        self.assertCode("V4", left + "#### 镜头 S03" + board + "【逐镜关键帧】" + later)

    def test_unknown_event_reference(self):
        self.assertCode("V4", GOOD.replace("【关联事件链】：C01", "【关联事件链】：C99", 1))

    def test_state_drift(self):
        left,right = GOOD.split("#### 镜头 S02",1)
        right=right.replace("【起态】：", "【起态】：右手突然多出一把剑；", 1)
        self.assertCode("V5", left + "#### 镜头 S02" + right)

    def test_each_segment_limit(self):
        self.assertCode("V6", GOOD.replace("【单次生成时长能力】：0–30秒之间任意时长", "【单次生成时长能力】：0–5秒之间任意时长"))

    def test_total_longer_than_limit_is_valid_when_split(self):
        self.assertEqual(self.errors(GOOD), [])  # 18 seconds total; 3 x 6s, not 18 > 6.

    def test_segment_must_assign_whole_shots(self):
        self.assertCode("V6", GOOD.replace("| FORMAL_1 | 0–6", "| FORMAL_1 | 0–5"))

    def test_invalid_segment_id_is_not_silently_ignored(self):
        bad = GOOD.replace(
            "| FORMAL_1 | 0–6 | 0–6 | C01 |",
            "| BAD_ID | 0–6 | 0–6 | C01 |",
            1,
        )
        self.assertCode("V6", bad)

    def test_malformed_segment_row_is_not_silently_ignored(self):
        bad = GOOD.replace(
            "| FORMAL_1 | 0–6 | 0–6 | C01 |",
            "| BROKEN | 0–6 | 0–6 |",
            1,
        )
        self.assertCode("V6", bad)

    def test_frame_time_outside_shot(self):
        self.assertCode("V7", GOOD.replace("K01｜handoff｜S01｜6秒", "K01｜handoff｜S01｜7秒"))

    def test_frame_role_invalid(self):
        self.assertCode("V7", GOOD.replace("K01｜handoff", "K01｜unknown"))

    def test_frame_label_alone_not_image_prompt(self):
        self.assertCode("V7", GOOD.replace("【图像提示词】：", "【丢失图像字段】：", 1))

    def test_keyframe_requires_event_chain(self):
        left, right = GOOD.split("【逐镜关键帧】", 1)
        frames, tail = right.split("【视频提示词母稿】", 1)
        frames = frames.replace("【关联事件链】：C01\n", "", 1)
        self.assertCode("V7", left + "【逐镜关键帧】" + frames + "【视频提示词母稿】" + tail)

    def test_boundary_handoff_required(self):
        self.assertCode("V8", GOOD.replace("K01｜handoff", "K01｜single"))

    def test_high_risk_no_fallback(self):
        text=GOOD.replace("【生成风险】：低", "【生成风险】：高", 1)
        text=text.replace("【保底构图】：无需额外降级，双手和药箱保持可辨。", "【保底构图】：无", 1)
        self.assertCode("V12", text)

    def test_internal_id_in_generator_text(self):
        left,right=GOOD.split("【视频提示词母稿】",1)
        self.assertCode("V13", left + "【视频提示词母稿】" + right.replace("镜头一{", "镜头一{\n内部标识C01必须执行",1))

    def test_slightly_low_camera_not_shorthand(self):
        self.assertFalse(any(s.startswith("V13 ") for s in self.errors(GOOD)))

    def test_changed_spoken_text(self):
        left,right=GOOD.split("【视频提示词母稿】",1)
        self.assertCode("V14", left + "【视频提示词母稿】" + right.replace("门锁了，钥匙在你那？", "门开了，钥匙给我。"))

    def test_missing_dialogue(self):
        self.assertCode("V14", GOOD.replace('穆青（低声）：“门锁了，钥匙在你那？”', ''))

    def test_wrong_speaker(self):
        self.assertCode("V14", GOOD.replace('穆青（低声）：“门锁了，钥匙在你那？”', '阿澜（低声）：“门锁了，钥匙在你那？”'))

    def test_repeated_dialogue(self):
        self.assertCode("V14", GOOD.replace('穆青（低声）：“门锁了，钥匙在你那？”', '穆青（低声）：“门锁了，钥匙在你那？”\n穆青：“门锁了，钥匙在你那？”'))

    def test_no_source_no_false_claim(self):
        errors,warnings=validate_visual_package(GOOD)
        self.assertEqual(errors, [])
        self.assertTrue(any(s.startswith("V14 ") and "未运行" in s for s in warnings))

    def test_missing_segment_master(self):
        left,right=GOOD.split("#### 提交段 FORMAL_3",1)
        self.assertCode("V15", left + "【视觉制作包结束】")

    def test_master_wrong_duration(self):
        self.assertCode("V15", GOOD.replace("总时长：6秒", "总时长：5秒",1))

    def test_master_incomplete_fields(self):
        left,right=GOOD.split("【视频提示词母稿】",1)
        self.assertCode("V15",left+"【视频提示词母稿】"+right.replace("运镜及拍摄主体：", "遗漏项：",1))

    def test_visual_scene_not_forced_into_episode_length(self):
        self.assertEqual(validate(GOOD, scope="visual", source_text=SOURCE)[0], [])
        self.assertEqual(validate(GOOD, source_text=SOURCE)[0], [])

    def test_legacy_episode_stats_isolated_from_visual(self):
        script=(ROOT / "examples/screenplay-standard.md").read_text(encoding="utf-8")
        _,_,before=validate(script)
        _,_,after=validate(script+GOOD,source_text=SOURCE)
        self.assertEqual(before,after)
        self.assertEqual(collect_notes(script),collect_notes(script+GOOD))

    def test_new_delivery_cannot_silently_omit_visual(self):
        script=(ROOT / "examples/screenplay-standard.md").read_text(encoding="utf-8")
        self.assertTrue(any(s.startswith("V1 ") for s in validate(script,require_visual=True)[0]))

    def test_cli_visual_and_missing_source(self):
        cmd=[sys.executable,"-B","-X","utf8",str(ROOT/"scripts/check_episode.py"),str(ROOT/"examples/storyboard-scene.md"),"--scope","visual","--source",str(ROOT/"examples/storyboard-source.md")]
        result=subprocess.run(cmd,capture_output=True,encoding="utf-8")
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        cmd[-1]=str(ROOT/"examples/does-not-exist.md")
        result=subprocess.run(cmd,capture_output=True,encoding="utf-8")
        self.assertEqual(result.returncode,2)


    def test_content_driven_segment_package_passes(self):
        self.assertEqual(validate_visual_package(GOOD12, SOURCE), ([], []))

    def test_missing_segment_decision_table_fails_v16(self):
        text = GOOD12.replace("【分段决策表】", "【其他表】")
        self.assertCode("V16", text)

    def test_missing_segment_strategy_fails_v16(self):
        text = GOOD12.replace("【分段策略】：按内容关联判断；先保“开锁+放箱”与“抬门+进入”两个动作链，再在双手空闲、门关闭的稳定状态分段；不默认取上限，不均分。\n", "")
        self.assertCode("V16", text)

    def test_generic_segment_strategy_warns_v16(self):
        text = GOOD12.replace(
            "【分段策略】：按内容关联判断；先保“开锁+放箱”与“抬门+进入”两个动作链，再在双手空闲、门关闭的稳定状态分段；不默认取上限，不均分。",
            "【分段策略】：默认30秒，均分。",
        )
        self.assertWarn("V16", text)
        self.assertFalse(any(s.startswith("V16 ") for s in self.errors(text)))

    def test_missing_segment_rationale_fails_v16(self):
        text = GOOD12.replace("#### 分段依据 FORMAL_1", "#### 其他依据 FORMAL_1")
        self.assertCode("V16", text)

    def test_segment_duration_claim_must_match(self):
        text = GOOD12.replace("【本段时长】：8.0秒 = 开锁2.0", "【本段时长】：9.0秒 = 开锁2.0")
        self.assertCode("V16", text)

    def test_segment_over_model_capability_fails_v6(self):
        text = GOOD12.replace("【单次生成时长能力】：0–30秒之间任意时长", "【单次生成时长能力】：0–8秒之间任意时长")
        self.assertCode("V6", text)

    def test_old_capability_field_is_rejected(self):
        text = GOOD12.replace(
            "【单次生成时长能力】：0–30秒之间任意时长（0到30秒可任意选择）；本场实际段长按内容判断，未取上限。",
            "【单段时长上限】：30秒",
        )
        self.assertCode("V2", text)

    def test_old_contract_version_is_rejected(self):
        text = GOOD.replace("【包版本】：2.0", "【包版本】：1.1")
        self.assertCode("V1", text)

    def combat_fixture(self):
        # Synthetic structural fixture, not claimed to be a semantically reviewed fight/media.
        text=GOOD.replace('【场景类型】：普通场','【场景类型】：战斗场')
        text=text.replace('【资产清单】', '''【战斗设计方式】：原创斗法设计
【双方目标】：甲要通过门，乙要封门。
【有效规则】：符只能用一次，不能正面胜过对手。
【战斗终态】：符用尽，两方都有后续限制。
【数值复算】：速度与路径以源事实为准，此为结构夹具不证明物理成立。
【资产清单】''',1)
        extra='''【战斗动作拍】
| ID | 全场时码 | 行动 | 回应 | 结果 | 完成依赖 | 标记 |
|---|---|---|---|---|---|---|
| C01 | 0–6 | 甲改地面 | 乙侧移 | 碎片留地 | 无前拍 | 普通 |
| C02 | 6–12 | 甲试图通过 | 乙据前拍改变站位 | 武器留下缺口 | C01 | pivotal,adaptation |
| C03 | 12–18 | 停止新攻击 | 双方看清状态 | 代价保留 | C02 | breath |
【代价账】
| 归属 | 支出 | 来源拍 | 不可逆 | 后续限制 |
|---|---|---|---|---|
| 甲 | 符 | C01 | 是 | 此后不能再施术 |
| 乙 | 武器缺口 | C02 | 是 | 此后不能再刺击 |
【战场痕迹】
| ID | 痕迹 | 来源拍 | 后续影响 |
|---|---|---|---|
| T01 | 碎片 | C01 | 不能从原地蹬步 |
'''
        text=text.replace('【时长预算与分段】',extra+'【时长预算与分段】',1)
        frames=''
        for kid,role,time in (('K04','prep',7),('K05','contact',9),('K06','result',11)):
            frames+=f'''#### 关键帧 {kid}｜{role}｜S02｜{time}秒
【关联事件链】：C02
【静态状态】：此刻的接触姿态和兵器位置。
【图像提示词】：双人侧面中景静帧，手和兵器有一个明确接点，脚底贴地，身体轮廓清晰，侧光来自门内。
'''
        return text.replace('【视频提示词母稿】',frames+'【视频提示词母稿】',1)

    def test_combat_structural_fixture(self):
        self.assertEqual(self.errors(self.combat_fixture()),[])

    def test_missing_combat_design(self):
        self.assertCode('V9',GOOD.replace('【场景类型】：普通场','【场景类型】：战斗场'))

    def test_completion_dependency_not_future(self):
        self.assertCode('V9',self.combat_fixture().replace('| C01 | 普通 |','| C03 | 普通 |').replace('| 无前拍 | 普通 |','| C03 | 普通 |'))

    def test_two_sided_costs_required(self):
        self.assertCode('V9',self.combat_fixture().replace('| 乙 | 武器缺口','| 甲 | 武器缺口'))

    def test_irreversible_cost_required(self):
        self.assertCode('V9',self.combat_fixture().replace('| 是 |','| 否 |'))

    def test_breath_not_pivotal_or_overlapping(self):
        self.assertCode('V9',self.combat_fixture().replace('| pivotal,adaptation |','| pivotal,adaptation,breath |'))

    def test_pivotal_three_real_frames(self):
        self.assertCode('V10',self.combat_fixture().replace('K05｜contact','K05｜single'))

    def test_pivotal_frame_chronology(self):
        self.assertCode('V10',self.combat_fixture().replace('K05｜contact｜S02｜9秒','K05｜contact｜S02｜7秒'))

    def test_fixed_source_not_forced_to_invent_cost(self):
        text=self.combat_fixture().replace('【战斗设计方式】：原创斗法设计','【战斗设计方式】：既定动作忠实转译')
        left,rest=text.split('【代价账】',1)
        _,right=rest.split('【时长预算与分段】',1)
        self.assertFalse(any(s.startswith('V9 ') for s in self.errors(left+'【时长预算与分段】'+right)))



    def test_two_packages_share_source_by_disjoint_line_ranges(self):
        count=len(SOURCE.splitlines())
        one=GOOD.replace('【范围类型】：完整场',f'【源文行范围】：1–{count}\n【范围类型】：完整场',1)
        two=GOOD.replace('【范围类型】：完整场',f'【源文行范围】：{count+1}–{count*2}\n【范围类型】：完整场',1)
        self.assertEqual(self.errors(one+'\n'+two,SOURCE+SOURCE),[])

    def test_multiple_packages_need_explicit_source_scopes(self):
        self.assertCode('V14',GOOD+'\n'+GOOD,SOURCE+SOURCE)

    def test_source_scope_cannot_repeat_consumption(self):
        count=len(SOURCE.splitlines())
        one=GOOD.replace('【范围类型】：完整场',f'【源文行范围】：1–{count}\n【范围类型】：完整场',1)
        self.assertCode('V14',one+'\n'+one,SOURCE+SOURCE)



    def test_single_paragraph_quoted_source_is_checked(self):
        source='穆青：“门锁了，钥匙在你那？” 阿澜：“我照着，你先把药送进去。”'
        self.assertEqual(self.errors(GOOD,source),[])
        self.assertCode('V14',GOOD.replace('门锁了，钥匙在你那？','钥匙呢？'),source)

    def test_unrecognizable_speech_not_silent_pass(self):
        _,warnings=validate_visual_package(GOOD,'两个人说了些什么，随后进门。')
        self.assertTrue(any(s.startswith('V14 ') and '未识别' in s for s in warnings))



    def test_duration_with_real_confirmation_note(self):
        self.assertEqual(self.errors(GOOD.replace('【单次生成时长能力】：0–30秒之间任意时长（0到30秒可任意选择）；本场按用户指定6秒上限分段。', '【单次生成时长能力】：0–30秒之间任意时长；来源：用户已确认，仅本项目。')),[])

    def test_budget_table_not_confused_with_segment_assignment(self):
        budget='| 段号 | 内容 |\n|---|---|\n| FORMAL_1 | 台词2.8秒与动作并行 |\n'
        self.assertEqual(self.errors(GOOD.replace('【分段表】',budget+'【分段表】',1)),[])



    def test_quoted_original_speech_not_process_leak(self):
        source='穆青：「前镜C01这串字是纸上的。」 阿澜：“我照着，你先把药送进去。”'
        candidate=GOOD.replace('穆青（低声）：“门锁了，钥匙在你那？”','穆青：「前镜C01这串字是纸上的。」')
        errors=self.errors(candidate,source)
        self.assertFalse(any(s.startswith(('V13 ','V14 ')) for s in errors),errors)



    def test_complete_fenced_image_prompt_after_empty_label(self):
        import re
        candidate=re.sub(r'(?m)^【图像提示词】：([^\n]+)$',lambda m:'【图像提示词】：\n'+chr(96)*3+'text\n'+m.group(1)+'\n'+chr(96)*3,GOOD)
        self.assertEqual(self.errors(candidate),[])

    def test_aspect_confirmation_note_not_part_of_ratio(self):
        candidate=GOOD.replace('9:16','2.39:1').replace('【视频画幅】：2.39:1','【视频画幅】：2.39:1（用户明确指定）',1)
        self.assertEqual(self.errors(candidate),[])

    def test_equivalent_aspect_ratio(self):
        candidate=GOOD.replace('9:16','2.39:1').replace('【画幅】：2.39:1','【画幅】：239:100')
        self.assertEqual(self.errors(candidate),[])

    def test_ratio_choices_are_not_a_confirmed_value(self):
        self.assertCode('V2',GOOD.replace('【视频画幅】：9:16','【视频画幅】：9:16或16:9',1))

    def test_single_paragraph_unquoted_role_labels(self):
        source='诊所后门。穆青抱药箱。穆青：门锁了，钥匙在你那？阿澜打开门锁。阿澜：我照着，你先把药送进去。穆青走进门。'
        self.assertEqual(self.errors(GOOD,source),[])
        self.assertCode('V14',GOOD.replace('门锁了，钥匙在你那？','门打开了。'),source)



    def test_new_speaker_cannot_be_ignored(self):
        self.assertCode('V14',GOOD.replace('镜头一{','镜头一{\n丙：“这句并不属于原文！”',1))

    def test_new_unquoted_speaker_cannot_be_ignored(self):
        self.assertCode('V14',GOOD.replace('镜头一{','镜头一{\n丙：这句并不属于原文。',1))

    def test_no_dialogue_source_cannot_gain_spoken_lines(self):
        self.assertCode('V14',GOOD,'停电的诊所。两人静默送药，没有对白。')



    def test_comma_duration_explanation(self):
        candidate=GOOD.replace('【单次生成时长能力】：0–30秒之间任意时长（0到30秒可任意选择）；本场按用户指定6秒上限分段。', '【单次生成时长能力】：0–30秒之间任意时长，用户明确指定；平台选项未知。').replace('【整场时长】：18秒','【整场时长】：18秒，用户定稿锁定。')
        self.assertEqual(self.errors(candidate),[])

    def test_outcome_directive_is_not_an_actor(self):
        from scripts.check_storyboard import source_dialogue
        self.assertEqual(source_dialogue('石桥。结局锁定：双方罢手，罐不破；没有台词。'),[])

    def test_explicit_silent_source_still_rejects_added_dialogue(self):
        self.assertCode('V14',GOOD,'石桥。结局锁定：双方罢手，罐不破；没有台词。')



class NarrativeCarrierTests(unittest.TestCase):
    SILENT = """第【1】集：【锁门】
【冲突形态】：规则谜题型
【叙事承载】：动作主导
[场景]：内景·旧楼·夜
[人物]：阿宁
△ 门锁炸开，水涌入走廊，阿宁将木箱顶住门扇。
△ 她拆下窗边的铁杆，卡住折断的门闩。
△ 水压推动木箱，铁杆弯曲，阿宁踩上窗台换到高处。
【本集断章卡点】：窗外升起另一道闸门，去路被封住。（黑屏）
"""

    def test_silent_mystery_can_use_action_carrier_without_added_dialogue(self):
        fails,warns,_=validate(self.SILENT)
        self.assertFalse(any('E9 ' in item or 'E21 ' in item for item in warns),warns)
        self.assertFalse(any('E23 ' in item for item in fails),fails)

    def test_action_persistence_accepts_real_environmental_obstacle(self):
        text=self.SILENT.replace('规则谜题型','行动坚持型')+'【质疑者配角】：无\n【阻碍来源】：上涨水位堵住出口，木箱抵不住水压。\n'
        fails,_,_=validate(text)
        self.assertFalse(any('E23 ' in item for item in fails),fails)

    def test_action_persistence_still_requires_specific_obstacle(self):
        text=self.SILENT.replace('规则谜题型','行动坚持型')+'【质疑者配角】：无\n【阻碍来源】：同上\n'
        fails,_,_=validate(text)
        self.assertTrue(any('E23 ' in item for item in fails),fails)

    def test_dialogue_carrier_retains_dialogue_checks(self):
        _,warns,_=validate(self.SILENT.replace('动作主导','对白主导'))
        self.assertTrue(any('E9 ' in item for item in warns),warns)
        self.assertTrue(any('E21 ' in item for item in warns),warns)

    def test_action_carrier_does_not_bypass_opening_conflict(self):
        text=self.SILENT.replace('门锁炸开，水涌入走廊，阿宁将木箱顶住门扇。','早晨太阳升起，阿宁走在路上。')
        fails,_,_=validate(text)
        self.assertTrue(any('E4 ' in item for item in fails),fails)

    def test_storyboard_annotation_cannot_change_screenplay_carrier(self):
        text=self.SILENT.replace('【叙事承载】：动作主导\n','')+'【视觉制作包】\n【叙事承载】：动作主导\n'
        _,warns,_=validate(text,scope='episode')
        self.assertTrue(any('E9 ' in item for item in warns),warns)


if __name__=="__main__":
    unittest.main()
