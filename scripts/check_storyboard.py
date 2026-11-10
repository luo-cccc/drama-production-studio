"""Mechanical checks for the integrated visual package. No media or network operations.

Natural-language meaning, physical reachability and platform execution remain manual review.
V1 package/baseline, V2 values, V3 shot clock, V4 shot fields, V5 state,
V6 segment budget, V7 frames, V8 handoff, V9 combat, V10 pivotal frames,
V11 lighting, V12 fallback, V13 prompt text, V14 source speech, V15 masters,
V16 segmentation rationale/capability (1.2). V16 checks records and hard bounds,
not whether the chosen dramatic boundary or duration is artistically right.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
import re

START = "【视觉制作包】"
END = "【视觉制作包结束】"
NUMBER = r"\d+(?:\.\d+)?"
SPAN = re.compile(r"^\s*(" + NUMBER + r")\s*[–—~～\-]\s*(" + NUMBER + r")\s*(?:秒)?\s*$")
SHOT = re.compile(r"^#{3,4}[ \t]+镜头[ \t]*(S?\d+)[ \t]*[｜|][ \t]*(FORMAL_\d+)[ \t]*[｜|][ \t]*(" + NUMBER + r")[ \t]*[–—~～\-][ \t]*(" + NUMBER + r")[ \t]*秒[^\n]*$", re.M)
FRAME = re.compile(r"^#{3,4}[ \t]+关键帧[ \t]+(K\d+)[ \t]*[｜|][ \t]*(single|prep|contact|result|handoff)[ \t]*[｜|][ \t]*(S?\d+)[ \t]*[｜|][ \t]*(" + NUMBER + r")[ \t]*秒[^\n]*$", re.M)
EPS = 1e-6
MAJOR = ("资产清单", "稳定事件链", "战斗动作拍", "代价账", "战场痕迹", "时长预算与分段", "分段决策表", "分段表", "完整导演分镜", "逐镜关键帧", "视频提示词母稿", "模型适配稿", "检查证据")
EMPTY = re.compile(r"^(?:[_＿\-—.。…\s]+|待填(?:写)?|未填(?:写)?|待补(?:充)?|TODO|TBD|同上|略|无|不需要|N/?A)$", re.I)


def usable(value):
    return bool(value and not EMPTY.fullmatch(value.strip()) and not re.search(r"\[[^\]\n]*待[^\]\n]*\]", value))


def value(text, label):
    # A field may have real prose or a fenced copy block after its label. Never eat a new field.
    match = re.search(r"(?m)^[ \t]*【" + re.escape(label) + r"】[ \t]*[：:][ \t]*([^\n]*)$", text)
    if not match:
        return ""
    inline=match.group(1).strip()
    if inline:
        return inline
    tail=text[match.end():].lstrip("\r\n \t")
    if not tail or tail.startswith(('【','#','|','}')):
        return ""
    fence=re.match(r"(\x60{3,}|~{3,})(?:text)?[ \t]*\n",tail)
    if fence:
        content=tail[fence.end():]
        close=re.search(r"(?m)^"+re.escape(fence.group(1))+r"[ \t]*$",content)
        return content[:close.start()].strip() if close else ""
    stop=re.search(r"(?m)^[ \t]*(?:【|#{1,6}[ \t]|\|)",tail)
    return (tail[:stop.start()] if stop else tail).strip()


def aspect(raw):
    match=re.fullmatch(r"[ \t]*(\d+(?:\.\d+)?)[ \t]*[:：/][ \t]*(\d+(?:\.\d+)?)(?:[ \t]*[（(].*[）)]|[；;，,][^\n]*)?[ \t]*",raw)
    if not match:
        return None
    a,b=map(float,match.groups())
    return a/b if all(math.isfinite(x) and x>0 for x in (a,b)) else None


def section(text, label):
    match = re.search(r"(?m)^【" + re.escape(label) + r"】[^\n]*\n?", text)
    if not match:
        return ""
    tail = text[match.end():]
    stop = re.search(r"(?m)^【(?:" + "|".join(map(re.escape, MAJOR)) + r")】", tail)
    return tail[:stop.start()] if stop else tail


def tables(text):
    """Return table rows indexed by the actual header; do not infer meaning from cell words."""
    return [dict(zip(header, cells)) for header, cells in table_records(text)
            if len(cells) == len(header)]


def table_records(text):
    """Return each markdown table row together with its header and raw cell count.

    The normal ``tables`` helper intentionally drops malformed rows for the
    flexible narrative tables.  Strict production tables (such as the segment
    assignment table) need to see those rows so they cannot disappear from
    validation merely because a cell was missing or an ID was malformed.
    """
    records, header = [], None
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            header = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r"[\s:\-]+", c or " ") for c in cells):
            continue
        if header is None:
            header = cells
            continue
        records.append((header, cells))
    return records


def blocks(text, pattern):
    hits = list(pattern.finditer(text))
    return [(hit, text[hit.end():hits[i + 1].start() if i + 1 < len(hits) else len(text)]) for i, hit in enumerate(hits)]


def span(raw):
    match = SPAN.fullmatch(raw)
    if not match:
        return None
    start, end = map(float, match.groups())
    if not all(math.isfinite(x) for x in (start, end)) or start < 0 or end <= start:
        return None
    return start, end


def norm(text):
    return re.sub(r"\s+", "", text).strip("。；;")


def seconds(raw):
    match = re.fullmatch(r"[ \t]*(" + NUMBER + r")[ \t]*(?:秒|s)?(?:[ \t]*[（(].*[）)]|[；;，,][^\n]*)?[ \t]*", raw)
    if not match:
        return None
    result = float(match.group(1))
    return result if math.isfinite(result) and result > 0 else None


def claimed_seconds(raw):
    """Read a leading duration claim, allowing a following explanation.

    ``8.0秒 = 开锁2.0 + 放箱2.0`` claims 8.0 seconds; the rest is the
    content-budget rationale, not another duration option.
    """
    match = re.match(r"[ \t]*(" + NUMBER + r")[ \t]*(?:秒|s)?", raw or "")
    if not match:
        return None
    result = float(match.group(1))
    return result if math.isfinite(result) and result > 0 else None


def capability(raw):
    """Read a model duration capability: range, max, single option or option list."""
    text = (raw or "").strip()
    if not text or text.startswith(("未确认", "未指定", "未知", "UNKNOWN", "unknown")):
        return None
    match = re.search(r"(" + NUMBER + r")[ \t]*(?:秒|s)?[ \t]*(?:[–—~～\-]|到|至)[ \t]*(" + NUMBER + r")", text)
    if match:
        high = float(match.group(2))
        return high if math.isfinite(high) and high > 0 else None
    match = re.search(r"(?:最大|最长|不超过|上限)[ \t]*(" + NUMBER + r")[ \t]*(?:秒|s)?", text)
    if match:
        high = float(match.group(1))
        return high if math.isfinite(high) and high > 0 else None
    match = re.fullmatch(r"[ \t]*(" + NUMBER + r")[ \t]*(?:秒|s)?(?:[ \t]*[（(].*[）)]|[；;，,][^\n]*)?[ \t]*", text)
    if match:
        high = float(match.group(1))
        return high if math.isfinite(high) and high > 0 else None
    numbers = [float(item) for item in re.findall(NUMBER, text)]
    if numbers:
        high = max(numbers)
        return high if math.isfinite(high) and high > 0 else None
    return None


def segment_rationales(text):
    """Return per-FORMAL ``#### 分段依据`` blocks, stopping at the next heading."""
    pattern = re.compile(r"(?m)^#{3,4}[ \t]+分段依据[ \t]+(FORMAL_\d+)[^\n]*\n")
    hits = list(pattern.finditer(text))
    result = {}
    for index, hit in enumerate(hits):
        tail = text[hit.end():hits[index + 1].start() if index + 1 < len(hits) else len(text)]
        stop = re.search(r"(?m)^#{1,6}[ \t]+|^【(?:完整导演分镜|逐镜关键帧|视频提示词母稿|模型适配稿|检查证据|视觉制作包结束)】", tail)
        result[hit.group(1)] = (tail[:stop.start()] if stop else tail).strip()
    return result


