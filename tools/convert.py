#!/usr/bin/env python3
"""Convert local Vision OCR and scan regions into traceable Markdown sections.

OCR is a draft transcription. Diagrams, tabular data and unreviewed code retain
their scan pixels; recognized text is supplementary, not trusted source code.
"""
import argparse
import collections
import difflib
import hashlib
import html
import json
import re
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / 'tmp'
ASSETS = []
AUDIT = []
WARNINGS = []
CORRECTIONS = json.loads((ROOT / 'maintenance/text-corrections.json').read_text()) if (ROOT / 'maintenance/text-corrections.json').exists() else {}


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def compact(text):
    return re.sub(r'\s+', '', text)


def escape(text):
    return re.sub(r'([\\*_`\[\]#])', r'\\\1', html.escape(text, quote=False))


def join(a, b):
    if a and b and re.search(r'[A-Za-z0-9]$', a) and re.match(r'[A-Za-z0-9]', b):
        return a + ' ' + b
    return a + b


def rect_union(rects):
    return [min(r[0] for r in rects), min(r[1] for r in rects), max(r[2] for r in rects), max(r[3] for r in rects)]


def inside(row, box):
    r = row['bbox']
    return box[0] <= (r[0]+r[2])/2 <= box[2] and box[1] <= (r[1]+r[3])/2 <= box[3]


