import { h,badge } from '/base.js'
import { listing } from './ui.js'

export function totalsPage(summary) {
  return `<div class="summary-cap"><h2>班次 / 核定载客</h2>${badge(summary.closed ? '已封账' : '营业中',summary.closed ? 'count' : 'open')}</div>
  ${listing(['船班','航线','扫描','有效票数','重复','待签','核定载客','月票占用'],summary.rows.map(row=>[
    h(row.shift),h(row.route),row.scan_count,row.riders,row.duplicates,row.pending,row.seat_limit,
    `<div class="capacity"><meter min="0" max="100" value="${Math.min(100,row.capacity_pct)}"></meter>${row.capacity_pct}%</div>`
  ]))}`
}
