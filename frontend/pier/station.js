import { mount } from '/base.js'
import { postBoard } from './board.js'
import { gateDesk } from './gate-desk.js'
import { reviewDeck } from './review-deck.js'
import { closeBook } from './close-book.js'

const work = {
  timetable: ['班次水牌', postBoard],
  ledger: ['闸机流水', gateDesk],
  exceptions: ['待签复核', reviewDeck],
  reconciliation: ['封账透视', closeBook]
}
mount({
  title: '水牌 · 渡口核销对账',
  kicker: '青屿渡运合作社 / 营业日结算',
  pages: Object.fromEntries(Object.entries(work).map(([key,[label]]) => [key,label])),
  render: (slug,outlet,session) => work[slug][1](outlet,session)
})
