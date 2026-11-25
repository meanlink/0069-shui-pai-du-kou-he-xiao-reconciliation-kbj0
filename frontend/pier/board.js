import { api } from '/base.js'
import { routeStrip } from './route-card.js'
import { bind } from './submit.js'
import { pageHeading } from './ui.js'

export async function postBoard(outlet, session) {
  const ships = await api('/api/ferry/shifts')
  outlet.innerHTML = pageHeading('班次排布','渡口水牌','按营业日排班。午夜之后的班次仍列在始发营业日。')
    + `<div class="pier-grid"><section><h2>航线发班 / 过闸时窗</h2><ol class="ships">${ships.map(routeStrip).join('')}</ol></section>
    <aside><h2>登船时钟</h2><p>发船前 20 分钟到发船后 3 分钟可计入该班次。跨午夜以营业日开头计分钟。</p>
    ${session.role==='operator' ? `<form><label>船班号<input name="code" value="F-" pattern="F-[0-9]{3}" required></label>
    <label>航线<input name="route" required></label><label>营业日<input name="service_day" type="date" required></label>
    <label>离岸分钟<input name="departure_minute" type="number" min="0" max="2879" required></label>
    <label>核定载客<input name="capacity" type="number" min="1" max="500" required></label>
    <button>录入排班</button><p role="status"></p></form>` : ''}</aside></div>`
  bind(outlet.querySelector('form'), data=>api('/api/ferry/shifts','POST',{...data,departure_minute:+data.departure_minute,capacity:+data.capacity}),
       ()=>postBoard(outlet,session))
}
