"""In-memory DOM regression. Storage and speech are explicit mocks; no network or phone-audio claim."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'practice.html').read_text(encoding='utf-8')
SPEECH_MOCK = """
window.__speechError=false;
window.SpeechSynthesisUtterance=function(text){this.text=text;};
Object.defineProperty(window,'speechSynthesis',{value:{
 getVoices:()=>[{lang:'th-TH',localService:true,name:'TEST MOCK, NOT A REAL VOICE'}],
 addEventListener:()=>{},cancel:()=>{},
 speak:u=>setTimeout(()=>window.__speechError?u.onerror?.({error:'synthesis-failed'}):u.onend?.(),10)
},configurable:true});
"""
NO_VOICE = "Object.defineProperty(window,'speechSynthesis',{value:{getVoices:()=>[],addEventListener:()=>{},cancel:()=>{}},configurable:true});"
STORAGE_MOCK = """entries=>{const m=new Map(Object.entries(entries));Object.defineProperty(window,'localStorage',{value:{getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k)},configurable:true});}"""


def main():
    assertions = 0
    errors = []
    def check(condition, message):
        nonlocal assertions
        assert condition, message
        assertions += 1

    with sync_playwright() as p:
        executable = os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
        browser = p.chromium.launch(**({'executable_path': executable} if executable else {}), args=['--no-sandbox'])
        def open_page(speech=NO_VOICE, storage=None):
            page = browser.new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.evaluate(STORAGE_MOCK, storage or {})
            page.evaluate(speech)
            page.set_content(HTML)
            return page

        page = open_page(storage={'chiangmai-ear-v1': '{"learned":["1-2"],"sentinel":"keep"}'})
        page.evaluate("setPage('money')")
        check(page.get_by_role('button', name='听音练习', exact=True).is_disabled(), 'No voice disables audio')
        check('未检测到本地泰语语音' in page.locator('#audio-status').inner_text(), 'No-voice notice')
        nums = page.evaluate('NUMBERS.map(x=>x.n)')
        for n in nums:
            for unit in ['person', 'total', 'unknown']:
                page.evaluate("([n,unit])=>{const x=NUMBERS.find(x=>x.n===n);state.q={id:`${n}-${unit}`,n,unit,th:(unit==='person'?'คนละ':unit==='total'?'ทั้งหมด':'')+x.th+'บาท',numberRoman:x.rom};state.result=null;render();}", [n, unit])
                page.locator('[name=amount]').fill(f'{n:,}')
                page.locator('[name=unit]').select_option(unit)
                if unit == 'unknown':
                    page.locator('[name=unknown]').check()
                else:
                    page.locator('[name=total]').fill(str(n * 2 if unit == 'person' else n))
                page.get_by_role('button', name='核对答案', exact=True).click()
                check(page.evaluate('state.result.correct'), f'Money {n}/{unit}')
        check(page.evaluate("parseAmount('๑,๕๐๐')===1500"), 'Thai digits')
        check(page.evaluate("Number.isNaN(parseAmount('1,50'))"), 'Reject invalid grouping')
        check(page.evaluate("Number.isNaN(parseAmount('-150'))"), 'Reject negative prices')
        page.evaluate("state.q={id:'wrong-unit',n:50,unit:'person',th:'คนละห้าสิบบาท',numberRoman:'hâa sìp'};state.result=null;render();")
        page.locator('[name=amount]').fill('50')
        page.locator('[name=unit]').select_option('total')
        page.locator('[name=total]').fill('50')
        page.get_by_role('button', name='核对答案', exact=True).click()
        check(not page.evaluate('state.result.correct'), 'Right number with wrong unit fails')
        for kind, data in [('negative', 'NEGATIVE'), ('confirm', 'CONFIRM'), ('signs', 'SIGNS')]:
            page.evaluate('setPage', kind)
            for i in range(page.evaluate(f'{data}.length')):
                page.evaluate(f"i=>{{state.q={{...{data}[i],id:{data}[i].id||{data}[i].th,layout:0}};state.result=null;state.stage=1;render();}}", i)
                choice = page.evaluate('state.q.options.indexOf(state.q.answer||state.q.zh)')
                page.locator(f'[data-answer="{choice}"]').click()
                check(page.evaluate('state.result.correct'), f'{kind} correct answer {i}')
        for width in [240, 320, 390, 768]:
            page.set_viewport_size({'width': width, 'height': 850})
            for route in ['plan', 'money', 'negative', 'confirm', 'signs', 'dialect', 'sources']:
                page.evaluate('setPage', route)
                check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), f'No overflow {width}/{route}')
        check(page.evaluate("JSON.parse(localStorage.getItem('chiangmai-ear-v1'))") == {'learned': ['1-2'], 'sentinel': 'keep'}, 'Original record preserved in mock store')
        page.evaluate("setPage('money')")
        page.get_by_role('button', name='没听清／先确认，不猜金额').click()
        check(page.evaluate("progress.attempts.at(-1).mode==='assisted'"), 'Assistance separate from listening')
        check(not page.evaluate('progress.attempts.at(-1).correct'), 'Assistance not independent recognition')
        page.evaluate("setPage('signs')")
        page.get_by_role('button', name='去掉提示', exact=True).click()
        check(page.locator('.chunk').count() == 0, 'No chunk hints in test')
        check(page.locator('.sign-prefix').count() == 0, 'No prefix underline')
        page.set_viewport_size({'width':390,'height':844})
        page.screenshot(path=str(ROOT.parent / 'practice-mobile.png'), full_page=True)
        page.close()

        ap = open_page(SPEECH_MOCK)
        ap.evaluate("setPage('negative')")
        ap.get_by_role('button', name='听音练习', exact=True).click()
        check(ap.locator('#app [lang=th]').count() == 0, 'Audio Thai hidden before answer')
        ap.locator('[data-answer="0"]').click()
        check(ap.evaluate('state.result===null'), 'Cannot score before playback ends')
        ap.get_by_role('button', name='播放标准泰语', exact=True).click()
        ap.wait_for_function('state.heard===true')
        i = ap.evaluate('state.q.options.indexOf(state.q.answer)')
        ap.locator(f'[data-answer="{i}"]').click()
        check(ap.evaluate("progress.attempts.at(-1).mode==='audio'"), 'Audio mode separately scored')
        ap.get_by_role('button', name='下一题', exact=True).click()
        ap.evaluate('window.__speechError=true')
        ap.get_by_role('button', name='播放标准泰语', exact=True).click()
        ap.wait_for_function("state.audioError!==''")
        check(not ap.evaluate('state.heard'), 'Playback error clears heard flag')
        ap.locator('[data-answer="0"]').click()
        check(ap.evaluate('state.result===null'), 'Playback failure cannot score listening')
        ap.get_by_role('button', name='文字练习', exact=True).click()
        check(ap.evaluate("state.mode==='text' && !state.heard"), 'Switch to text starts fresh')
        ap.close()
        corrupt = open_page(storage={'chiangmai-practice-v1':'{broken'})
        check(corrupt.locator('#app').inner_text() != '', 'Corrupt stored JSON does not crash')
        corrupt.close()
        denied = browser.new_page()
        denied.on('pageerror', lambda e: errors.append(str(e)))
        denied.set_content(HTML)
        check(denied.locator('#app').inner_text() != '', 'Opaque-origin storage failure does not crash')
        check('无法保存' in denied.locator('#storage-status').inner_text(), 'Storage failure disclosed')
        denied.close()
        browser.close()
    check(not errors, 'No browser errors: ' + repr(errors))
    print(json.dumps({'status':'PASS','assertions':assertions,'money_cases':len(nums)*3,
                      'method':'Chromium in-memory DOM; storage and speech mocked',
                      'not_tested':['HTTP/file navigation blocked by host policy','real phone pronunciation','real browser service worker offline navigation'],
                      'browser_errors':errors},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
