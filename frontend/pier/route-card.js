import { h } from '/base.js'
import { gateTime } from './words.js'

export function routeStrip(shift) {
  const open = Math.max(0,shift.departure_minute - 20)
  const shut = shift.departure_minute + 3
  return `<li><time>${gateTime(shift.departure_minute)}</time><div><strong>${h(shift.route)}</strong>
    <span>${h(shift.service_day)} / ${h(shift.code)}</span></div><div class="gate-window"><b>${gateTime(open)} — ${gateTime(shut)}</b>
    <span>读秒窗 / 核定载客 ${shift.capacity}</span></div><b class="scan-count">${shift.scans}<small>笔扫描</small></b></li>`
}
