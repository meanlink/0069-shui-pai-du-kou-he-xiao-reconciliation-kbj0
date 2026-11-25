import { api, empty, waitJob, h, badge } from '/base.js'
import { pageHeading, choice, listing } from './ui.js'
import { totalsPage } from './totals.js'
import { downloadClose } from './download.js'
import { bind } from './submit.js'

function adjustmentLedger(data) {
  const rows = data.adjustments ?? []
  if (!rows.length) return ''
  const totals = data.adjustment_totals ?? {}
  return `<section id="adjustment-ledger"><h2>改记增减 · 原流水</h2>
    <p>更正单的冲销（−）与补计（+）同日入本营业日；原封账单与凭据照旧不动。
       共 ${rows.length} 条${totals.net !== undefined ? `，净增减 ${totals.net > 0 ? '+' : ''}${h(totals.net)}` : ''}。</p>
    ${listing(['增减', '影响船班', '月票', '原流水', '更正流水', '入账时间'], rows.map(a => [
      a.delta > 0 ? badge('补计 +1', 'count') : badge('冲销 −1', 'repeat'),
      h(a.shift_code), h(a.pass_code), h(a.original_serial),
      h(a.correction_serial), h(String(a.created_at ?? '').replace('T', ' ').slice(0, 16)),
    ]))}</section>`
}

function correctionForm(shifts, punches) {
  return `<form id="correct-form">
    <h2>月票错班改记</h2>
    <p>封账后发现刷错船班，由复核员改记到后续未封营业日。正班已有该票只冲销错记；正班满载需补计时整笔退回。同一更正流水可安全重试，换班重号会被拒绝。</p>
    <label>更正流水号<input name="serial" pattern="[A-Z0-9-]{3,24}" minlength="3" maxlength="24" required placeholder="如 GZ-20261120-01"></label>
    <label>原闸机流水<select name="original_serial" required>${choice(punches, r => `${r.serial} · ${r.shift_code} · ${r.pass_code}`, 'serial')}</select></label>
    <label>更正后的正班船班<select name="shift_code" required>${choice(shifts, r => `${r.code} / ${r.route} / ${r.service_day}`, 'code')}</select></label>
    <label>改记入账营业日<input name="service_day" type="date" required></label>
    <label>复核说明（选填）<input name="note" maxlength="240" placeholder="错班核查说明"></label>
    <button>登记改记</button><p role="status"></p></form>`
}

export async function closeBook(outlet, session, selection) {
  const [shifts, punches] = await Promise.all([
    api('/api/ferry/shifts'),
    api('/api/ferry/punches'),
  ])
  const days = [...new Set(shifts.map(row => row.service_day))]
  const day = selection ?? days[0]
  if (!day) { outlet.innerHTML = empty('登记班次后可查看核销透视。'); return }
  const data = await api('/api/ferry/daily/' + day)
  const dayOptions = days.includes(day) ? days : [day, ...days]
  outlet.innerHTML = pageHeading('营业日结算', '封账透视 / 错班改记', '同班次同月票仅计一次。各班次分开核算，保留午夜跨日流水。封账后错班在此改记，增减与原流水可查。')
    + `<div class="pier-grid"><section id="pivot">${totalsPage(data)}</section><aside>
    <h2>结算选择</h2><label>营业日<select id="service-day">${choice(dayOptions.map(value => ({ code: value })), r => r.code)}</select></label>
    ${data.closed ? `<form id="download"><button>下载冻结 CSV</button><p role="status"></p></form>` :
    session.role === 'reviewer' ? `<form id="close"><button>签名封账</button><p role="status"></p></form>` : ''}
    <p>审批未结或核销超员时，本日暂缓关闭。</p>
    ${session.role === 'reviewer' ? correctionForm(shifts, punches) : ''}
    </aside></div>
    <div class="pier-grid"><section class="wide">${adjustmentLedger(data)}</section></div>`
  const selector = outlet.querySelector('#service-day')
  selector.value = day
  selector.onchange = () => closeBook(outlet, session, selector.value)
  bind(outlet.querySelector('#close'), async () => {
    const request = await api('/api/ferry/daily/' + day + '/close', 'POST', {})
    await waitJob(request.job)
  }, () => closeBook(outlet, session, day))
  bind(outlet.querySelector('#download'), () => downloadClose(day), () => { })
  let reloadDay = day
  bind(outlet.querySelector('#correct-form'), async form => {
    await api('/api/ferry/corrections', 'POST', {
      serial: form.serial,
      original_serial: form.original_serial,
      shift_code: form.shift_code,
      service_day: form.service_day,
      note: form.note || undefined,
    })
    reloadDay = form.service_day
  }, () => closeBook(outlet, session, reloadDay))
}