def generic_reason(text):
    """True when a rationale uses default/equal-split/fill language without negation."""
    for match in re.finditer(r"默认|取上限|按上限|均分|平均|按[ \t]*30[ \t]*秒|凑", text or ""):
        prefix = (text or "")[max(0, match.start() - 6):match.start()]
        if any(word in prefix for word in ("不", "非", "未")):
            continue
        return True
    return False


def parse_masters(text):
    pattern = re.compile(r"^#{3,4}[ \t]+提交段[ \t]+(FORMAL_\d+)[^\n]*\n[ \t]*\n?\x60{3}(?:text)?[ \t]*\n(.*?)^\x60{3}[ \t]*$", re.M | re.S)
    return [(m.group(1), m.group(2).strip()) for m in pattern.finditer(text)]


def source_dialogue(text, quoted_only=False):
    """Read explicitly labelled speech; quoted lines may appear in one prose paragraph.

    This is not a screenplay parser. Unlabelled/ambiguous speech is reported for manual review.
    """
    events=[]
    noise={
        "时间","声效","音效","声音","场景","人物","景别","机位","构图",
        "总时长","画幅","画面内容","画面文字","道具文字","标牌文字","字幕",
        "结局锁定","事实锁定","角色设计","角色锚定","全片风格","整体描述",
        "起态","终态","禁止项","运镜及拍摄主体","特效/材质反馈","光照与归属",
        "生成风险","保底构图","关联事件链","静态状态","图像提示词","段内时刻",
        "段号","全场时码","段内时码","开场状态","段尾状态","下一段尚未开始的动作",
        "交接帧","本段起态","本段终态与承接","资产","素材来源","控制","继承","排除",
        "摄影","镜头","段","场","制作段","状态","文本","输入","TEXT","INPUT",
        "CAPABILITY","MEDIA","台词与声音","全片风格","模型适配","当前视觉版本",
        "冷色写实电影质感","光照与材质","风格","质感","风格与材质",
    }
    quoted=re.compile(r"(?<![\u4e00-\u9fffA-Za-z0-9])([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9]{0,11})(?:[（(][^）)\n]*[）)])?[ \t]*[：:][ \t]*[“\"「]([^”\"」\n]+)[”\"」]")
    quote_spans=[]
    for match in quoted.finditer(text):
        speaker,speech=match.groups()
        if speaker not in noise:
            events.append((match.start(),speaker,speech))
            quote_spans.append(match.span())
    if quoted_only:
        return [(speaker,speech) for _,speaker,speech in sorted(events)]
    lines=re.compile(r"^([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9]{0,11})(?:[（(][^）)\n]*[）)])?[ \t]*[：:][ \t]*(.+)$",re.M)
    for match in lines.finditer(text):
        if any(match.start()<=a<match.end() for a,_ in quote_spans):
            continue
        speaker,speech=match.groups()
        if speaker not in noise and not speech.startswith(('“','"','「')):
            events.append((match.start(),speaker,speech.strip()))
    # Prose input can use explicit role labels without quote/newline boundaries.
    inline=re.compile(r"(?<![\u4e00-\u9fffA-Za-z0-9])([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9]{0,11})(?:[（(][^）)\n]*[）)])?[ \t]*[：:][ \t]*([^\n。！？!?“\"「]+[。！？!?])")
    for match in inline.finditer(text):
        speaker,speech=match.groups()
        if speaker in noise or any(pos==match.start() for pos,_,_ in events):
            continue
        events.append((match.start(),speaker,speech.strip()))
    return [(speaker,speech) for _,speaker,speech in sorted(events)]


