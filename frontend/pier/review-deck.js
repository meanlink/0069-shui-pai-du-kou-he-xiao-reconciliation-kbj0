import { api,empty } from '/base.js'
import { ticket } from './dispute-ticket.js'
import { bind } from './submit.js'
import { choice,pageHeading } from './ui.js'

export async function reviewDeck(outlet,session) {
  const [cases,scans] = await Promise.all([api('/api/ferry/disputes'),api('/api/ferry/punches')])
  const pending = scans.filter(scan=>['outside','ineligible'].includes(scan.verdict)&&!cases.some(row=>row.serial===scan.serial))
  const operator = session.role==='operator'
  outlet.innerHTML = pageHeading('人工审签','待签复核','逐条保留补计证据，跨航线和过期月票只能驳回。')
   + `<div class="ticket-rail">${cases.length ? cases.map(row=>ticket(row,session.role==='reviewer')).join('') : empty('没有需要复核的流水。')}</div>
   ${operator && pending.length ? `<form id="open-appeal"><h2>提请复核</h2><label>流水<select name="serial">${choice(pending,row=>row.serial,'serial')}</select></label>
     <label>值班记录<input name="operator_note" minlength="4" maxlength="240" required></label><button>提交</button><p role="status"></p></form>` : ''}`
  for (const form of outlet.querySelectorAll('[data-serial]')) {
    bind(form,data=>api('/api/ferry/disputes/'+form.dataset.serial,'PUT',data),()=>reviewDeck(outlet,session))
  }
  bind(outlet.querySelector('#open-appeal'),data=>api('/api/ferry/disputes','POST',data),()=>reviewDeck(outlet,session))
}
