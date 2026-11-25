export const verdicts = {first:'有效',repeat:'重复',outside:'不在读秒窗',ineligible:'不适用月票'}
export const rulings = {open:'待签',count:'补计',reject:'驳回'}
export const gates = {east:'东闸',west:'西闸'}

export function gateTime(minute) {
  const format = n => String(n).padStart(2,'0')
  return (minute >= 1440 ? '次日 ' : '') + format(Math.floor(minute / 60) % 24) + ':' + format(minute % 60)
}