@dataclass
class Check:
    fails: list
    warns: list
    prefix: str = ""

    def fail(self, code, message):
        self.fails.append(f"{code} {self.prefix}{message}")

    def warn(self, code, message):
        self.warns.append(f"{code} {self.prefix}{message}")


def _check_package(body, check, source_text):
    version = value(body, "包版本")
    if version not in ("1.1", "1.2"):
        check.warn("V1", "输入为旧版/未标文本契约；按1.1模板整理真实已有产物，以下未解析字段不等于剧情缺陷")
    required = ("视频画幅", "全片风格", "整场时长", "源文覆盖", "场级观看任务", "范围类型", "场景类型")
    for field in required:
        if not usable(value(body, field)):
            check.fail("V2", f"【{field}】缺少实际值（空白、占位或下一行标题均不算填写）")
    cap_raw = value(body, "单次生成时长能力")
    legacy_raw = value(body, "单段时长上限")
    if version == "1.2":
        if not usable(cap_raw):
            if usable(legacy_raw):
                check.warn("V6", "1.2包使用旧字段【单段时长上限】；新交付建议写【单次生成时长能力】")
                cap_raw = legacy_raw
            else:
                check.fail("V2", "【单次生成时长能力】缺少实际值（空白、占位或下一行标题均不算填写）")
    else:
        if not usable(legacy_raw):
            check.fail("V2", "【单段时长上限】缺少实际值（空白、占位或下一行标题均不算填写）")
        cap_raw = legacy_raw
    for field in ("视觉制作基线", "资产清单", "稳定事件链", "时长预算与分段", "完整导演分镜", "逐镜关键帧", "视频提示词母稿"):
        if not re.search(r"(?m)^【" + field + r"】", body):
            check.fail("V1", f"缺少【{field}】")
    total = seconds(value(body, "整场时长"))
    if total is None:
        check.fail("V3", "【整场时长】须为正有限秒数，不能用单段时长代表整场")
    limit = capability(cap_raw)
    if limit is None:
        if cap_raw.startswith(("未确认", "未指定", "未知")):
            check.warn("V6", "单次生成时长能力未确认：当前仅是通用文字方案，不代表特定平台可直接提交")
        else:
            check.fail("V6", "单次生成时长能力格式应为正秒数/范围，或明确的未指定状态")
    elif limit > 30 + EPS:
        check.warn("V6", f"能力上限{limit:g}秒高于当前0–30秒前提；请确认模型实际能力与依据")
    if aspect(value(body, "视频画幅")) is None:
        check.fail("V2", "视频画幅须有唯一正数比例，可在括号或分号后保留来源注记")
    scene_type = value(body, "场景类型")
    if scene_type not in ("普通场", "战斗场"):
        check.fail("V9", "场景类型应明确为普通场或战斗场，不能从正文是否出现‘战斗场’猜测")
    chain_rows = tables(section(body, "稳定事件链"))
    chains = {}
    for row in chain_rows:
        cid = row.get("ID", "")
        if not re.fullmatch(r"(?:EP\d+-SC\d+-)?C\d+", cid):
            check.fail("V4", "稳定事件链表需要唯一的 Cxx 或 EPxx-SCxx-Cxx ID")
            continue
        if cid in chains:
            check.fail("V4", f"事件链重复 {cid}")
        for col in ("原文锚点", "事件事实", "起态", "结果"):
            if not usable(row.get(col, "")):
                check.fail("V4", f"事件链{cid}缺少{col}")
        chains[cid] = row
    if not chains:
        check.fail("V4", "稳定事件链必须有实际记录，只有标题不构成覆盖证据")
    shot_blocks = blocks(section(body, "完整导演分镜"), SHOT)
    if len(re.findall(r"(?m)^#{3,4}[ \t]+镜头", section(body, "完整导演分镜"))) != len(shot_blocks):
        check.fail("V3", "有镜头标题格式/数字无效，不能跳过无效镜头后声称连续")
    shots, previous, lit = {}, None, []
    for match, text in shot_blocks:
        sid, formal, a, b = match.groups()
        a, b = float(a), float(b)
        if sid in shots:
            check.fail("V3", f"镜头 ID 重复{sid}")
        if b <= a or not all(math.isfinite(x) for x in (a, b)):
            check.fail("V3", f"镜头{sid}时间区间无效")
        if (previous is None and abs(a) > EPS) or (previous and abs(a - previous['end']) > EPS):
            check.fail("V3", f"镜头{sid}时轴不连续（首镜须从0开始，后镜不得重叠或留空）")
        fields = ("关联事件链", "起态", "景别、机位", "运镜及拍摄主体", "构图", "画面内容", "台词与声音", "光照与归属", "特效/材质反馈", "生成风险", "终态")
        for label in fields:
            if not usable(value(text, label)):
                check.fail("V4", f"镜头{sid}【{label}】未填实际内容")
        refs = re.findall(r"(?:EP\d+-SC\d+-)?C\d+", value(text, "关联事件链"))
        if not refs or any(r not in chains for r in refs):
            check.fail("V4", f"镜头{sid}有缺失/未知事件链引用")
        if previous and norm(previous['closing']) != norm(value(text, '起态')):
            check.fail("V5", f"镜头{previous['id']}终态与镜头{sid}起态不一致；复用同一份世界状态")
        risk = value(text, "生成风险")
        if risk not in ("高", "低", "high", "low"):
            check.fail("V12", f"镜头{sid}风险仅接受高/低或high/low")
        if risk in ("高", "high") and not usable(value(text, "保底构图")):
            check.fail("V12", f"高风险镜头{sid}需要具体保底构图，‘无/不需要’不算")
        record = dict(id=sid, formal=formal, start=a, end=b, opening=value(text,'起态'), closing=value(text,'终态'), refs=refs)
        shots[sid] = previous = record
        lit.append(value(text, '光照与归属'))
    if not shots:
        check.fail("V3", "未检出导演镜头；使用‘#### 镜头 S01｜FORMAL_1｜0–8秒’格式")
    elif total is not None and abs(previous['end'] - total) > EPS:
        check.fail("V3", f"末镜结束{previous['end']}秒与整场{total}秒不一致")
    covered = {cid for s in shots.values() for cid in s['refs']}
    for cid in chains.keys() - covered:
        check.fail("V4", f"事件链{cid}没有镜头承载，不能声称完整覆盖")

    segments, end_prev = {}, 0.0
    segment_table = table_records(section(body, "分段表"))
    for header, cells in segment_table:
        if len(cells) != len(header):
            check.fail('V6', '分段表存在列数不一致的行，不能静默忽略')
            continue
        row = dict(zip(header, cells))
        fid = row.get('段号', '').strip()
        if not re.fullmatch(r'FORMAL_\d+', fid):
            check.fail('V6', f'分段表段号无效：{fid or "空"}')
            continue
        if fid in segments:
            check.fail('V6', f'分段表重复{fid}')
        window, local = span(row.get('全场时码','')), span(row.get('段内时码',''))
        if not window or not local:
            check.fail('V6', f'{fid}分段表的全场/段内时码无效')
            continue
        a,b=window
        if abs(a-end_prev)>EPS or abs(local[0])>EPS or abs((b-a)-local[1])>EPS:
            check.fail('V6', f'{fid}段时码不连续或段内时码未从0换算')
        if limit is not None and b-a>limit+EPS:
            check.fail('V6', f'{fid}实际段长{b-a:g}秒超过上限{limit:g}秒')
        owned = [s for s in shots.values() if s['formal']==fid]
        if not owned or abs(owned[0]['start']-a)>EPS or abs(owned[-1]['end']-b)>EPS:
            check.fail('V6', f'{fid}分段表与实际整镜分配不一致')
        if owned and (norm(owned[0]['opening'])!=norm(row.get('开场状态','')) or norm(owned[-1]['closing'])!=norm(row.get('段尾状态',''))):
            check.fail('V5', f'{fid}分段表起终态与首末镜不一致')
        segments[fid]=dict(start=a,end=b,row=row,owned=owned)
        end_prev=b
    if not segments or (total is not None and abs(end_prev-total)>EPS):
        check.fail('V6','分段表必须按整镜连续覆盖整场，单次生成时长能力不能拿整场长度比较')
    for s in shots.values():
        if s['formal'] not in segments:
            check.fail('V6',f"镜头{s['id']}所属{s['formal']}不在分段表")

    _check_segmentation(body, check, version, segments, limit)

    frames, handoffs = {}, []
    frame_blocks = blocks(section(body, "逐镜关键帧"), FRAME)
    if len(re.findall(r"(?m)^#{3,4}[ \t]+关键帧", section(body, "逐镜关键帧"))) != len(frame_blocks):
        check.fail("V7", "关键帧标题含无效角色/时刻/镜头，不能略过")
    for match,text in frame_blocks:
        kid,role,sid,t = match.groups(); t=float(t)
        if kid in frames:
            check.fail('V7',f'关键帧 ID 重复{kid}')
        s=shots.get(sid)
        if s is None or t < s['start']-EPS or t>s['end']+EPS:
            check.fail('V7',f'关键帧{kid}不在所属镜头窗口内')
        for field in ('静态状态','图像提示词'):
            if not usable(value(text,field)):
                check.fail('V7',f'{kid}缺少可独立复现的{field}，角色名/时码标签不算静图提示词')
        chain_text = value(text, '关联事件链')
        refs = re.findall(r'(?:EP\d+-SC\d+-)?C\d+', chain_text)
        if not usable(chain_text) or not refs:
            check.fail('V7', f'{kid}缺少有效的关联事件链；关键帧必须能追溯到事件事实')
        elif any(ref not in chains for ref in refs):
            check.fail('V7', f'{kid}引用未知事件链：{", ".join(ref for ref in refs if ref not in chains)}')
        frame=dict(id=kid,role=role,shot=sid,time=t,state=value(text,'静态状态'),refs=refs)
        frames[kid]=frame
        if role=='handoff':
            handoffs.append(frame)
    for sid in shots:
        if not any(k['shot']==sid for k in frames.values()):
            check.fail('V7',f'镜头{sid}没有一张实际关键帧图像提示词')
    seglist=list(segments.items())
    for (fid,seg),(nextid,nxt) in zip(seglist,seglist[1:]):
        last=seg['owned'][-1] if seg['owned'] else None
        matching=[f for f in handoffs if abs(f['time']-seg['end'])<=EPS and last and f['shot']==last['id']]
        if not matching:
            check.fail('V8',f'{fid}→{nextid}缺少归属前段末镜、时刻对齐的handoff静帧')
        elif any(norm(f['state'])!=norm(last['closing']) for f in matching):
            check.fail('V8',f'{fid}交接帧状态与末镜终态不一致')
        if norm(seg['row'].get('段尾状态',''))!=norm(nxt['row'].get('开场状态','')):
            check.fail('V8',f'{fid}→{nextid}共享世界状态漂移')

    if scene_type=='战斗场':
        _check_combat(body, check, frames, total)
        if len(shots)>1 and len(set(map(norm,lit)))<2:
            check.warn('V11','全场光照登记完全相同，需人工核对光源归属和持续光对表面的反馈')
    masters=parse_masters(section(body,'视频提示词母稿'))
    byid={}
    for fid,prompt in masters:
        if fid in byid:
            check.fail('V15',f'{fid}视频母稿重复')
        byid[fid]=prompt
        for field in ('角色锚定','全片风格','整体描述','起态','终态','禁止项'):
            if not usable(value(prompt,field)):
                check.fail('V15',f'{fid}母稿缺少独立的【{field}】：正文')
        if norm(value(prompt,'全片风格'))!=norm(value(body,'全片风格')):
            check.fail('V15',f'{fid}母稿风格正文与已确认风格不一致')
        pa,ba=aspect(value(prompt,'画幅')),aspect(value(body,'视频画幅'))
        if pa is None or ba is None or not math.isclose(pa,ba,rel_tol=1e-8):
            check.fail('V15',f'{fid}母稿画幅缺失或与已确认画幅不同')
        dur=re.search(r'(?m)^总时长[：:][ \t]*('+NUMBER+r')[ \t]*秒',prompt)
        expected=segments.get(fid)
        if not dur or (expected and abs(float(dur.group(1))-(expected['end']-expected['start']))>EPS):
            check.fail('V15',f'{fid}母稿总时长与该段实际长度不一致')
        prompt_shots=re.findall(r'^镜头[^\n{]*\{\n(.*?)^\}',prompt,re.M|re.S)
        pend=0.0
        if expected and len(prompt_shots)!=len(expected['owned']):
            check.fail('V15',f'{fid}母稿镜数不等于导演稿整镜分配')
        for idx,ptext in enumerate(prompt_shots):
            tm=re.search(r'(?m)^时间[：:][ \t]*([^\n]+)',ptext)
            ps=span(tm.group(1).rstrip('。') if tm else '')
            if not ps or abs(ps[0]-pend)>EPS:
                check.fail('V15',f'{fid}母稿镜内时码不连续或未从本段0起算')
            if ps:
                pend=ps[1]
                if expected and idx<len(expected['owned']):
                    s=expected['owned'][idx]
                    if abs(ps[0]-(s['start']-expected['start']))>EPS or abs(ps[1]-(s['end']-expected['start']))>EPS:
                        check.fail('V15',f'{fid}母稿镜时码与导演稿换算不符')
            for field in ('景别、机位','运镜及拍摄主体','构图','画面内容','声效'):
                if not re.search(r'(?m)^'+re.escape(field)+r'[：:][ \t]*\S',ptext):
                    check.fail('V15',f'{fid}母稿镜头缺少{field}实际正文')
        if expected and abs(pend-(expected['end']-expected['start']))>EPS:
            check.fail('V15',f'{fid}母稿镜头没有完整覆盖段时长')
        if expected and expected['owned'] and (norm(value(prompt,'起态'))!=norm(expected['owned'][0]['opening']) or norm(value(prompt,'终态'))!=norm(expected['owned'][-1]['closing'])):
            check.fail('V5',f'{fid}母稿起终态与导演稿不一致')
        _lint_prompt(prompt, fid, check)
    if set(byid)!=set(segments):
        check.fail('V15','每个正式段须恰有一份独立母稿；只给一个总摘要不算覆盖所有段')
    if source_text is None:
        check.warn('V14','原文逐字核对未运行：提供 --source 精确覆盖原文；结构通过不代表台词/动作保真')
    else:
        source=source_dialogue(source_text)
        explicitly_silent = bool(re.search(r"(?:^|[\n。；;])[ \t]*(?:本[场段][^，。：；\n]{0,8})?(?:没有|无)(?:台词|对白)[。！! \t\n]*$", source_text))
        if not source and not explicitly_silent:
            check.warn("V14", "源文未识别出明确标注角色的话轮；无对白或未标注内容须人工核对，不能声称自动逐字检查已覆盖")
        actual=[]
        for prompt in byid.values():
            # source_dialogue filters known production-field labels above.  Keep
            # every remaining explicit role label, including unquoted lines, so
            # a newly invented speaker cannot bypass V14 by omitting quotation
            # marks.
            actual.extend(source_dialogue(prompt))
        if Counter(source)!=Counter(actual) or source!=actual:
            check.fail('V14','视频母稿台词的说话人、逐字内容、次数或顺序与指定原文不同')


