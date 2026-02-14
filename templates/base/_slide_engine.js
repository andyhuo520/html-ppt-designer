/**
 * SlideEngine + AutoPlayController
 * 幻灯片翻页引擎和自动播放控制器
 */

class SlideEngine {
  constructor(options = {}) {
    this.slides = document.querySelectorAll('.slide');
    this.current = 0;
    this.total = this.slides.length;
    this.transitioning = false;
    this.transitionStyle = localStorage.getItem('ppt-transition') || (options.defaultTransition || 'fade');
    this.onSlideChange = options.onSlideChange || null;
    this.init();
  }

  init() {
    // 初始化所有幻灯片状态
    this.slides.forEach((slide, index) => {
      if (index === 0) {
        slide.classList.add('slide-active');
        slide.style.visibility = 'visible';
        slide.style.opacity = '1';
      } else {
        slide.classList.remove('slide-active');
        slide.style.visibility = 'hidden';
        slide.style.opacity = '0';
      }
    });

    this.updateNav();
    this.bindKeys();
    this.bindTouch();
  }

  async goTo(index) {
    // 边界检查
    if (index < 0 || index >= this.total) return;
    if (index === this.current) return;
    if (this.transitioning) return;

    this.transitioning = true;

    const leaving = this.slides[this.current];
    const entering = this.slides[index];
    const viewport = document.querySelector('.slides-viewport');

    // 获取动画时长
    const duration = this.getDuration();

    // 设置过渡类
    viewport.className = 'slides-viewport transition-' + this.transitionStyle;

    // 准备进入的幻灯片
    entering.style.visibility = 'visible';
    entering.classList.add('slide-entering');

    // 添加离开动画类
    leaving.classList.add('slide-leaving');

    // 等待动画完成
    await this.wait(duration + 50);

    // 清理离开的幻灯片
    leaving.style.visibility = 'hidden';
    leaving.style.opacity = '0';
    leaving.classList.remove('slide-active', 'slide-leaving');

    // 设置进入的幻灯片为活动状态
    entering.classList.remove('slide-entering');
    entering.classList.add('slide-active');
    entering.style.opacity = '1';
    entering.style.visibility = 'visible';

    // 更新当前索引
    this.current = index;
    this.transitioning = false;

    // 更新导航
    this.updateNav();

    // 触发回调
    if (this.onSlideChange) {
      this.onSlideChange(index, this.total);
    }
  }

  next() {
    if (this.current < this.total - 1) {
      this.goTo(this.current + 1);
    }
  }

  prev() {
    if (this.current > 0) {
      this.goTo(this.current - 1);
    }
  }

  first() {
    this.goTo(0);
  }

  last() {
    this.goTo(this.total - 1);
  }

  getDuration() {
    const durations = {
      fade: 600,
      slide: 500,
      cinematic: 800,
      cut: 50,
      flip: 600,
      zoom: 500
    };
    return durations[this.transitionStyle] || 600;
  }

  setTransition(style) {
    const validStyles = ['fade', 'slide', 'cinematic', 'cut', 'flip', 'zoom'];
    if (!validStyles.includes(style)) return;

    this.transitionStyle = style;
    localStorage.setItem('ppt-transition', style);

    // 更新按钮状态
    document.querySelectorAll('.style-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.style === style);
    });
  }

  wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  bindKeys() {
    document.addEventListener('keydown', (e) => {
      // 忽略输入框内的按键
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      switch (e.key) {
        case 'ArrowRight':
        case 'ArrowDown':
        case ' ':
        case 'PageDown':
          e.preventDefault();
          this.next();
          break;
        case 'ArrowLeft':
        case 'ArrowUp':
        case 'PageUp':
          e.preventDefault();
          this.prev();
          break;
        case 'Home':
          e.preventDefault();
          this.first();
          break;
        case 'End':
          e.preventDefault();
          this.last();
          break;
      }
    });
  }

  bindTouch() {
    let startX = 0;
    let startY = 0;
    const threshold = 50;

    document.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
    }, { passive: true });

    document.addEventListener('touchend', (e) => {
      const endX = e.changedTouches[0].clientX;
      const endY = e.changedTouches[0].clientY;
      const diffX = endX - startX;
      const diffY = endY - startY;

      // 只有水平滑动距离大于垂直滑动距离时才翻页
      if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > threshold) {
        if (diffX > 0) {
          this.prev();
        } else {
          this.next();
        }
      }
    }, { passive: true });
  }

  updateNav() {
    // 更新导航点
    document.querySelectorAll('.nav-dot').forEach((dot, index) => {
      dot.classList.toggle('active', index === this.current);
    });

    // 更新计数器
    const counter = document.querySelector('.slide-counter');
    if (counter) {
      counter.textContent = `${this.current + 1} / ${this.total}`;
    }

    // 更新进度条（如果存在）
    const progress = document.querySelector('.progress-bar');
    if (progress) {
      const percent = ((this.current + 1) / this.total) * 100;
      progress.style.width = `${percent}%`;
    }
  }
}

