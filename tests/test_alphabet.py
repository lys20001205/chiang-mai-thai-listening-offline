"""Offline, in-memory Chromium tests. Speech/storage are explicit mocks; no real voice claim."""
from pathlib import Path
import json, os, shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'alphabet.html').read_text(encoding='utf-8')
STORAGE="""entries=>{const m=new Map(Object.entries(entries));Object.defineProperty(window,'localStorage',{value:{getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,String(v))},configurable:true});}"""
NO_VOICE="Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[],cancel:()=>{},addEventListener:()=>{}},configurable:true})"
MOCK="""window.SpeechSynthesisUtterance=function(t){this.text=t;};window.spoken=[];Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[{lang:'th-TH',localService:true,name:'MOCK'}],cancel:()=>{},addEventListener:()=>{},speak:u=>{window.spoken.push(u.text);if(window.failSpeech)u.onerror({error:'synthesis-failed'});}},configurable:true});"""
def main():
 count=0;errors=[]
 def check(ok,msg):
  nonlocal count
  assert ok,msg
  count+=1
 with sync_playwright() as p:
  exe=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
  browser=p.chromium.launch(**({'executable_path':exe} if exe else {}),args=['--no-sandbox'])
  def page(speech=NO_VOICE,entries=None):
   q=browser.new_page(viewport={'width':390,'height':844});q.on('pageerror',lambda e:errors.append(str(e)))
   q.evaluate(STORAGE,entries or {});q.evaluate(speech);q.set_content(HTML);return q
  a=page(entries={'chiangmai-ear-v1':'ORIGINAL','chiangmai-practice-v1':'PRACTICE'})
  check(a.evaluate('LETTERS.length===44 && new Set(LETTERS.map(x=>x.id)).size===44'),'44 unique letters')
  check(a.evaluate('VOWELS.length===15 && MARKS.length===6'),'15 vowel parts and 6 marks')
  check(a.evaluate('WORDS.every(w=>w.parts.join(\"\")===w.th && w.explain.length===w.parts.length && w.parts.every(id=>BY[id]))'),'Decompositions complete and in actual spelling order')
  a.locator('[data-deck="0"]').first.click();check(a.locator('.glyph').inner_text()=='ก','Starts with single letter not word')
  check(a.locator('[data-say]').is_disabled(),'No voice disables speaking')
  check(a.evaluate('progress.mastered.length===0'),'Viewing does not pass quiz')
  a.locator('[data-quiz]').click();check(a.evaluate('state.page==="learn"'),'No untaught distractors in one-letter quiz')
  for i in range(3):a.locator('[data-next-letter]').click()
  a.locator('[data-next-letter]').click();check(a.evaluate('state.page==="quiz"'),'Learn then quiz')
  target=a.evaluate('state.quiz.ids[state.quiz.i]');wrong=a.evaluate('state.quiz.options.find(x=>x!==state.quiz.ids[state.quiz.i])')
  a.locator(f'[data-answer="{wrong}"]').click();check(a.evaluate('state.quiz.score===0 && progress.mastered.length===0'),'Wrong response not mastered')
  a.evaluate('answer',target);check(a.evaluate('state.quiz.score===0'),'Cannot click second answer to claim first-try pass')
  a.locator('[data-quiz-next]').click()
  for _ in range(3):
   target=a.evaluate('state.quiz.ids[state.quiz.i]');check(a.locator('h2').inner_text().find(target)<0,'Prompt does not reveal target glyph')
   a.locator(f'[data-answer="{target}"]').click();a.locator('[data-quiz-next]').click()
  check(a.evaluate('state.quiz.score===3'),'First group correct scoring')
  for item in a.evaluate('ITEMS.map(x=>x.id)'):
   a.evaluate('openItem',item)
   check(a.locator('.glyph').inner_text()==a.evaluate('glyph',item),f'Renders single item {item}')
  for group in [5,6]:
   a.evaluate('openDeck',group);a.evaluate('startQuiz()')
   while a.evaluate('state.quiz.i<state.quiz.ids.length'):
    target=a.evaluate('state.quiz.ids[state.quiz.i]')
    check(target not in a.locator('h2').inner_text(),'Symbol not leaked by prompt')
    a.locator(f'[data-answer="{target}"]').click();a.locator('[data-quiz-next]').click()
  for i in range(a.evaluate('WORDS.length')):
   a.evaluate('(i)=>{state.wi=i;resetBuild();go("build")}',i)
   check(a.locator('.word').count()==1,'Explanation before building')
   a.locator('[data-build-start]').click();check(a.locator('.word').count()==0,'Word hidden in building')
   a.locator('[data-piece="0"]').click()
   for j in range(1,a.evaluate('WORDS[state.wi].parts.length')):a.locator(f'[data-piece="{j}"]').click()
   check(a.locator('.slot').inner_text()==a.evaluate('WORDS[state.wi].th'),f'Build complete {i}')
  a.evaluate('state.wi=8;resetBuild();go("build");startBuild()')
  a.locator('[data-piece="1"]').click();a.locator('[data-piece="0"]').click();a.locator('[data-piece="2"]').click()
  check(a.locator('.slot').inner_text()=='ออก','Repeated letters accepted in either identical-token order')
  a.evaluate('state.wi=0;resetBuild();go("build");startBuild()')
  a.locator('[data-piece="1"]').click();check(a.evaluate('state.placed.length===0'),'Wrong piece does not advance')
  a.locator('[data-build-hint]').click();check(a.locator('.word').count()==1 and a.evaluate('state.buildHint'),'Hint marked explicitly')
  for width in [240,320,390,768]:
   a.set_viewport_size({'width':width,'height':850})
   for route in ['start','reference','symbols','build','sources']:
    a.evaluate('go',route)
    check(a.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'No overflow {width}/{route}')
   a.evaluate('openItem','ื');check(a.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),f'No overflow {width}/letter')
  check(a.evaluate('localStorage.getItem("chiangmai-ear-v1")==="ORIGINAL" && localStorage.getItem("chiangmai-practice-v1")==="PRACTICE"'),'Other progress untouched')
  saved=a.evaluate('localStorage.getItem(STORE)');b=page(entries={'chiangmai-alphabet-v1':saved});check(b.evaluate('progress.built.length===10'),'Progress restored')
  b.close();b=page(entries={'chiangmai-alphabet-v1':'{broken'});check('无法保存' in b.locator('#storage').inner_text(),'Malformed storage handled');b.close()
  b=page(MOCK);b.evaluate('openItem','ก');b.locator('[data-say]').click();check(b.evaluate('spoken[0]==="กอ ไก่"'),'Letter name spoken not mislabeled as phoneme')
  b.evaluate('go("build")');b.locator('[data-say]').click();check(b.evaluate('spoken.at(-1)==="กา"'),'Whole word spoken separately')
  b.evaluate('window.failSpeech=true');b.locator('[data-say]').click();check('播放失败' in b.locator('#audio').inner_text(),'Speech failure surfaced')
  b.close();a.set_viewport_size({'width':390,'height':844});a.evaluate('openItem','ป')
  a.screenshot(path=str(ROOT.parent/'alphabet-mobile.png'),full_page=True)
  a.locator('summary').click();a.locator('[data-trace]').click();check(a.locator('canvas').is_visible(),'Optional tracing visible')
  check(not errors,'No JS errors: '+str(errors));browser.close()
 print(json.dumps({'status':'PASS','assertions':count,'scope':'Chromium in-memory DOM; mock speech/storage. Real iPhone audio and SW navigation NOT_RUN'},ensure_ascii=False))
if __name__=='__main__':main()
