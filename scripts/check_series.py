#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""drama-production-studio 全剧台账与视觉连续性机检

用法:
    python check_series.py <台账.md> [--episodes 80] [--script-dir 剧本目录]
    python check_series.py --self-test
    （Windows 用 python；macOS / Linux 用 python3）

台账为 markdown 表格文件（templates/project-ledger-template.md 格式），必备四类账及可选视觉账：
    伏笔账 / 人物账 / 道具账 / 世界观规则账 / 视觉制作账

总集数 --episodes 决定付费墙区间：标准档 60/80/100 集；长档（约3分钟/集）30/40/50 集
（1 长档集 ≈ 2 标准集，墙集数减半，见 references/story/series-structure.md §二/§四）。

检查项:
    S1  伏笔"拟收"超期: 状态含 埋/养/未收 且 当前集>拟收+3      WARN
    S2  伏笔废置: 状态"废"但正文未给废弃说明列               WARN
    S3  死人开口: 人物账状态含 死/殒/失踪 但剧本目录中其后集数该角色有对白行  FAIL
    S4  人物无档案: 剧本目录出现【角色】名册外人名            WARN(需--script-dir)
    S5  断章缺失扫描: --script-dir 时逐集查【本集断章卡点】    FAIL(缺)
    S6  付费墙落位: 三档总集数下墙集区间内无"墙"标记行         WARN
    S7  台账必备四表齐全                                      FAIL(缺表)
    S8  反转手段轮换: 反转手段矩阵表相邻3集内复用同一[A-I]标签  WARN
    S9  视觉制作基线与资产账字段缺失（含单次生成时长能力/分段策略）                              WARN（存在视觉制作账时）
    S10 稳定事件链 ID 同场重复、为空或占位                                  WARN（存在视觉制作账时）
    S11 斗法扩展未登记目标/规则/代价/痕迹/复算                    WARN（存在斗法扩展时）
        (A身份压制/B铁证如山/C盟友倒戈/D降维制裁/E诛心破防/F纯粹武力
         /G情感剥夺/H舆论社死/I借刀自噬; G/H/I为女频文戏新增)
