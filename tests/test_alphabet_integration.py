"""Check integration with existing app in a memory DOM; no network/audio assertion."""
from pathlib import Path
import json,os,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
 errors=[];checks=0
 def check(ok,msg):
  nonlocal checks
  assert ok,msg
  checks+=1
 with sync_playwright() as p:
  exe=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium')
  b=p.chromium.launch(**({'executable_path':exe} if exe else {}),args=['--no-sandbox'])
  for file in ['index.html','practice.html']:
   q=b.new_page(viewport={'width':390,'height':844});q.on('pageerror',lambda e:errors.append(str(e)))
   q.evaluate("Object.defineProperty(window,'localStorage',{value:{getItem:()=>null,setItem:()=>{}},configurable:true});")
   q.set_content((ROOT/file).read_text())
   check(q.locator('a[href="./alphabet.html"]').count()>0,file+' homepage entry')
   if file=='index.html':
    check(q.evaluate('all.length===150 && signs.length===36 && readingSteps.length===12'),'Legacy content retained')
    q.evaluate('go("signs")');check(q.locator('.sign-board').count()==0,'Original novice entry does not show a word quiz')
    check(q.locator('a[href="./alphabet.html"]').count()>0,'Original novice entry links letter teaching')
    q.locator('[data-sign-basics-ready]').click();check(q.locator('.sign-board').count()==1,'Advanced skip preserves original signs')
    q.evaluate('go("lessons")');check(q.locator('[data-lesson]').count()==8,'Eight legacy lessons')
    q.evaluate('startQuiz("text")');check(q.locator('[data-choice]').count()==4,'Legacy quiz intact')
   else:
    q.evaluate('setPage("signs")');check(q.locator('.board').count()==0,'Practice novice entry does not start with words')
    q.locator('[data-letter-ready]').click();check(q.locator('.board').count()==1,'Practice skip preserves stages')
    q.evaluate('setPage("money")');check(q.locator('#money-form').count()==1,'Money form intact')
   check('v1.3.0' in q.locator('body').inner_text(),file+' version')
   check(q.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),file+' mobile no overflow')
   q.close()
  check(not errors,'No JS errors: '+str(errors));b.close()
 print(json.dumps({'status':'PASS','assertions':checks,'scope':'In-memory Chromium; mocked storage. Real devices NOT_RUN'}))
if __name__=='__main__':main()
