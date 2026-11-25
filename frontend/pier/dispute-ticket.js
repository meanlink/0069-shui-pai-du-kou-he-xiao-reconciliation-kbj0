import { h,badge } from '/base.js'
import { rulings,verdicts } from './words.js'

export function ticket(row, reviewer) {
  return `<article class="dispute"><header><div><h2>${h(row.serial)} · ${h(row.shift_code)}</h2>
  <span>${h(row.pass_code)} / ${verdicts[row.verdict]}</span></div>${badge(rulings[row.ruling],row.ruling)}</header>
  <blockquote>${h(row.operator_note)}</blockquote>
  ${row.resolution ? `<p>${h(row.resolution)}</p>` : ''}
  ${reviewer && row.ruling==='open' ? `<form data-serial="${h(row.serial)}">
  <label>复核决定<select name="ruling"><option value="reject">驳回</option><option value="count">补计</option></select></label>
  <label>依据<input name="resolution" minlength="4" maxlength="240" required></label>
  <button>签审</button><p role="status"></p></form>` : ''}</article>`
}