S9~S11 仅检查文本字段、占位和重复，不代表语义正确、图片已读或平台媒体可用。
退出码: 0=通过, 1=FAIL, 2=用法错误
"""
import argparse
import re
import sys
import pathlib

WALL_RANGES = {60: [(8, 11), (21, 24), (41, 44)], 80: [(10, 15), (28, 32), (55, 58)], 100: [(13, 19), (35, 40), (68, 73)],
               # 长档（约 3 分钟/集）：集数减半，墙集区间同步折算
               30: [(4, 6), (10, 12), (20, 22)], 40: [(5, 8), (14, 16), (27, 29)], 50: [(7, 10), (17, 20), (34, 37)]}
SUPPORTED_EPISODES = frozenset(WALL_RANGES)
TABLE_KEYS = {"伏笔": "伏笔账", "人物": "人物账", "道具": "道具账", "规则": "世界观规则账"}


def _rows(text, section_kw):
    """取某账小节后的 markdown 表格数据行"""
    m = re.search(r"^#+[^\n]*?" + section_kw + r"[^\n]*\n(.*?)(?=^#+\s|\Z)", text, re.S | re.M)
    if not m:
        return None
    rows = []
    for line in m.group(1).splitlines():
        s = line.strip()
        if s.startswith("|") and not re.match(r"^\|[\s\-:|]+\|$", s):
            cells = [c.strip() for c in s.strip("|").split("|")]
            rows.append(cells)
    return rows[1:] if rows else []  # 去表头


def _reversal_entries(text):
    """解析'反转手段轮换矩阵'表, 返回按集数升序的 [(ep:int, tag:str)]。"""
    m = re.search(r"#+.*?反转手段轮换矩阵.*?\n(.*?)(?=\n#+\s|\Z)", text, re.S)
    out = []
    if not m:
        return out
    for line in m.group(1).splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|$", s):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells or "集数" in cells[0]:
            continue
        em = re.search(r"(\d+)", cells[0])
        tm = re.search(r"\[([A-I])\]", s)
        if em and tm:
            out.append((int(em.group(1)), tm.group(1)))
    out.sort()
    return out


_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+([^\r\n]+)", re.M)
_SCOPE_HEADERS = ("场次范围", "适用集场", "集场范围", "集场", "场次", "场景ID", "场景编号", "场号")
_ID_HEADERS = ("ID", "编号", "链ID", "链号", "事件链ID", "稳定事件链ID")
_EP_HEADERS = ("集数", "集次", "集", "EP")


def _script_body(text):
    """S3~S5 只读取正式剧本；下游导演记录和提示词不能补写剧本事实。"""
    labels = r"视觉制作包|视觉导演记录|完整导演分镜|视频提示词母稿"
    boundary = re.search(
        r"^[ \t]*(?:【(?:" + labels + r")】|#{1,6}[ \t]+[^\r\n]*(?:" + labels + r"))",
        text, re.M)
    return text[:boundary.start()] if boundary else text


def _visual_ledger(text):
    """取得视觉账及其子节，不借用相邻同级章节的字段。None 表示旧台账。"""
    headings = list(_HEADING_RE.finditer(text))
    for i, heading in enumerate(headings):
        if "视觉制作账" in heading.group(2):
            end = next((m.start() for m in headings[i + 1:]
                        if len(m.group(1)) <= len(heading.group(1))), len(text))
            return text[heading.end():end]
    return None


def _cells(line):
    body = line.strip()[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [cell.strip().replace(r"\|", "|") for cell in re.split(r"(?<!\\)\|", body)]


def _visual_tables(body):
    """保留每张表的实际表头、全部数据行和所属标题（用于场次范围）。"""
    lines = body.splitlines()
    titles, tables = [], []
    i = 0
    while i < len(lines):
        heading = _HEADING_RE.match(lines[i])
        if heading:
            level = len(heading.group(1))
            titles = [(depth, title) for depth, title in titles if depth < level]
            titles.append((level, heading.group(2)))
        if lines[i].strip().startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
            divider = _cells(lines[i + 1])
            if divider and all(re.fullmatch(r":?-+:?", cell.replace(" ", "")) for cell in divider):
                headers, rows = _cells(lines[i]), []
                i += 2
                while i < len(lines) and lines[i].strip().startswith("|"):
                    rows.append(_cells(lines[i]))
                    i += 1
                tables.append((tuple(title for _, title in titles), headers, rows))
                continue
        i += 1
    return tables


def _header_key(value):
    return re.sub(r"[\s*`【】\[\]/／_()（）:：-]", "", value).casefold()


def _column(headers, aliases):
    names = {_header_key(name) for name in aliases}
    return next((i for i, header in enumerate(headers) if _header_key(header) in names), None)


def _unfilled(value, names=()):
    """仅识别空白、明确占位和字段名自填，不推断填写内容的语义。"""
    plain = re.sub(r"[*`\u200b\ufeff]", "", value).strip()
    if not plain or re.fullmatch(r"[\s_＿—–.。…?？/／:：|｜-]+", plain):
        return True
    if re.search(r"[_＿]{2,}", plain):
        return True
    if re.fullmatch(r"(?:TODO|TBD|N/?A|NULL|NONE)", plain, re.I):
        return True
    if re.match(r"^[【\[（(<]?(?:待填写|待填|待补充|待补|待定|未填写|未填|未确认|待确认|占位|TODO|TBD)(?:$|[：:\s（()）\]】>])", plain, re.I):
        return True
    return _header_key(plain) in {_header_key(name) for name in names}


def _cell(row, column):
    return row[column] if column is not None and column < len(row) else ""


def _check_fields(warns, code, section, headers, rows, fields):
    for label, aliases in fields.items():
        column = _column(headers, aliases)
        if column is None:
            warns.append(f"{code} {section}缺少{label}列")
            continue
        for number, row in enumerate(rows, 1):
            if _unfilled(_cell(row, column), aliases):
                warns.append(f"{code} {section}第{number}行{label}为空、占位或仅含字段名")


def _heading_scope(titles):
    title = " ".join(titles)
    episode = re.findall(r"(?<![A-Za-z])EP[ \t]*\d+|第[ \t]*[零〇一二三四五六七八九十百\d]+[ \t]*集", title, re.I)
    scene = re.findall(r"(?<![A-Za-z])SC[ \t]*\d+|第[ \t]*[零〇一二三四五六七八九十百\d]+[ \t]*场", title, re.I)
    return (episode[-1] if episode else "", scene[-1] if scene else "")


def _scope_key(episode, scene):
    def clean(value):
        value = re.sub(r"\s|[*`\u200b\ufeff]", "", value).casefold()
        value = re.sub(r"第(\d+)集", r"ep\1", value)
        value = re.sub(r"第(\d+)场", r"sc\1", value)
        return re.sub(r"\d+", lambda match: str(int(match.group())), value)

    episode, scene = clean(episode), clean(scene)
    # EP01-SC01、第1集第1场、分开的集数/场次列得到同一个键。
    combined = re.fullmatch(r"(ep\d+)[_./:：·-]*(.+)", scene)
    if combined and not re.search(r"ep\d+", combined.group(2)):
        episode, scene = combined.groups()
    if episode.isdecimal():
        episode = "ep" + episode
    if scene.isdecimal():
        scene = "sc" + scene
    return episode, scene


def _is_dead_status(value):
    """识别明确的死亡/失踪/退场状态，避免把“未死亡”误判为死亡。"""
    state = re.sub(r"\s+", "", value or "")
    if not state:
        return False
    if re.search(r"(?:未|不|尚未|仍然?活|存活|生还|在世)", state):
        return False
    return bool(re.search(r"(?:死亡|已死|殒命|殒落|失踪|阵亡|下线|退场)", state))


def _table_kind(titles):
    # 子级斗法表不能因祖先标题含“稳定事件链”而被当成链表。
    for title in reversed(titles):
        for kind, aliases in (
            ("asset", ("资产状态", "资产账", "资产清单")),
            ("chain", ("稳定事件链",)),
            ("combat", ("斗法扩展",)),
        ):
            if any(alias in title for alias in aliases):
                return kind
    return None


def _validate_visual_ledger(body, warns):
    """S9~S11 只核对文本结构；不认证语义、图片已读或平台媒体可用。"""
    def field_values(label):
        # 空白只允许在本行；不能用 \s* 吞掉下一字段前的换行。
        return re.findall(r"^[ \t]*(?:【" + label + r"】|" + label + r")[ \t]*[：:][ \t]*([^\r\n]*)", body, re.M)

    for label in ("视频画幅", "全片风格", "当前视觉版本"):
        values = field_values(label)
        if not values or any(_unfilled(value, (label,)) for value in values):
            warns.append(f"S9 视觉制作账缺少{label}实际值（为空、占位或仅含字段名）")
    capability = field_values("单次生成时长能力")
    if not capability or any(_unfilled(value, ("单次生成时长能力",)) for value in capability):
        warns.append("S9 视觉制作账缺少单次生成时长能力实际值（为空、占位或仅含字段名）")
    strategy = field_values("分段策略")
    if not strategy or any(_unfilled(value, ("分段策略",)) for value in strategy):
        warns.append("S9 视觉制作账缺少分段策略实际值（为空、占位或仅含字段名）")

    tables = _visual_tables(body)
    asset_tables = [table for table in tables if _table_kind(table[0]) == "asset"]
    if not any(rows for _, _, rows in asset_tables):
        warns.append("S9 视觉制作账没有资产状态记录")
    asset_fields = {
        "资产": ("资产", "资产名称", "角色/场景/道具"),
        "稳定锚点": ("稳定锚点", "稳定身份锚点"),
        "当前状态": ("当前状态",),
        "持有/所在": ("持有/所在", "持有者/所在", "持有者/位置"),
        "适用集场": ("适用集场", "场次范围", "适用范围"),
        "提示词": ("提示词", "图片提示词"),
    }
    for _, headers, rows in asset_tables:
        _check_fields(warns, "S9", "资产状态", headers, rows, asset_fields)

    chain_tables = [table for table in tables if _table_kind(table[0]) == "chain"]
    if not any(rows for _, _, rows in chain_tables):
        warns.append("S10 视觉制作账没有稳定事件链记录")
    seen = set()
    for titles, headers, rows in chain_tables:
        id_column = _column(headers, _ID_HEADERS)
        if id_column is None:
            warns.append("S10 稳定事件链缺少ID列")
            continue
        scope_column = _column(headers, _SCOPE_HEADERS)
        ep_column = _column(headers, _EP_HEADERS)
        heading_ep, heading_scene = _heading_scope(titles)
        for number, row in enumerate(rows, 1):
            cid = _cell(row, id_column)
            if _unfilled(cid, _ID_HEADERS):
                warns.append(f"S10 稳定事件链第{number}行ID为空、占位或仅含字段名")
                continue
            scope = _cell(row, scope_column) if scope_column is not None else heading_scene
            episode = _cell(row, ep_column) if ep_column is not None else heading_ep
            if scope_column is not None and _unfilled(scope, _SCOPE_HEADERS):
                warns.append(f"S10 稳定事件链{cid}第{number}行场次范围为空或占位")
                continue
            if ep_column is not None and _unfilled(episode, _EP_HEADERS):
                warns.append(f"S10 稳定事件链{cid}第{number}行集数为空或占位")
                continue
            key = (_scope_key(episode, scope), re.sub(r"[*`]", "", cid).strip().casefold())
            if key in seen:
                location = " / ".join(part for part in (episode, scope) if part) or "未标场次"
                warns.append(f"S10 稳定事件链 ID 重复: {cid}（场次范围：{location}）")
            seen.add(key)

    if any("斗法扩展" in heading.group(2) for heading in _HEADING_RE.finditer(body)):
        combat_tables = [table for table in tables if _table_kind(table[0]) == "combat"]
        if not any(rows for _, _, rows in combat_tables):
            warns.append("S11 斗法扩展没有填写场次记录")
        fields = {
            "场次": _SCOPE_HEADERS,
            "双方目标": ("双方目标", "目标"),
            "有效规则": ("有效规则", "规则"),
            "不可逆代价": ("不可逆代价", "代价"),
            "战场痕迹": ("战场痕迹", "痕迹"),
            "数值复算": ("数值复算", "复算"),
        }
        for _, headers, rows in combat_tables:
            _check_fields(warns, "S11", "斗法扩展", headers, rows, fields)


def validate_ledger(text, total_eps=80, scripts=None):
    fails, warns = [], []
    for kw in TABLE_KEYS.values():
        if not re.search(r"#+.*?" + kw, text):
            fails.append(f"S7 台账缺「{kw}」表")
        elif not _rows(text, kw):
            fails.append(f"S7 台账「{kw}」缺少可解析的数据表或数据行")
    episodes_supported = total_eps in SUPPORTED_EPISODES
    if not episodes_supported:
        fails.append(f"S6 不支持总集数 {total_eps}；请使用 {', '.join(map(str, sorted(SUPPORTED_EPISODES)))}")
    mm = re.search(r"当前集[:：]\s*(\d+)", text)
    cur = int(mm.group(1)) if mm else (max(scripts) if scripts else total_eps)

    # S1/S2 伏笔账
    fb = _rows(text, "伏笔") or []
    for r in fb:
        if len(r) < 5:
            continue
        plan, state = r[3], r[4].strip()
        try:
            pn = int(plan)
        except ValueError:
            warns.append(f"S1 伏笔「{r[1][:12]}」拟收集数非数字: {plan}"); continue
        is_open = ("埋" in state or "养" in state or "未收" in state) and not state.startswith("收")
        if is_open and cur > pn + 3:
            warns.append(f"S1 伏笔「{r[1][:12]}」超期未收(拟收{pn}集,现{cur}集,状态{state})")
        if state.startswith("废") and (len(r) < 6 or not r[5]):
            warns.append(f"S2 伏笔「{r[1][:12]}」标废但未写原因")

    script_bodies = {ep: _script_body(body) for ep, body in (scripts or {}).items()}

    # S3 死人开口
    dead = {}
    for r in (_rows(text, "人物") or []):
        if len(r) < 3:
            continue
        if _is_dead_status(r[2]):
            mm2 = re.search(r"(\d+)", r[4] if len(r) > 4 else r[2])
            dead[r[0].strip()] = int(mm2.group(1)) if mm2 else cur
    if scripts:
        for ep in sorted(scripts):
            for name, at in dead.items():
                if ep > at:
                    body = script_bodies[ep]
                    if re.search(r"^" + re.escape(name[:4]) + r"(\(|（|[:：])", body, re.M):
                        fails.append(f"S3 「{name}」第{at}集后状态死亡/失踪，但第{ep}集有对白")

    # S4 名册外角色
    roster = {r[0].strip() for r in (_rows(text, "人物") or []) if len(r) > 0}
    if scripts and roster:
        NOISE = {"第", "场景", "人物", "本集", "所属", "黄金", "情绪", "备注", "接上",
                 "声音", "旁白", "画外音", "内心独白", "镜头", "字幕", "提示", "音效"}
        for ep in sorted(scripts):
            seen = set()
            for m2 in re.finditer(r"^([\u4e00-\u9fa5A-Za-z0-9]{1,8})(?:（[^）]*）|\([^)]*\))?\s*[:：]", script_bodies[ep], re.M):
                nm = m2.group(1)
                if nm in NOISE or nm in seen:
                    continue
                seen.add(nm)
                if nm not in roster:
                    warns.append(f"S4 第{ep}集台词角色「{nm}」不在人物账名册")

    # S5 断章缺失
    if scripts:
        for ep in sorted(scripts):
            if not re.search(r"【本集断章卡点】|\[本集断章", script_bodies[ep]):
                fails.append(f"S5 第{ep}集缺【本集断章卡点】")

    # S6 付费墙标记
    if episodes_supported:
        ranges = WALL_RANGES[total_eps]
        marks = []
        for m in re.finditer(r"墙[^\n]{0,12}?(\d+)\s*[-~至]?\s*(\d+)?", text):
            marks.append(int(m.group(1)))
            if m.group(2):
                marks.append(int(m.group(2)))
        for lo, hi in ranges:
            if not any(lo <= x <= hi for x in marks):
                warns.append(f"S6 未见付费墙落在第{lo}~{hi}集区间(三档各需一条'X级墙 第N集'标记)")

    # S8 反转手段轮换: 相邻3集内(集数差<=2)复用同一[A-I]标签 → WARN
    rev = _reversal_entries(text)
    for i in range(len(rev)):
        e1, t1 = rev[i]
        for j in range(i + 1, len(rev)):
            e2, t2 = rev[j]
            if e2 - e1 > 2:
                break
            if t1 == t2:
                warns.append(f"S8 反转手段重复: EP{e1}与EP{e2}相邻3集内复用[{t1}]")
    # S9~S11：视觉制作账为可选扩展；旧台账保持兼容。
    visual = _visual_ledger(text)
    if visual is not None:
        _validate_visual_ledger(visual, warns)
    return fails, warns, cur


LEDGER_GOOD = """# 台账：demo 项目
当前集: 30

