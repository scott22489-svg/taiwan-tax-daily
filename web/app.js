'use strict';
const $ = id => document.getElementById(id);
let archive, category = '', page = 1;
const pageSize = 15;
const categories = ['營業稅','營利事業所得稅','綜合所得稅','遺產及贈與稅','房地合一／不動產','其他稅務'];
function element(tag, text, className) { const el = document.createElement(tag); if (text) el.textContent = text; if (className) el.className = className; return el; }
function link(url, text) { const a = element('a', text); const parsed = new URL(url); if (!['https:', 'http:'].includes(parsed.protocol)) throw new Error('不支援的來源網址'); a.href = parsed.href; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a; }
function renderCategories() {
  $('categories').replaceChildren(...['', ...categories].map(name => {
    const button = element('button', name || '全部消息', 'category'); button.type = 'button'; button.setAttribute('aria-pressed', String(name === category));
    button.append(element('span', String(archive.articles.filter(a => !name || a.category === name).length)));
    button.addEventListener('click', () => { category = name; page = 1; renderCategories(); render(); }); return button;
  }));
}
function render() {
  const query = $('search').value.trim().toLocaleLowerCase();
  const days = Number($('period').value);
  const today = new Date().toLocaleDateString('en-CA', {timeZone:'Asia/Taipei'});
  const cutoff = Number.isFinite(days) ? new Date(Date.parse(today + 'T00:00:00+08:00') - (days - 1) * 86400000).toLocaleDateString('en-CA', {timeZone:'Asia/Taipei'}) : '';
  const rows = archive.articles.filter(a => (!category || a.category === category) && (!$('source').value || a.sourceId === $('source').value) && (!cutoff || (a.date && a.date >= cutoff && a.date <= today)) && (!query || [a.title,a.summary,a.source,a.category].join(' ').toLocaleLowerCase().includes(query)));
  const totalPages = Math.max(1, Math.ceil(rows.length/pageSize)); page = Math.min(page,totalPages);
  $('section-title').textContent = category || '最新稅務消息'; $('count').textContent = `${rows.length} 篇消息`;
  $('articles').replaceChildren(...rows.slice((page-1)*pageSize,page*pageSize).map(a => {
    const article = element('article'); const date = element('div', a.date ? a.date.slice(0,4) : '日期未提供', 'article-date');
    if(a.date) date.append(element('strong',a.date.slice(5).replace('-',' / ')));
    const content = element('div'), meta = element('div', '', 'meta'); meta.append(element('span',a.category,'tag'),element('span',a.source));
    const heading = element('h3'); heading.append(link(a.url,a.title));
    const bottom = element('div','','article-bottom'); bottom.append(element('span',a.summaryType),link(a.url,'閱讀官方原文 ↗'));
    content.append(meta,heading,element('p',a.summary || '此來源未提供摘要，請閱讀官方原文。'),bottom); article.append(date,content); return article;
  }));
  if (!rows.length) $('articles').append(element('p','找不到符合條件的消息，請調整關鍵字或篩選條件。','empty'));
  $('page-info').textContent = `${page} / ${totalPages}`; $('previous').disabled = page === 1; $('next').disabled = page === totalPages;
}
async function init() {
  try {
    const response = await fetch('./data.json', {cache:'no-cache'}); if(!response.ok) throw new Error('資料讀取失敗'); archive = await response.json();
    $('updated').textContent = new Date(archive.updatedAt).toLocaleString('zh-TW',{timeZone:'Asia/Taipei',hour12:false,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
    for(const source of archive.sources) {
      const option = element('option',source.name); option.value = source.id; $('source').append(option);
      const li = element('li'); li.append(link(source.url, source.name + (source.status === 'error' ? '（暫停更新）' : ''))); if(source.status === 'error') li.className='error'; $('sources').append(li);
    }
    const failures = archive.sources.filter(s=>s.status==='error');
    const stale = Date.now() - Date.parse(archive.updatedAt) > 48*3600000;
    if(failures.length || stale) { $('notice').hidden=false; $('notice').textContent = stale ? '資料已超過 48 小時未更新，目前顯示歷史資料。' : `${failures.map(s=>s.name).join('、')}本次讀取失敗，已保留其歷史文章。`; }
    renderCategories(); render();
    for(const id of ['search','source','period']) $(id).addEventListener(id==='search'?'input':'change',()=>{page=1;render();});
    for(const [id,delta] of [['previous',-1],['next',1]]) $(id).addEventListener('click',()=>{page+=delta;render();$('section-title').scrollIntoView({block:'start'});});
  } catch(error) { $('updated').textContent='暫時無法讀取'; $('articles').replaceChildren(element('p','資料載入失敗，請稍後重新整理頁面。','empty')); $('previous').disabled=true; $('next').disabled=true; }
}
init();
