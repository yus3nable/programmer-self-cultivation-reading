#!/usr/bin/env python3
"""Build the reader from editable section Markdown, never re-run OCR implicitly."""
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'website/build'
DOCS=BUILD/'docs'
PARTS={0:'书前资料',1:'第一部分 · 简介',2:'第二部分 · 静态链接',3:'第三部分 · 装载与动态链接',4:'第四部分 · 库与运行库',5:'附录与索引'}
DESCRIPTIONS={1:'从 Hello World 出发，回顾硬件、操作系统、内存与线程。',2:'从编译器的输出，到链接器如何把目标文件组合成可执行程序。',3:'从文件到进程，理解装载、地址空间、共享库与动态链接。',4:'从内存布局、程序入口和系统调用，到亲手实现一个小型运行库。'}


def metadata(body,meta):
    return '---\n'+yaml.safe_dump(meta,allow_unicode=True,sort_keys=False)+'---\n\n'+body


def linked_images(text):
    return re.sub(r'^!\[([^\]]+)\]\(([^)]+)\)$',lambda m:f'<a class="scan-link" href="{html.escape(m[2],quote=True)}" target="_blank" rel="noopener"><img src="{html.escape(m[2],quote=True)}" alt="{html.escape(m[1],quote=True)}" loading="lazy"></a>',text,flags=re.M)


def reader_body(text):
    # Keep proofreading transcriptions in the editable source, outside the reader.
    labels = {
        '复制校对文字（未运行验证）', '复制文字（已对照原图）',
        '查看图中文字（按图分组）', '查看图中文字（已校对）',
        '查看校对表格', '查看表格文字（已校对）',
    }
    pattern = r'<details\b[^>]*>\s*<summary>(.*?)</summary>.*?</details>'
    return re.sub(pattern, lambda m: '' if m[1].strip() in labels else m[0], text, flags=re.S)


def main():
    order=json.loads((ROOT/'maintenance/reading-order.json').read_text())['chapters']
    BUILD.mkdir(exist_ok=True,parents=True)
    if DOCS.exists():shutil.rmtree(DOCS)
    DOCS.mkdir()
    for name in ['chapters','front']:
        shutil.copytree(ROOT/name,DOCS/name)
    shutil.copytree(ROOT/'website/styles',DOCS/'styles')
    (DOCS/'README.md').write_text(metadata((ROOT/'README.md').read_text(),{'book':{'kind':'home'}}))
    nav=[{'书籍介绍':'README.md'},{'全书目录':'contents.md'}]
    groups={i:[] for i in PARTS}
    canonical=[]
    contents=['# 全书目录','点击章名直接进入正文；展开后可选择小节。']
    for part,name in PARTS.items():
        members=[c for c in order if c['part']==part]
        contents.append('## '+name)
        if part in DESCRIPTIONS:
            guide=['# '+name.split(' · ')[1],DESCRIPTIONS[part]]
            for c in members:
                start=f"{c['directory']}/{c['sections'][0]['path']}"
                guide.append(f"- [{c['title']}](../{start})")
            p=DOCS/f'parts/{part}.md';p.parent.mkdir(exist_ok=True)
            p.write_text(metadata('\n\n'.join(guide)+'\n',{'book':{'kind':'part','context':name.split(' · ')[0]},'chapter_start':True,'keep_in_nav':False}))
            groups[part].append({'本部分导览':f'parts/{part}.md'})
        for c in members:
            sections=[]
            start=f"{c['directory']}/{c['sections'][0]['path']}"
            contents.append(f"### [{c['title']}]({start})")
            whole=[]
            for i,s in enumerate(c['sections']):
                path=f"{c['directory']}/{s['path']}"
                body=(ROOT/path).read_text()
                canonical.append(path.replace('.md','.html'))
                first,last=s['pdf_pages']
                book={'kind':'section','context':c['title']}
                if first>=24:book['printed']=str(first-23)+('—'+str(last-23) if last>first else '')+' 页'
                if len(c['sections'])>1:book['whole']=f"{c['directory']}/chapter.html"
                meta={'book':book,'chapter_start':i==0 and len(c['sections'])>1,'keep_in_nav':True}
                (DOCS/path).write_text(metadata(linked_images(reader_body(body)),meta))
                sections.append({s['title']:path})
                if len(c['sections'])>1:contents.append(f"- [{s['title']}]({path})")
                whole.append(re.sub(r'^(#{1,5}) ',r'#\1 ',body,flags=re.M).replace('../assets/','assets/'))
            if len(sections)==1:groups[part].append({c['title']:start})
            else:
                groups[part].append({c['title']:sections})
                body='# '+c['title']+'\n\n'+'\n\n'.join(whole)
                (ROOT/c['directory']/'chapter.md').write_text(body)
                (DOCS/c['directory']/'chapter.md').write_text(metadata(linked_images(reader_body(body)),{'book':{'kind':'chapter','context':PARTS[part],'start':start.replace('.md','.html')},'search':{'exclude':True}}))
        if members:nav.append({name:groups[part]})
    (ROOT/'contents.md').write_text('\n\n'.join(contents)+'\n')
    (DOCS/'contents.md').write_text((ROOT/'contents.md').read_text())
    (ROOT/'maintenance/reading-pages.json').write_text(json.dumps({'pages':canonical},ensure_ascii=False,indent=2))
    config=yaml.safe_load((ROOT/'website/mkdocs.base.yml').read_text())
    config['plugins'][0]['search']['jieba_dict_user']=str(ROOT/'website/search-dictionary.txt')
    config.update(docs_dir='docs',site_dir='site',nav=nav,hooks=['../navigation.py'])
    config['theme']['custom_dir']='../overrides'
    (BUILD/'mkdocs.yml').write_text(yaml.safe_dump(config,allow_unicode=True,sort_keys=False))
    subprocess.run([sys.executable,'-m','mkdocs','build','--strict','-f',str(BUILD/'mkdocs.yml')],check=True)
    print(f'Built {len(canonical)} reading sections.')


if __name__=='__main__':main()