/**
 * 自动播放控制器
 */
class AutoPlayController {
  constructor(engine, options = {}) {
    this.engine = engine;
    this.interval = options.interval || 5000;
    this.timer = null;
    this.isPlaying = false;
    this.stopOnLast = options.stopOnLast !== false;
    this.onStateChange = options.onStateChange || null;
    this.hideAfterStart = options.hideAfterStart !== false; // 默认启动后隐藏按钮
    this.panel = null;
    this.hideTimeout = null;
  }

  toggle() {
    if (this.isPlaying) {
      this.stop();
    } else {
      this.start();
    }
  }

  start() {
    if (this.isPlaying) return;

    this.isPlaying = true;
    this.updateButton();

    // 启动后隐藏控制面板
    if (this.hideAfterStart) {
      this.scheduleHide();
    }

    this.timer = setInterval(() => {
      if (this.engine.current < this.engine.total - 1) {
        this.engine.next();
      } else if (this.stopOnLast) {
        this.stop();
      } else {
        // 循环播放
        this.engine.first();
      }
    }, this.interval);

    if (this.onStateChange) {
      this.onStateChange(true);
    }
  }

  stop() {
    this.isPlaying = false;

    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }

    // 停止时清除隐藏定时器并显示面板
    this.cancelHide();
    this.showPanel();
    this.updateButton();

    if (this.onStateChange) {
      this.onStateChange(false);
    }
  }

  scheduleHide() {
    // 2秒后隐藏控制面板
    this.hideTimeout = setTimeout(() => {
      this.hidePanel();
    }, 2000);
  }

  cancelHide() {
    if (this.hideTimeout) {
      clearTimeout(this.hideTimeout);
      this.hideTimeout = null;
    }
  }

  hidePanel() {
    this.panel = document.querySelector('.control-panel');
    if (this.panel) {
      this.panel.style.opacity = '0';
      this.panel.style.pointerEvents = 'none';
      this.panel.style.transform = 'translateX(-50%) translateY(20px)';
    }
  }

  showPanel() {
    this.panel = document.querySelector('.control-panel');
    if (this.panel) {
      this.panel.style.opacity = '1';
      this.panel.style.pointerEvents = 'auto';
      this.panel.style.transform = 'translateX(-50%) translateY(0)';
    }
  }

  setSpeed(ms) {
    this.interval = ms;

    // 更新速度按钮状态
    document.querySelectorAll('.speed-control button').forEach(btn => {
      btn.classList.remove('active');
    });
    if (event && event.target) {
      event.target.classList.add('active');
    }

    // 如果正在播放，重启定时器
    if (this.isPlaying) {
      this.stop();
      this.start();
    }
  }

  updateButton() {
    const btn = document.querySelector('.autoplay-toggle');
    if (!btn) return;

    if (this.isPlaying) {
      btn.innerHTML = '<span class="iconify" data-icon="ph:pause-circle-bold"></span>';
      btn.setAttribute('aria-label', '暂停自动播放');
    } else {
      btn.innerHTML = '<span class="iconify" data-icon="ph:play-circle-bold"></span>';
      btn.setAttribute('aria-label', '开始自动播放');
    }
  }
}

/**
 * 全屏控制器
 */
class FullscreenController {
  constructor(element) {
    this.element = element || document.documentElement;
    this.isFullscreen = false;
    this.bindEvents();
  }

  toggle() {
    if (!document.fullscreenElement) {
      this.enter();
    } else {
      this.exit();
    }
  }

  enter() {
    if (this.element.requestFullscreen) {
      this.element.requestFullscreen();
    } else if (this.element.webkitRequestFullscreen) {
      this.element.webkitRequestFullscreen();
    } else if (this.element.msRequestFullscreen) {
      this.element.msRequestFullscreen();
    }
  }

  exit() {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    }
  }

  bindEvents() {
    document.addEventListener('fullscreenchange', () => {
      this.isFullscreen = !!document.fullscreenElement;
      this.updateButton();
    });
  }

  updateButton() {
    const btn = document.querySelector('.fullscreen-toggle');
    if (!btn) return;

    if (this.isFullscreen) {
      btn.innerHTML = '<span class="iconify" data-icon="ph:arrows-in-bold"></span>';
      btn.setAttribute('aria-label', '退出全屏');
    } else {
      btn.innerHTML = '<span class="iconify" data-icon="ph:arrows-out-bold"></span>';
      btn.setAttribute('aria-label', '进入全屏');
    }
  }
}

// 导出（如果支持模块）
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { SlideEngine, AutoPlayController, FullscreenController };
}
