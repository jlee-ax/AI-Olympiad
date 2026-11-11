// Inspect the generated student HTML in an offline local browser; no learner data.
const { chromium } = require('playwright');
const { pathToFileURL } = require('url');
const path = require('path');
const fs = require('fs');
const out = process.env.KOAI_QA_DIR;
if (!out) throw new Error('Set KOAI_QA_DIR to an existing disposable output directory.');
(async () => {
  const browser = await chromium.launch({executablePath:'/usr/bin/chromium', args:['--no-sandbox']});
  const checks=[];
  try {
    for (const [label,width,height] of [['desktop',1440,900],['mobile',390,844]]) {
      const page = await browser.newPage({viewport:{width,height}, deviceScaleFactor:1});
      await page.route('**/*', route => route.request().url().startsWith('file:') ? route.continue() : route.abort());
      await page.goto(pathToFileURL(path.resolve('lessons/week01/week01_python_tables.html')).href,{waitUntil:'domcontentloaded'});
      for(const text of ['진단 5의 새 오류','새 배열을 혼자 예측하고 확인하기','새 분산 문제에 내 말로 답하기','새 병합 조건을 먼저 예측하기']) {
        const loc=page.getByText(text,{exact:false}).first();
        if(await loc.count()!==1 || !(await loc.isVisible())) throw new Error(label+' missing visible prompt: '+text);
      }
      const whole=await page.locator('body').innerText();
      if(whole.includes('def recorded_mean(values):'))throw new Error('teacher solution leaked into student HTML');
      const target=page.getByText(label==='desktop'?'진단 5의 새 오류':'새 배열을 혼자 예측하고 확인하기',{exact:false}).first();
      await target.scrollIntoViewIfNeeded();
      const file=path.join(out,label+'-notebook.png');
      await page.screenshot({path:file});
      checks.push({viewport:label,width,height,prompts_visible:4,teacher_solution_absent:true,screenshot:file});
      await page.close();
    }
  } finally {await browser.close();}
  fs.writeFileSync(path.join(out,'browser-result.json'),JSON.stringify({status:'passed',checks,scope:'Offline rendered HTML prompt presence only; no learner outcome or full accessibility audit.'},null,2)+'\n');
  console.log(JSON.stringify({status:'passed',checks:checks.map(({viewport,prompts_visible,teacher_solution_absent})=>({viewport,prompts_visible,teacher_solution_absent}))}));
})().catch(error=>{console.error(error);process.exitCode=1});