def _check_segmentation(body, check, version, segments, cap):
    """V16: 1.2 records why each segment has this duration and boundary.

    It checks presence, hard bounds and generic language only. It does not
    judge whether the chosen dramatic boundary is right.
    """
    if version != "1.2":
        return
    strategy = value(body, "分段策略")
    if not usable(strategy):
        check.fail("V16", "【分段策略】缺少实际值；1.2须说明按内容关联分段")
    elif generic_reason(strategy):
        check.warn("V16", "【分段策略】含默认/均分/取上限表述；应写具体内容关联判断")
    decision = section(body, "分段决策表")
    decision_rows = tables(decision) if decision else []
    if not decision_rows:
        check.fail("V16", "1.2须有【分段决策表】并列出候选方案")
    else:
        decision_text = " ".join(" ".join(row.values()) for row in decision_rows)
        if not re.search(r"否决|不采用|备选|放弃|淘汰|未选|落选", decision_text):
            check.warn("V16", "【分段决策表】没有记录被否决/备选的候选；需体现比较过程")
    rationales = segment_rationales(body)
    durations = []
    for fid, seg in segments.items():
        actual = seg['end'] - seg['start']
        durations.append(actual)
        row = seg['row']
        row_duration = row.get('本段时长', '')
        if usable(row_duration):
            stated_row = claimed_seconds(row_duration)
            if stated_row is None or abs(stated_row - actual) > EPS:
                check.fail("V16", f"{fid}分段表【本段时长】与全场时码{actual:g}秒不一致")
        block = rationales.get(fid, '')
        if not usable(block):
            table_reason = row.get('分段依据', '') or row.get('内容单元与关联依据', '')
            if not usable(table_reason):
                check.fail("V16", f"{fid}缺少【分段依据】；1.2须记录归组内容、时长、边界与风险")
                continue
            block = "【归组内容】：" + table_reason
        for field in ("归组内容", "本段时长", "边界状态"):
            if not usable(value(block, field)):
                check.fail("V16", f"{fid}【分段依据】缺少{field}实际内容")
        if not usable(value(block, "风险")) and not usable(value(block, "风险与返修")):
            check.fail("V16", f"{fid}【分段依据】缺少风险实际内容")
        stated = claimed_seconds(value(block, "本段时长"))
        if stated is None or abs(stated - actual) > EPS:
            check.fail("V16", f"{fid}【分段依据】本段时长与分段表{actual:g}秒不一致")
        group = value(block, "归组内容")
        if group and not re.search(r"(?:EP\d+-SC\d+-)?C\d+|S\d+", group):
            check.warn("V16", f"{fid}【归组内容】未引用事件链或镜头ID，需人工复核")
        if generic_reason(block):
            check.warn("V16", f"{fid}【分段依据】含默认/均分/凑时长表述，需人工复核")
        if cap is not None and abs(actual - cap) <= EPS and not re.search(r"内容|动作|台词|状态|边界|余韵|停顿", block):
            check.warn("V16", f"{fid}段长恰好等于能力上限，依据未见内容说明")
    if len(durations) > 1 and len({round(item, 6) for item in durations}) == 1:
        check.warn("V16", "所有段长完全相同；确认不是均分，需人工复核依据")