## 伏笔账
| ID | 内容 | 埋于 | 拟收 | 状态 | 备注 |
|---|---|---|---|---|---|
| FB-01 | 旧怀表 | 3 | 28 | 收 | 已当众展开 |
| FB-02 | 神秘来电 | 12 | 31 | 养 | 反派内讧线 |

## 人物账
| 角色 | 首出 | 状态 | 关系 | 变动集 | 备注 |
|---|---|---|---|---|---|
| 林辰 | 1 | 存活 | 主角 | 30 | |
| 陈峰 | 1 | 死亡 | 敌 | 25 | 第25集坠楼 |

## 道具账
| 道具 | 持有 | 状态 | 变动集 |
|---|---|---|---|
| 玄铁令 | 林辰 | 怀中 | 12 |

## 世界观规则账
| 规则 | 确立集 | 引用集 | 违反 |
|---|---|---|---|
| 龙王令只一次 | 12 | 25 | 否 |

付费墙落位: 一级墙 第12集(中点转换) / 二级墙 第30集 / 三级墙 第56集
"""

EP_GOOD = """第【3】集
[场景]：内景·大堂
△ 巴掌甩到半空停住。
陈峰：签了它。
林辰：你确定？
【本集断章卡点】：门外齐跪，"参见殿下"喊到一半——（黑屏）
"""
EP_BAD = """第【4】集
[场景]：内景·大堂
△ 对峙。
林辰：滚。
陈峰：好。
"""


def self_test():
    ok = 1
    scripts = {3: EP_GOOD, 4: EP_BAD}
    f, w, cur = validate_ledger(LEDGER_GOOD, 80, scripts)
    if not any("S5" in x and "第4集" in x for x in f):
        print("FAIL self-test: 第4集缺断章应报 S5:", f); ok = 0
    if any("S1" in x for x in w):
        print("FAIL self-test: 未超期不应报 S1:", w); ok = 0
    scripts2 = {3: EP_GOOD, 4: EP_BAD, 30: "第【30】集\n[场景]：内景·大宅\n△ 对峙。\n陈峰（阴笑）：我回来了。\n【本集断章卡点】：灯灭。（黑屏）\n"}
    f2, _, _ = validate_ledger(LEDGER_GOOD, 80, scripts2)
    if not any("S3" in x for x in f2):
        print("FAIL self-test: 死人开口应报 S3:", f2); ok = 0
    if any("S5" in x and "第30集" in x for x in f2):
        print("FAIL self-test: 第30集有断章不该报 S5"); ok = 0
    f3, _, _ = validate_ledger("空台账", 80)
    if len([x for x in f3 if x.startswith("S7")]) < 4:
        print("FAIL self-test: 空台账应报 4 条 S7:", f3); ok = 0

    led2 = LEDGER_GOOD.replace("| FB-02 | 神秘来电 | 12 | 31 | 养 | 反派内讧线 |",
                               "| FB-02 | 神秘来电 | 12 | 8 | 已埋 | 反派内讧线 |")
    f4, w4, _ = validate_ledger(led2, 80, scripts)
    if not any("S1" in x and "FB" not in x or "神秘来电" in x for x in w4):
        print("FAIL self-test: 状态'已埋'超期应报 S1:", w4); ok = 0
    ep_noise = {5: "第【5】集\n[场景]：内景\n△ 拍桌。\n声音：轰鸣。\n林辰：谁？\n陈峰：我。\n【本集断章卡点】：黑屏（黑屏）\n"}
    _, w5, _ = validate_ledger(LEDGER_GOOD, 80, ep_noise)
    if any("「声音」" in x for x in w5):
        print("FAIL self-test: '声音:' 旁白不应报 S4:", w5); ok = 0

    ep_dup = {9: "第【9】集\n[场景]：内景\n[人物]：甲\n△ 对峙。\n陌生人：你是谁？\n陌生人：说话！\n陌生人：再不说我动手了。\n林辰：别急。\n【本集断章卡点】：黑屏（黑屏）\n"}
    _, w6, _ = validate_ledger(LEDGER_GOOD, 80, ep_dup)
    dup_cnt = sum(1 for x in w6 if "「陌生人」" in x)
    if dup_cnt != 1:
        print(f"FAIL self-test: S4 同名角色应只报 1 次，实得 {dup_cnt}", w6); ok = 0

    led_long = LEDGER_GOOD.replace(
        "付费墙落位: 一级墙 第12集(中点转换) / 二级墙 第30集 / 三级墙 第56集",
        "付费墙落位: 一级墙 第6集(中点转换) / 二级墙 第15集 / 三级墙 第28集")
    _, w7, _ = validate_ledger(led_long, 40)
    if any("S6" in x for x in w7):
        print("FAIL self-test: 长档 40 集墙落位不应报 S6:", w7); ok = 0
    _, w8, _ = validate_ledger(LEDGER_GOOD, 40)
    if not any("S6" in x for x in w8):
        print("FAIL self-test: 标准档墙集数按长档 40 集核对应报 S6:", w8); ok = 0

    led_s8_bad = LEDGER_GOOD + """
