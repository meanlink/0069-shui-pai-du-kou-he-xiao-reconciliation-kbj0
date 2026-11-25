import { h,badge } from '/base.js'
import { gateTime,gates,verdicts } from './words.js'
import { listing } from './ui.js'

export function ledger(rows) {
  return listing(['流水','班次','营业日','月票','闸机','读秒','判定'],
    rows.map(row=>[h(row.serial),h(row.shift_code),h(row.service_day),h(row.pass_code),
      gates[row.gate],gateTime(row.minute),badge(verdicts[row.verdict],row.verdict)]))
}
