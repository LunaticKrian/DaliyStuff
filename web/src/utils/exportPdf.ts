// 动态引入：html2canvas + jsPDF 体积大，仅在真正导出时加载，避免拖大主包。
// 不再走 html2pdf.js：它 external 引用 html2canvas、却自带一份老版 jspdf 打进 bundle，
// 在 Vite + jspdf 4.x 下链路不可控（曾导致导出空白 PDF）。这里直接用项目依赖里的
// html2canvas@1.x + jsPDF@4 分步渲染，参数可控、便于诊断。
async function loadLibs() {
  const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
    import('html2canvas'),
    import('jspdf'),
  ])
  return { html2canvas, jsPDF }
}

const A4_W = 794 // 210mm @ 96dpi
const A4_H = 1123 // 297mm @ 96dpi
const PDF_W = 210 // mm
const PDF_H = 297 // mm

/**
 * 把一个 DOM 元素导出为满版 A4 PDF（不依赖浏览器打印对话框）。
 *
 * 思路：html2canvas 把元素按精确的 A4 像素尺寸渲染成位图，再手动按 A4 高度切成多页，
 * 用 jsPDF 逐页 addImage、margin=0、保留背景 → 满版无白边。
 *
 * 元素正常情况是 display:none（屏幕上不占位），这里临时在视口内 (0,0) 展开、负 z-index
 * 沉到页面内容之下渲染、抓图、再还原。html2canvas 只能抓「视口内的渲染结果」，所以必须
 * 让它进入视口、并等布局稳定，否则会抓到空白 canvas。
 */
export async function exportElementToPdf(
  el: HTMLElement,
  filename = 'resume.pdf',
): Promise<void> {
  // 等待 Web 字体（Newsreader / Inter 等）就绪，避免抓到回退字体
  if (document.fonts?.ready) {
    try { await document.fonts.ready } catch { /* ignore */ }
  }

  const prevCss = el.style.cssText
  // 祖先链无 transform/position，absolute (0,0) 落在页面左上角；负 z-index + pointer-events
  // 把它压到页面内容之下，屏幕不可见也不拦截交互。
  el.style.setProperty('display', 'block', 'important')
  el.style.setProperty('position', 'absolute', 'important')
  el.style.setProperty('left', '0', 'important')
  el.style.setProperty('top', '0', 'important')
  el.style.setProperty('width', `${A4_W}px`, 'important')
  el.style.setProperty('min-height', `${A4_H}px`, 'important')
  el.style.setProperty('z-index', '-9999', 'important')
  el.style.setProperty('pointer-events', 'none', 'important')

  try {
    // display:none→block 后等两帧，确保布局与绘制完成，否则 html2canvas 可能抓到 0 尺寸。
    await new Promise<void>((resolve) =>
      requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
    )

    const { html2canvas, jsPDF } = await loadLibs()

    // 诊断：确认元素已进入视口且有内容（空白 PDF 排查用，确认无误后可删）
    console.log('[exportPdf] el offset:', el.offsetWidth, 'x', el.offsetHeight,
      '| scrollH:', el.scrollHeight, '| children:', el.childElementCount)

    const canvas = await html2canvas(el, {
      scale: 2, // 2x 提升清晰度
      useCORS: true,
      backgroundColor: '#ffffff', // 白底，避免透明导致视觉空白
      windowWidth: A4_W,
      width: A4_W,
    })
    console.log('[exportPdf] canvas:', canvas.width, 'x', canvas.height)

    const pdf = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'portrait' })
    const pxPerMm = canvas.width / PDF_W
    const pageHeightPx = PDF_H * pxPerMm // 单页对应的 canvas 像素高

    let y = 0
    let page = 0
    while (y < canvas.height) {
      const slicePx = Math.min(pageHeightPx, canvas.height - y)
      const pageCanvas = document.createElement('canvas')
      pageCanvas.width = canvas.width
      pageCanvas.height = slicePx
      const ctx = pageCanvas.getContext('2d')
      if (ctx) {
        ctx.fillStyle = '#ffffff'
        ctx.fillRect(0, 0, pageCanvas.width, pageCanvas.height)
        ctx.drawImage(canvas, 0, y, canvas.width, slicePx, 0, 0, pageCanvas.width, slicePx)
      }
      if (page > 0) pdf.addPage()
      pdf.addImage(pageCanvas.toDataURL('image/jpeg', 0.98), 'JPEG', 0, 0, PDF_W, slicePx / pxPerMm)
      y += slicePx
      page += 1
    }
    console.log('[exportPdf] pages:', page)

    pdf.save(filename)
  } finally {
    el.style.cssText = prevCss
  }
}
