import { notice } from '/base.js'

export function bind(form, action, reload) {
  if (!form) return
  form.addEventListener('submit', async event => {
    event.preventDefault()
    const button = form.querySelector('button')
    const status = form.querySelector('[role=status]')
    button.disabled = true
    try {
      await action(Object.fromEntries(new FormData(form)))
      await reload()
    } catch (error) {
      notice(status,error.message,true)
    } finally {
      button.disabled = false
    }
  })
}