def _lint_prompt(text, fid, check):
    protected=re.sub(r'“[^”\n]+”|"[^"\n]+"|「[^」\n]+」|『[^』\n]+』|‘[^’\n]+’','',text)
    if re.search(r'同上|按前段|见资产表|沿用上段|上一镜|下一镜|前镜(?!子|面)|下一段|RUN_STATE|next_required|coverage_ledger|(?<![A-Za-z0-9_])FORMAL_\d+|(?<![A-Za-z0-9_])C\d+|(?<![A-Za-z0-9_])K\d+',protected):
        check.fail('V13',f'{fid}生成器正文含省略指针/内部工程标识')
    if re.search(r'(?m)^\s*(略|其余同理)\s*[。.]?\s*$|_{2,}|\[[^\]\n]*(?:填写|待填|填入)[^\]\n]*\]',protected):
        check.fail('V13',f'{fid}生成器正文残留占位说明')


def _check_combat(body,check,frames,total):
    mode=value(body,'战斗设计方式')
    if mode not in ('原创斗法设计','既定动作忠实转译'):
        check.fail('V9','战斗设计方式须区分原创设计与既定动作忠实转译')
    for field in ('双方目标','有效规则','战斗终态','数值复算'):
        if not usable(value(body,field)):
            check.fail('V9',f'战斗场缺少{field}')
    rows=tables(section(body,'战斗动作拍')); beats={}
    for row in rows:
        cid=row.get('ID',''); win=span(row.get('全场时码',''))
        if not cid or cid in beats or not win or (total and win[1]>total+EPS):
            check.fail('V9','动作拍存在重复ID/无效时间窗口')
            continue
        for col in ('行动','回应','结果'):
            if not usable(row.get(col,'')):
                check.fail('V9',f'动作拍{cid}缺少{col}')
        beats[cid]=dict(row=row,start=win[0],end=win[1],marks=row.get('标记','').split(','))
    if not beats:
        check.fail('V9','战斗场需要有行动、回应、结果和完成依赖的实际动作拍')
    for cid,b in beats.items():
        deps=re.findall(r'(?:EP\d+-SC\d+-)?C\d+',b['row'].get('完成依赖',''))
        for dep in deps:
            if dep not in beats or dep==cid or beats[dep]['end']>b['start']+EPS:
                check.fail('V9',f'{cid}完成依赖{dep}未在该拍开始前完成')
        if 'adaptation' in b['marks'] and not deps:
            check.fail('V9',f'{cid}变招拍没有已完成前因')
    pivotal=[(cid,b) for cid,b in beats.items() if 'pivotal' in b['marks']]
    for cid,b in pivotal:
        ts=[]
        for role in ('prep','contact','result'):
            candidates=[f['time'] for f in frames.values() if f['role']==role and cid in f['refs'] and b['start']-EPS<=f['time']<=b['end']+EPS]
            if not candidates:
                check.fail('V10',f'关键转折{cid}缺少窗口内的{role}图像提示词')
            else:
                ts.append(min(candidates))
        if len(ts)==3 and not ts[0]<ts[1]<ts[2]:
            check.fail('V10',f'关键转折{cid}三帧时刻必须严格递增')
    for cid,b in beats.items():
        if 'breath' in b['marks'] and any(b['start']<p['end']-EPS and p['start']<b['end']-EPS for _,p in pivotal):
            check.fail('V9',f'呼吸拍{cid}不得与关键转折重叠')
    if mode=='原创斗法设计':
        marks={m for b in beats.values() for m in b['marks']}
        if not {'pivotal','breath','adaptation'}<=marks:
            check.fail('V9','原创斗法设计缺少转折、呼吸或对手变招的实际动作拍')
        costs=tables(section(body,'代价账'))
        owners={r.get('归属','') for r in costs if usable(r.get('支出','')) and usable(r.get('后续限制',''))}
        if len(owners-{''})<2 or not any(r.get('不可逆','') in ('是','true','True') for r in costs):
            check.fail('V9','原创斗法代价账须有至少两个主体和一项不可逆支出，且写出具体限制')
        traces=tables(section(body,'战场痕迹'))
        if not traces or not any(r.get('来源拍') in beats and usable(r.get('后续影响','')) and (not pivotal or beats[r['来源拍']]['end']<=min(p['start'] for _,p in pivotal)+EPS) for r in traces):
            check.fail('V9','缺少在转折前形成并有后续影响的战场痕迹')


