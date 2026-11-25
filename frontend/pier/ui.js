import { h } from '/base.js'

export const pageHeading = (label,title,description) =>
  `<header class="pier-heading"><span>${h(label)}</span><h1>${h(title)}</h1><p>${h(description)}</p></header>`

export function choice(rows, label, value='code') {
  return rows.map(row => `<option value="${h(row[value])}">${h(label(row))}</option>`).join('')
}

export function listing(headers, rows) {
  return `<div class="over-table"><table><thead><tr>${headers.map(cell=>`<th scope="col">${h(cell)}</th>`).join('')}</tr></thead>
    <tbody>${rows.map(row=>`<tr>${row.map(cell=>`<td>${cell}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`
}
