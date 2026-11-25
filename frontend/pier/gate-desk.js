import { api } from '/base.js'
import { pageHeading,choice } from './ui.js'
import { ledger } from './latest.js'
import { bind } from './submit.js'

export async function gateDesk(outlet, session) {
  const [punches,shifts,passes] = await Promise.all(['/punches','/shifts','/passes'].map(path=>api('/api/ferry'+path)))
  outlet.innerHTML = pageHeading('双闸记录','核销流水','追查同一月票在同一船班的重复刷卡，并核对午夜后记录。')
    + `<div class="pier-grid"><section><h2>班次核销底账</h2>${ledger(punches)}</section><aside>
    <h2>闸口补录</h2><p>使用闸机的原始流水号。相同号和相同内容可安全重传。</p>
    ${session.role==='operator' ? `<form><label>闸机流水号<input name="serial" pattern="[A-Z0-9-]{3,24}" required></label>
    <label>船班<select name="shift_code">${choice(shifts,row=>row.code+' / '+row.route)}</select></label>
    <label>月票<select name="pass_code">${choice(passes,row=>row.code+' / '+row.route)}</select></label>
    <label>闸口<select name="gate"><option value="east">东闸</option><option value="west">西闸</option></select></label>
    <label>营业日分钟<input name="minute" type="number" min="0" max="2879" required></label>
    <button>登记流水</button><p role="status"></p></form>` : ''}</aside></div>`
  bind(outlet.querySelector('form'), data=>api('/api/ferry/punches','POST',{...data,minute:+data.minute}),()=>gateDesk(outlet,session))
}
