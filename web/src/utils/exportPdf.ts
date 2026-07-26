// 动态引入：html2pdf 体积大（含 html2canvas），仅在真正导出时加载，避免拖大主包。
async function loadHtml2Pdf() {
  return (await import('html2pdf.js')).default
}

/**
 * 把一个 DOM 元素导出为满版 A4 PDF（不依赖浏览器打印对话框）。
 *
 * 思路：用 html2canvas 把元素按精确的 A4 像素尺寸（210×297mm @96dpi = 794×1123）
 * 渲染成位图，再用 jsPDF 切成 A4 页、margin=0、强制保留背景 → 满版无白边。
 *
 * 元素正常情况是 display:none（屏幕上不占位），这里临时展开到屏幕外渲染、抓图、再还原。
 */
const A4_W = 794 // 210mm @ 96dpi
const A4_H = 1123 // 297mm @ 96dpi

export async function exportElementToPdf(
  el: HTMLElement,
  filename = 'resume.pdf',
): Promise<void> {
  // 等待 Web 字体（Press Start 2P / Newsreader 等）就绪，避免抓到回退字体
  if (document.fonts?.ready) {
    try { await document.fonts.ready } catch { /* ignore */ }
  }

  // 记录原样式，抓完还原
  const prev = {
    cssText: el.style.cssText,
  }
  el.style.setProperty('display', 'block', 'important')
  el.style.setProperty('position', 'fixed', 'important')
  el.style.setProperty('left', '-10000px', 'important')
  el.style.setProperty('top', '0', 'important')
  el.style.setProperty('width', `${A4_W}px`, 'important')
  el.style.setProperty('min-height', `${A4_H}px`, 'important')
  el.style.setProperty('z-index', '-1', 'important')

  try {
    const html2pdf = await loadHtml2Pdf()
    await html2pdf()
      .set({
        margin: 0,
        filename,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: {
          scale: 2, // 2x 提升清晰度
          useCORS: true,
          backgroundColor: null, // 用元素自身背景，保证满版底色
          windowWidth: A4_W,
        },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
      })
      .from(el)
      .save()
  } finally {
    el.style.cssText = prev.cssText
  }
}
