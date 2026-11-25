import { api,empty,waitJob } from '/base.js'
import { pageHeading,choice } from './ui.js'
import { totalsPage } from './totals.js'
import { downloadClose } from './download.js'
import { bind } from './submit.js'

export async function closeBook(outlet,session,selection) {
  const shifts = await api('/api/ferry/shifts')
  const days = [...new Set(shifts.map(row=>row.service_day))]
  const day = selection ?? days[0]
  if (!day) { outlet.innerHTML=empty('登记班次后可查看核销透视。'); return }
  const data = await api('/api/ferry/daily/'+day)
  outlet.innerHTML = pageHeading('营业日结算','封账透视','同班次同月票仅计一次。各班次分开核算，保留午夜跨日流水。')
    + `<div class="pier-grid"><section id="pivot">${totalsPage(data)}</section><aside>
    <h2>结算选择</h2><label>营业日<select id="service-day">${choice(days.map(value=>({code:value})),r=>r.code)}</select></label>
    ${data.closed ? `<form id="download"><button>下载冻结 CSV</button><p role="status"></p></form>` :
    session.role==='reviewer' ? `<form id="close"><button>签名封账</button><p role="status"></p></form>` : ''}
    <p>审批未结或核销超员时，本日暂缓关闭。</p></aside></div>`
  const selector = outlet.querySelector('#service-day')
  selector.value=day
  selector.onchange=()=>closeBook(outlet,session,selector.value)
  bind(outlet.querySelector('#close'),async()=>{
    const request=await api('/api/ferry/daily/'+day+'/close','POST',{})
    await waitJob(request.job)
  },()=>closeBook(outlet,session,day))
  bind(outlet.querySelector('#download'),()=>downloadClose(day),()=>{})
}