## 反转手段轮换矩阵
| 集数 | 反转标签 | 核心冲突事件 | 攻守方 | 爽点结算 |
|---|---|---|---|---|
| EP1 | [F] 纯粹武力 | 破门踹翻打手 | 主角 vs 反派 | 肢体压制 |
| EP2 | [A] 身份压制 | 亮出真实身份 | 亲信 vs 反派家族 | 阶层逆转 |
| EP3 | [F] 纯粹武力 | 再次武力控场 | 主角 vs 反派 | 爽点重复 |
"""
    _, w_s8b, _ = validate_ledger(led_s8_bad, 80)
    if not any(x.startswith("S8") and "EP1与EP3" in x and "[F]" in x for x in w_s8b):
        print("FAIL self-test: 相邻3集复用[F]应报 S8:", w_s8b); ok = 0
    led_s8_good = LEDGER_GOOD + """
## 反转手段轮换矩阵
| 集数 | 反转标签 | 核心冲突事件 | 攻守方 | 爽点结算 |
|---|---|---|---|---|
| EP1 | [F] 纯粹武力 | 破门踹翻打手 | 主角 vs 反派 | 肢体压制 |
| EP2 | [A] 身份压制 | 亮出真实身份 | 亲信 vs 反派家族 | 阶层逆转 |
| EP3 | [B] 铁证如山 | 亮出原始黑账 | 主角 vs 前妻 | 道德崩塌 |
| EP4 | [C] 盟友倒戈 | 核心靠山反水 | 大伯 vs 反派 | 现场倒戈 |
"""
    _, w_s8g, _ = validate_ledger(led_s8_good, 80)
    if any(x.startswith("S8") for x in w_s8g):
        print("FAIL self-test: 正常轮换不应报 S8:", w_s8g); ok = 0

    print("[+] self-test PASSED" if ok else "[-] self-test FAILED")
    return 0 if ok else 1


def main():
    # Windows 管道和重定向同样输出 UTF-8；StringIO 等测试流没有 reconfigure。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ledger", nargs="?", help="UTF-8 Markdown 台账")
    parser.add_argument("--episodes", type=int, default=80, help="总集数（正整数）")
    parser.add_argument("--script-dir", type=pathlib.Path, help="剧本目录")
    parser.add_argument("--self-test", action="store_true", help="运行内置回归检查")
    try:
        args = parser.parse_args()
    except SystemExit as error:
        return error.code
    if args.self_test:
        return self_test()
    if not args.ledger:
        print(__doc__); return 2
    if args.episodes not in SUPPORTED_EPISODES:
        print("[-] --episodes 只支持 " + ", ".join(map(str, sorted(SUPPORTED_EPISODES)))); return 2
    try:
        led = pathlib.Path(args.ledger).read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        print(f"[-] 找不到台账文件: {args.ledger}"); return 2
    except IsADirectoryError:
        print(f"[-] 路径是目录，不是台账文件: {args.ledger}"); return 2
    except UnicodeDecodeError:
        print(f"[-] 台账不是 UTF-8 文本: {args.ledger}"); return 2
    except OSError as error:
        print(f"[-] 无法读取台账文件: {args.ledger}（{error}）"); return 2
    scripts = None
    if args.script_dir is not None:
        directory = args.script_dir
        if not directory.is_dir():
            print(f"[-] 剧本目录不存在: {directory}"); return 2
        scripts = {}
        try:
            paths = sorted(directory.glob("*.md"))
        except OSError as error:
            print(f"[-] 无法读取剧本目录: {directory}（{error}）"); return 2
        for script_path in paths:
            if not (re.search(r"集|EP", script_path.stem, re.I) or re.fullmatch(r"\d+", script_path.stem)):
                continue
            match = re.search(r"(\d+)", script_path.stem)
            if match:
                try:
                    scripts[int(match.group(1))] = script_path.read_text(encoding="utf-8-sig")
                except (UnicodeDecodeError, OSError) as error:
                    print(f"[-] 无法读取剧本: {script_path}（{error}）"); return 2
    fails, warns, cur = validate_ledger(led, args.episodes, scripts)
    print(f"== {args.ledger}  总集数={args.episodes} 当前集={cur} ==")
    for message in fails:
        print("[-] FAIL:", message)
    for message in warns:
        print("[!] WARN:", message)
    if _visual_ledger(led) is not None:
        print("说明: 视觉检查仅覆盖文本结构与登记完整性；语义、图片读取和媒体可用性需另行复核。")
    if fails:
        print("结果: FAILED"); return 1
    print("结果: PASSED" + ("（含 WARN）" if warns else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
