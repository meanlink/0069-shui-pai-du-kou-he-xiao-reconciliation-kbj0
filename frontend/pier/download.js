import { api } from '/base.js'

export async function downloadClose(day) {
  const content = await api('/api/ferry/daily/'+day+'/download')
  const url = URL.createObjectURL(new Blob(['\ufeff'+content],{type:'text/csv;charset=utf-8'}))
  const link = document.createElement('a')
  link.href=url
  link.download='ferry-'+day+'.csv'
  link.click()
  setTimeout(()=>URL.revokeObjectURL(url),1000)
}