def validate_visual_package(text, source_text=None, required=False):
    fails,warns=[],[]; check=Check(fails,warns)
    if START not in text:
        if required or END in text:
            check.fail('V1','缺少视觉制作包起始标记')
        return fails,warns
    cursor=0; count=0; source_ranges=[]
    while True:
        start=text.find(START,cursor)
        if start<0:
            break
        end=text.find(END,start+len(START)); nested=text.find(START,start+len(START))
        if end<0 or (nested>=0 and nested<end):
            check.fail('V1','视觉制作包未闭合或发生嵌套')
            break
        count+=1; check.prefix=f'包{count}：'
        body=text[start+len(START):end]
        if not body.strip():
            check.fail('V1','视觉制作包为空')
        else:
            scoped_source = source_text
            line_range = value(body, "源文行范围")
            if source_text is not None and line_range:
                bounds = re.fullmatch(r"(\d+)[ \t]*[–—~～\-][ \t]*(\d+)", line_range)
                lines = source_text.splitlines()
                if not bounds or not (1 <= int(bounds.group(1)) <= int(bounds.group(2)) <= len(lines)):
                    check.fail("V14", "源文行范围须为源文件内从1起算的闭区间")
                    scoped_source = None
                else:
                    lo,hi=map(int,bounds.groups())
                    if any(lo <= oldhi and oldlo <= hi for oldlo,oldhi in source_ranges):
                        check.fail("V14", "多个视觉包重复声明源文行范围，需复核重复消费/重复对白")
                    source_ranges.append((lo,hi))
                    scoped_source = "\n".join(lines[lo-1:hi])
            elif source_text is not None and text.count(START) > 1:
                check.fail("V14", "多包文件逐字核对需每包填写源文行范围，不能拿全篇对白匹配每个场")
                scoped_source = None
            _check_package(body,check,scoped_source)
        cursor=end+len(END)
    if text.count(END)!=count:
        check.fail('V1','视觉制作包结束标记数量与起始/闭合不匹配')
    return fails,warns
