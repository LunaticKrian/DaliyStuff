import { ref } from 'vue'

interface TypewriterOptions {
  /** 每个 tick 的间隔（ms），默认 30 —— 约 33 字/秒的复古打字机节奏。 */
  speedMs?: number
  /** 每个 tick 输出多少个字符，默认 1。 */
  charsPerTick?: number
  /** 每次有新字符输出时回调，参数为当前已显示的完整文本。 */
  onUpdate?: (full: string) => void
  /** 源数据结束且队列排空时回调（= 打字彻底结束）。 */
  onDone?: () => void
}

/**
 * 打字机缓冲：吸收后端 SSE 快速吐出的 token，前端按固定节奏逐字显示。
 *
 * 生产者（后端 delta）远快于消费者（固定 ~30ms/字），用内部 queue 吸收差值：
 *   push(text)  → 入队，启动定时器
 *   finish()    → 标记「源已结束」；队列空则立即收尾，否则等排空再收尾
 *   reset()     → 作废当前实例（清队列 + 停定时器，且不再触发 onDone）
 *
 * 每个 controller 仅用于一条消息；换消息时新建一个。
 */
export function useTypewriter(opts: TypewriterOptions = {}) {
  const speedMs = opts.speedMs ?? 30
  const charsPerTick = opts.charsPerTick ?? 1

  const displayed = ref('')
  let queue = ''
  let sourceFinished = false
  let alive = true
  let timer: ReturnType<typeof setInterval> | null = null

  function fireDone() {
    if (alive) opts.onDone?.()
  }

  function tick() {
    if (!alive) return
    if (queue.length === 0) {
      // 暂时没东西可打：源已结束则收尾，否则空转等更多 push
      if (sourceFinished) {
        stop()
        fireDone()
      }
      return
    }
    const n = Math.min(charsPerTick, queue.length)
    displayed.value += queue.slice(0, n)
    queue = queue.slice(n)
    opts.onUpdate?.(displayed.value)
  }

  function start() {
    if (timer != null) return
    timer = setInterval(tick, speedMs)
  }

  function stop() {
    if (timer != null) {
      clearInterval(timer)
      timer = null
    }
  }

  function push(text: string) {
    if (!alive || !text) return
    queue += text
    start()
  }

  /** 标记后端流已结束。队列里若有积压，会继续打完再触发 onDone。 */
  function finish() {
    if (!alive) return
    sourceFinished = true
    if (queue.length === 0) {
      stop()
      fireDone()
    }
  }

  /** 作废：清空状态并停止，且后续不再触发任何回调。 */
  function reset() {
    alive = false
    stop()
    displayed.value = ''
    queue = ''
    sourceFinished = false
  }

  return { displayed, push, finish, reset, stop }
}
