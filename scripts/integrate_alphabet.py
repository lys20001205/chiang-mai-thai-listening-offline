"""One-shot, hash-guarded integration into the existing pages; no user-data migration."""
from pathlib import Path
import hashlib, re
ROOT=Path(__file__).resolve().parents[1]
EXPECTED={'index.html':'c2b84de24699d1630618af55a93abd7ed7e176f8','practice.html':'bc2c72d5fe58461e1e10861ff77600765394821e','sw.js':'0cdd9b6ce2119bd170fcb3fdf69371e7eb1f4bed','README.md':'961378e34a2a0727c379b5edf8482a4d957cd686'}
def once(s,old,new):
 assert s.count(old)==1, 'Missing/ambiguous integration anchor: '+old[:100]
 return s.replace(old,new,1)
def main():
 files={}
 for name,sha in EXPECTED.items():
  b=(ROOT/name).read_bytes();actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
  assert actual==sha, f'{name} changed since review: {actual}; stop instead of overwrite'
  files[name]=b.decode('utf-8')
 s=files['index.html']
 cta='<a class="practice-feature" href="./alphabet.html"><span class="practice-icon thai" aria-hidden="true">ก</span><span class="practice-copy"><small>零基础从这里开始</small><b>先认一个字母</b><em>44 个辅音逐张教 · 元音位置 · 逐字拼回短词</em></span><span class="practice-arrow" aria-hidden="true">→</span></a>'
 s=once(s,'</section><a class="practice-feature" href="./practice.html"','</section>'+cta+'<a class="practice-feature" href="./practice.html"')
 intro='function renderReadIntro(){return `<section class="read-intro"><span class="pill">从单个字母开始 · v1.2.0</span><h3>还不认识字母？先别猜整词。</h3><p>先看一个辅音的轮廓，再学元音和上方符号。每个字母都有放大、相似字对照、观察提示和学后辨认。</p><a class="btn primary download-link" href="./alphabet.html">从第一个字母开始 →</a><details><summary>已有字母基础：展开原词块教学</summary>${renderAnchorGrid()}<p>下面的 12 关练词块，不替代单字母入门。</p><button class="btn" data-read-start>继续原 12 关词块练习</button></details></section>`}'
 s,n=re.subn(r'^function renderReadIntro\(\)\{[^\n]*$',lambda _:intro,s,count=1,flags=re.M);assert n==1
 s=once(s,'function renderSigns(){const rows=', 'function renderSigns(){if(!state.signBasicsReady)return renderReadIntro()+`<button class="btn" style="width:100%" data-sign-basics-ready>我已有字母基础，直接看 36 块标牌</button>`;const rows=')
 s=once(s,'  if(b.dataset.go){go(b.dataset.go);return}', '  if(b.hasAttribute("data-sign-basics-ready")){state.signBasicsReady=true;render();return}\n  if(b.dataset.go){go(b.dataset.go);return}')
 s=s.replace('从零认词块，再看店铺和警告牌','先学单字母，再看词块和标牌')
 s=s.replace('常在句尾；不是表示同意。','常在句尾表示礼貌；独立回答时也可表示肯定，但不证明所有交易条件已确认。')
 s=s.replace('数字；与 ข้าว（饭）只是近似拼音，泰语声调不同。','与 ข้าว（饭）在标准泰语里都是降调；注意起音送气等差别，不能只靠声调区分。')
 s=s.replace('也在菜名里；与 เก้า（九）声调不同。','也在菜名里；与 เก้า（九）都为降调，起音等特征不同。')
 s=s.replace('先听清开头的 ไม่，含义与 ได้ 相反。','作为回答可表示不能；放在动词前还可能表示没做，如 ไม่ได้ไป（没有去），与 ไปไม่ได้（去不了）不同。')
 files['index.html']=s.replace('v1.1.0','v1.2.0').replace('\\n<meta','\n<meta')
 s=files['practice.html']
 s=once(s,'<nav id="nav" aria-label="速成练习导航">','<a class="button full" href="./alphabet.html">完全不认字？先从单个字母开始 →</a><nav id="nav" aria-label="速成练习导航">')
 s=once(s,'function renderSigns(){const q=', 'function renderSigns(){if(!state.letterGatePassed&&state.stage===0)return `<section class=card><h2>先认识字母，再做标牌题</h2><p>这一页的词块题需要一点字母基础。先逐张认识辅音、元音和上方记号，再看如何把它们组成 ร้าน、ทาง、ห้าม。</p><a class="button primary full" href="./alphabet.html">从第一个字母开始 →</a><button class=full data-letter-ready>我已有字母基础，继续标牌练习</button></section>`;const q=')
 s=once(s,'if(!b)return;if(b.dataset.mode)', 'if(!b)return;if(b.hasAttribute("data-letter-ready")){state.letterGatePassed=true;render();return;}if(b.dataset.mode)')
 s=s.replace('第一步学词块；第二步去掉提示；第三步改变字重和布局。建议先完成原版 12 关。','先完成单字母与逐字拼词。这里继续练词块，再去提示、改变字重和布局。')
 s=s.replace('40 分钟：原版 12 关词块教学，再做无提示认字。25 分钟：确认地点、等待时间、往返范围。25 分钟：有本地语音时练合成听音；无语音则继续文字练习，真人听力留待核验。','50 分钟：先学单字母、元音位置，再逐字拼词。20 分钟：确认地点与等待时间。20 分钟：标牌复习；有本地语音时可辅助跟读，真人听力仍待核验。')
 s=s.replace('<a href="./index.html">原版看字教学</a>','<a href="./alphabet.html">从单个字母开始</a>')
 files['practice.html']=s.replace('v1.1.0','v1.2.0').replace('\\n<meta','\n<meta')
 s=files['sw.js'].replace("shell-v6","shell-v7")
 s=once(s,"const MANIFEST =", "const ALPHABET = new URL('./alphabet.html', ROOT).href;\nconst MANIFEST =")
 s=once(s,'[ROOT, SHELL, PRACTICE, MANIFEST]','[ROOT, SHELL, PRACTICE, ALPHABET, MANIFEST]')
 files['sw.js']=s
 s=files['README.md'].replace('\\n','\n').replace('**当前版本：v1.1.0**','**当前版本：v1.2.0**')
 release='''## v1.2.0 从单个字母开始

- 新增 `alphabet.html`：44 个辅音分别讲解；常用 20 个分五组优先学，每组四个。
- 放大字形、传统名称、起音、相似字对照、观察提示；可选手指描形不冒充笔顺／手写识别。
- 15 个元音部件、四个声调记号、两个其他符号，解释前后上下的位置。
- 学过才出题；测验隐藏范字，错题不计为首次认出。10 个短词逐字讲解和组字。
- 主页新增入口，原看字页与速成标牌页默认先显示字母教学入口，保留已有基础的跳过按钮。
- 新进度键 `chiangmai-alphabet-v1`；旧课程／练习键不变。三页统一 v1.2.0，缓存 v7。
- 修正原词卡“九／米饭声调不同”、礼貌词和 `ไม่ได้` 的过度简化提示。
- 资料链接在字母课中；音频仍是设备合成，真人音质和真实设备飞行模式未验收。

测试：`python tests/test_alphabet.py`、`python tests/test_alphabet_integration.py`、原练习及缓存测试。

'''
 s=once(s,'## v1.1.0 前端更新',release+'## v1.1.0 前端更新')
 s=s.replace('原卡片中的相关错误提示仍未直接改写。','v1.2.0 已修正原卡片中上述三项简化提示。')
 files['README.md']=s
 for name,s in files.items():(ROOT/name).write_text(s,encoding='utf-8')
 for name in ['index.html','practice.html','alphabet.html']:
  assert 'v1.2.0' in (ROOT/name).read_text()
 print('INTEGRATION_APPLIED: index.html practice.html sw.js README.md; legacy progress unchanged')
if __name__=='__main__':main()