def intersect(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def cjk(text):
    return len(re.findall(r'[\u3400-\u9fff]', text))


def get_rows(n):
    data = json.loads((TMP / f'ocr/p{n:04d}.json').read_text())
    rows = []
    for i, line in enumerate(sorted(data['lines'], key=lambda l: ((l['bbox'][1]+l['bbox'][3])/2, l['bbox'][0]))):
        box = line['bbox']
        # Printed pages have repeated running heads above 8% and footers below 91%.
        if n >= 4 and (box[3] < data['height']*.078 or box[1] > data['height']*.907):
            continue
        line = {**line, 'source_ids': [i], 'parts': [line]}
        line['text'] = CORRECTIONS.get(str(n), {}).get(line['text'], line['text'])
        same = next((r for r in reversed(rows[-6:]) if abs((r['bbox'][1]+r['bbox'][3]-box[1]-box[3])/2) < 9 and (r['bbox'][2] < box[0]+4 or box[2] < r['bbox'][0]+4)), None)
        if same:
            same['parts'].append(line['parts'][0])
            same['parts'].sort(key=lambda p:p['bbox'][0])
            same['text'] = ' '.join(CORRECTIONS.get(str(n), {}).get(p['text'],p['text']) for p in same['parts'])
            same['source_ids'] += line['source_ids']
            same['bbox'] = rect_union([same['bbox'], box])
        else:
            rows.append(line)
    rows.sort(key=lambda r: (r['bbox'][1], r['bbox'][0]))
    for i, row in enumerate(rows):
        row['id'] = i
        row['page'] = n
        row['height'] = row['bbox'][3]-row['bbox'][1]
    return data, rows


def save_region(n, box, directory, kind, label, serial):
    image = Image.open(TMP / f'scans/p{n:04d}.png').convert('RGB')
    box = [max(0, int(box[0]-5)), max(0, int(box[1]-5)), min(image.width, int(box[2]+6)), min(image.height, int(box[3]+6))]
    path = ROOT / directory / 'assets' / f'p{n:04d}-{kind}-{serial}.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    image.crop(tuple(box)).save(path, optimize=True)
    ASSETS.append({'path': path.relative_to(ROOT).as_posix(), 'pdf_page': n, 'printed_page': n-23 if n >=24 else None,
                   'bbox': box, 'kind': kind, 'label': label, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return f'![{label}](../assets/{path.name})'


def table_regions(n, w, h):
    gray = cv2.imread(str(TMP / f'scans/p{n:04d}.png'), cv2.IMREAD_GRAYSCALE)
    ink = cv2.threshold(gray, 175, 255, cv2.THRESH_BINARY_INV)[1]
    horizontal = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((1, 70), np.uint8))
    vertical = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((35, 1), np.uint8))
    # Connect ruling intersections, including slightly skewed scans.
    grid = cv2.dilate(horizontal | vertical, np.ones((5,5), np.uint8))
    contours = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    regions = []
    for contour in contours:
        x,y,bw,bh = cv2.boundingRect(contour)
        if bw < w*.25 or bh < 55 or y < h*.08 or y+bh > h*.91:
            continue
        # A table must have vertical and horizontal rules, not just a code separator.
        if np.count_nonzero(vertical[y:y+bh, x:x+bw]) < bh*1.4:
            continue
        regions.append([x,y,x+bw,y+bh])
    return regions


def events(n, directory, headings):
    data, rows = get_rows(n)
    w,h = data['width'], data['height']
    taken = set()
    output = []
    regions = []

    def add(kind, text, selected, box=None):
        box = box or rect_union([r['bbox'] for r in selected])
        taken.update(r['id'] for r in selected)
        output.append({'kind':kind,'text':text,'bbox':box,'page':n,'row_ids':[r['id'] for r in selected]})

    # Mark known headings before region detection so they cannot become code.
    for title in headings:
        number = re.match(r'([\dA]+(?:\.\d+)+)', title)
        number = number[1] if number else None
        candidates = [r for r in rows if r['id'] not in taken and (
            (number and re.match(r'^'+re.escape(number)+r'(?![\d.])', r['text'])) or
            (not number and compact(title)==compact(r['text'])))]
        if candidates:
            row = max(candidates, key=lambda r:r['height'])
            if row['height'] >= 22 or len(row['text']) < len(title)+8:
                add('heading', title, [row])

    # Figure captions are below the graphic. Long full-width prose bounds its top.
    for cap in rows:
        if cap['id'] in taken or not re.match(r'^图\s*\d+\s*[-－—.]\s*\d+',cap['text']) or cjk(cap['text'])>28:
            continue
        prior = [r for r in rows if r['bbox'][3]<cap['bbox'][1]-5 and (
            (cjk(r['text'])>=16 and r['bbox'][2]-r['bbox'][0]>w*.48) or (cjk(r['text'])>=3 and r['height']>=21 and r['bbox'][0]<w*.225 and not re.match(r'^[图表]',r['text'])) or
            any(r['id'] in e['row_ids'] and e['kind']=='heading' for e in output))]
        lower = max([r['bbox'][3] for r in prior] + [h*.07]) + 8
        blockers = [r[3] for r in regions if r[3] < cap['bbox'][1]]
        if blockers: lower=max(lower,max(blockers)+10)
        if cap['bbox'][1]-lower<45:
            continue
        box=[w*.09,lower,w*.94,cap['bbox'][1]-5]
        if any(intersect(box,b) for b in regions):continue
        selected=[r for r in rows if r['id'] not in taken and inside(r,box)]
        text=save_region(n,box,directory,'figure',cap['text'],len(regions)+1)
        text+='\n\n<p class="image-caption">'+html.escape(cap['text'])+'</p>'
        if selected:
            text+='\n\n<details markdown="1"><summary>查看图中文字</summary>\n\n'+ '\n\n'.join(escape(r['text']) for r in selected)+'\n\n</details>'
        add('figure',text,selected+[cap],box)
        regions.append(box)

    for i, box in enumerate(table_regions(n,w,h)):
        if any(intersect(box,b) for b in regions):continue
        selected = [r for r in rows if r['id'] not in taken and inside(r,box)]
        if selected and all(r['text'] in ['博文编辑','俞甲子'] for r in selected):
            continue
        if not selected or any(e['kind']=='heading' and intersect(e['bbox'],box) for e in output):
            continue
        cap = next((r for r in rows if r['id'] not in taken and re.match(r'^表\s*\d+[-－—.]\d+',r['text']) and 0<=box[1]-r['bbox'][3]<40), None)
        label = cap['text'] if cap else (f'原书第 {n-23} 页表格' if n>=24 else f'PDF 第 {n} 页表格')
        text = save_region(n,box,directory,'table',label,i+1)
        text += '\n\n<details markdown="1"><summary>查看表格文字</summary>\n\n' + '\n\n'.join(escape(r['text']) for r in selected) + '\n\n</details>'
        add('table',text,selected+([cap] if cap else []),box)
        regions.append(box)

    # Code and command output use scan crops by default to retain every operator.
    groups=[]; group=[]
    for row in rows:
        t=row['text']; code=(cjk(t)/max(len(t),1)<.18) or (cjk(t)<8 and bool(re.match(r'^(?:\$\s|#include|typedef\b|struct\b)',t)))
        code=code and row['id'] not in taken and not re.match(r'^[图表清]\s*\d|^\d+(?:\.\d+)+\s',t)
        if code and (not group or row['bbox'][1]-group[-1]['bbox'][3]<75):
            group.append(row)
        else:
            if group:groups.append(group)
            group=[row] if code else []
    if group:groups.append(group)
    for group in groups:
        if len(group)<2 and not re.match(r'^(?:\$\s|#include|typedef\b)',group[0]['text']):continue
        box=rect_union([r['bbox'] for r in group])
        before=[r['bbox'][3] for r in rows if r['bbox'][3]<box[1]-1 and r not in group]
        after=[r['bbox'][1] for r in rows if r['bbox'][1]>box[3]+1 and r not in group]
        box[1]=max(box[1]-20,max(before)+4 if before else h*.085)
        box[3]=min(box[3]+22,min(after)-4 if after else h*.905)
        box[0]=w*.09;box[2]=w*.94
        if any(intersect(box,b) for b in regions):continue
        cap=next((r for r in rows if r['id'] not in taken and re.match(r'^清单',r['text']) and 0<=box[1]-r['bbox'][3]<35),None)
        label=cap['text'] if cap else (f'原书第 {n-23} 页代码与命令' if n>=24 else f'PDF 第 {n} 页代码与命令')
        raw=[]
        left=min(r['bbox'][0] for r in group)
        for row in group:
            text='';end=left
            for part in sorted(row['parts'],key=lambda p:p['bbox'][0]):
                text+=' '*max(0,round((part['bbox'][0]-end)/9))+part['text'];end=part['bbox'][2]
            raw.append(text.rstrip())
        text=save_region(n,box,directory,'code',label,len(regions)+1)
        text+='\n\n<details markdown="1"><summary>复制 OCR 文字（符号请对照原图）</summary>\n\n```text\n'+'\n'.join(raw).replace('```','~~~')+'\n```\n\n</details>'
        add('code',text,group+([cap] if cap else []),box)
        regions.append(box)

    for row in rows:
        if row['id'] not in taken:
            add('text',row['text'],[row])
    output.sort(key=lambda e:(e['bbox'][1],e['bbox'][0]))
    AUDIT.append({'pdf_page':n,'body_ocr_rows':len(rows),'represented_rows':len(taken),'characters':sum(len(r['text']) for r in rows),
                  'regions':len(regions),'source':'Apple Vision OCR, not line-by-line proofreading'})
    return output


def render(items):
    result=[]; paragraph=''; previous=None
    def flush():
        nonlocal paragraph
        if paragraph:result.append(paragraph);paragraph=''
    for event in items:
        kind=event['kind'];t=event['text'];box=event['bbox']
        if kind!='text':
            flush()
            if kind=='heading':
                number=re.match(r'[\dA]+(?:\.\d+)+',t)
                depth=2 if not number else min(4,number[0].count('.')+1)
                result.append('#'*depth+' '+t)
            else:result.append(t)
            previous=None;continue
        if re.match(r'^[•●▪◆◇口]\s*',t):
            flush();paragraph='- '+escape(re.sub(r'^[•●▪◆◇口]\s*','',t));previous=event;continue
        if t.startswith('—') or t in ['博文编辑','俞甲子']:
            flush();result.append('**'+escape(t)+'**');previous=None;continue
        newpara=previous is None or (event['page']==previous['page'] and (
            box[1]-previous['bbox'][3]>13 or box[0]-previous['bbox'][0]>22 or
            (previous['bbox'][2]<800 and re.search(r'[。！？：；”]$',previous['text']))))
        if previous is not None and paragraph.startswith('- '):
            newpara=bool(re.search(r'[。！？]$',previous['text']))
        if newpara:flush()
        paragraph=join(paragraph,escape(t))
        previous=event
    flush()
    return '\n\n'.join(result)+'\n'


def build(sample=False):
    toc=json.loads((TMP/'toc.json').read_text())
    titles_by_page=collections.defaultdict(list)
    for level,title,p in toc:
        if re.match(r'[\dA]+\.',title):titles_by_page[p].append(title)
    chapters=[]
    chapter_toc=[(i,t,p) for i,(level,t,p) in enumerate(toc) if level==2 and re.match(r'第',t)]
    part=1
    for pos,(idx,title,start) in enumerate(chapter_toc):
        number=pos+1
        part=1 if number==1 else 2 if number<=5 else 3 if number<=9 else 4
        boundary=chapter_toc[pos+1][2] if pos+1<len(chapter_toc) else 472
        part_page=next((p for l,t,p in toc if l==1 and '部分' in t and start<p<boundary),None)
        end=(part_page or boundary)-1
        sections=[(title,p) for l,title,p in toc[idx+1:] if l==3 and re.match(rf'^{number}\.\d+(?![\d.])',title)]
        if sample and number!=3:continue
        directory=f'chapters/{number:02d}'
        chapter={'id':str(number),'kind':'chapter','number':number,'title':re.sub(r'^第一章','第 1 章',title),'part':part,'directory':directory,'cover_page':start,'sections':[]}
        chapter_events=[]
        for n in range(sections[0][1],end+1):
            chapter_events.extend(events(n,directory,titles_by_page[n]))
        cuts=[]
        for title,page in sections:
            num=re.match(r'\d+\.\d+',title)[0]
            candidates=[(i,e) for i,e in enumerate(chapter_events) if e['kind']=='heading' and e['text']==title and abs(e['page']-page)<=1]
            if candidates:cut=candidates[0][0]
            else:
                cut=next((i for i,e in enumerate(chapter_events) if e['page']>=page),len(chapter_events))
                WARNINGS.append({'type':'heading_boundary_fallback','title':title,'pdf_page':page})
            cuts.append((cut,title,page,num))
        for i,(cut,title,p,num) in enumerate(cuts):
            selected=chapter_events[cut:cuts[i+1][0] if i+1<len(cuts) else len(chapter_events)]
            if selected and selected[0]['kind']=='heading' and selected[0]['text']==title:selected=selected[1:]
            path=f'sections/{num}.md'
            target=ROOT/directory/path;target.parent.mkdir(parents=True,exist_ok=True)
            text='# '+title+'\n\n'+render(selected)
            target.write_text(text)
            last=max([e['page'] for e in selected]+[p])
            chapter['sections'].append({'title':title,'path':path,'pdf_pages':[p,last],'printed_pages':[p-23,last-23]})
        chapters.append(chapter)
    if not sample:
        front=[('访谈','作者访谈录',4,7),('序言一','序言一',8,9),('序言二','序言二',10,10),('序言三','序言三',11,12),('导读','导读',13,14)]
        front_chapters=[]
        for ident,title,first,last in front:
            directory=f'front/{ident}'
            es=[e for n in range(first,last+1) for e in events(n,directory,[])]
            if es and compact(es[0]['text'])==compact(title):es=es[1:]
            p=ROOT/directory/'sections/introduction.md';p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('# '+title+'\n\n'+render(es))
            front_chapters.append({'id':ident,'kind':'front','title':title,'part':0,'directory':directory,'sections':[{'title':title,'path':'sections/introduction.md','pdf_pages':[first,last]}]})
        chapters=front_chapters+chapters
        directory='front/第四部分导言'
        es=events(305,directory,[])
        p=ROOT/directory/'sections/introduction.md';p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('# 库与运行库：导言\n\n'+render(es))
        intro={'id':'part-4-intro','kind':'introduction','title':'库与运行库：导言','part':4,'directory':directory,'sections':[{'title':'库与运行库：导言','path':'sections/introduction.md','pdf_pages':[305,305]}]}
        chapters.insert(next(i for i,c in enumerate(chapters) if c['id']=='10'),intro)
        appendix={'id':'A','kind':'appendix','title':'附录 A','part':5,'directory':'chapters/A','cover_page':472,'sections':[]}
        es=[e for n in range(473,480) for e in events(n,'chapters/A',titles_by_page[n])]
        ats=[(t,p) for level,t,p in toc if level==2 and t.startswith('A.')]
        for i,(title,p) in enumerate(ats):
            start=next((j for j,e in enumerate(es) if e['kind']=='heading' and e['text']==title),next(j for j,e in enumerate(es) if e['page']>=p))
            end=next((j for j,e in enumerate(es) if e['kind']=='heading' and i+1<len(ats) and e['text']==ats[i+1][0]),len(es))
            selected=es[start:end]
            if selected and selected[0]['kind']=='heading':selected=selected[1:]
            path=f'sections/{title.split()[0]}.md';out=ROOT/'chapters/A'/path;out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text('# '+title+'\n\n'+render(selected))
            appendix['sections'].append({'title':title,'path':path,'pdf_pages':[p,max([e['page'] for e in selected]+[p])]})
        chapters.append(appendix)
        # Preserve the original index in reading order; columns remain separate.
        parts=[]
        for n in range(480,483):
            data,rows=get_rows(n)
            columns=[[r for r in rows if r['bbox'][0]<data['width']*.5],[r for r in rows if r['bbox'][0]>=data['width']*.5]]
            parts.extend('\n\n'.join(escape(r['text']) for r in col) for col in columns)
            AUDIT.append({'pdf_page':n,'body_ocr_rows':len(rows),'represented_rows':len(rows),'kind':'index'})
        p=ROOT/'front/索引/sections/introduction.md';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('# 索引\n\n'+'\n\n'.join(parts))
        chapters.append({'id':'index','kind':'index','title':'索引','part':5,'directory':'front/索引','sections':[{'title':'索引','path':'sections/introduction.md','pdf_pages':[480,482]}]})
    dump(ROOT/'maintenance/reading-order.json',{'title':'程序员的自我修养','subtitle':'链接、装载与库','chapters':chapters})
    dump(ROOT/'maintenance/asset-map.json',ASSETS)
    dump(ROOT/'maintenance/reports/conversion.json',{'scope':'全量 OCR 与版面提取；未经逐句人工校对','pages':AUDIT,'warnings':WARNINGS,'asset_count':len(ASSETS)})
    print(json.dumps({'chapters':len(chapters),'reading_sections':sum(len(c['sections']) for c in chapters),'assets':len(ASSETS),'warnings':WARNINGS},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--sample',action='store_true')
    parser.add_argument('--overwrite-drafts',action='store_true',help='Explicitly replace existing section Markdown with OCR drafts')
    args=parser.parse_args()
    if (ROOT/'maintenance/reading-order.json').exists() and not args.overwrite_drafts:
        parser.error('Section sources exist. Back up your edits, then pass --overwrite-drafts only to regenerate OCR drafts.')
    build(args.sample)
