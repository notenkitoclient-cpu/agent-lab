/* ============================
   AGENT LAB - SCRIPT.JS
============================= */

// ============================
// ターミナルタイピングアニメーション
// ============================
const TERMINAL_COMMANDS = [
  "python github_hunter.py",
  "agent experiment #001 complete",
  "found 3 AI repos today",
  "generating X post...",
  "experiment logged ✓",
];

let cmdIndex = 0;
let charIndex = 0;
let isDeleting = false;
let terminalEl = document.getElementById("terminal-text");

function typeTerminal() {
  if (!terminalEl) return;
  const currentCmd = TERMINAL_COMMANDS[cmdIndex];

  if (!isDeleting) {
    terminalEl.textContent = currentCmd.slice(0, charIndex + 1);
    charIndex++;
    if (charIndex === currentCmd.length) {
      isDeleting = true;
      setTimeout(typeTerminal, 2000);
      return;
    }
  } else {
    terminalEl.textContent = currentCmd.slice(0, charIndex - 1);
    charIndex--;
    if (charIndex === 0) {
      isDeleting = false;
      cmdIndex = (cmdIndex + 1) % TERMINAL_COMMANDS.length;
    }
  }

  const speed = isDeleting ? 40 : 75;
  setTimeout(typeTerminal, speed);
}

// ============================
// スクロールでヘッダーをスタイル変更
// ============================
function handleHeaderScroll() {
  const header = document.getElementById("header");
  if (!header) return;
  if (window.scrollY > 40) {
    header.classList.add("scrolled");
  } else {
    header.classList.remove("scrolled");
  }
}

// ============================
// フェードインアニメーション（Intersection Observer）
// ============================
function initFadeIn() {
  const targets = document.querySelectorAll(
    ".pillar-card, .exp-card, .agent-card, .goal-card, .section-header"
  );

  targets.forEach((el, i) => {
    el.classList.add("fade-in");
    // カードは順番に遅延
    const delay = (i % 6) * 80;
    el.style.transitionDelay = `${delay}ms`;
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
  );

  targets.forEach((el) => observer.observe(el));
}

// ============================
// ハンバーガーメニュー
// ============================
function initHamburger() {
  const btn = document.getElementById("hamburger");
  const nav = document.getElementById("nav");
  if (!btn || !nav) return;

  btn.addEventListener("click", () => {
    btn.classList.toggle("open");
    nav.classList.toggle("open");
  });

  // ナビリンクをクリックしたらメニューを閉じる
  nav.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", () => {
      btn.classList.remove("open");
      nav.classList.remove("open");
    });
  });
}

// ============================
// カウンターアニメーション（スタッツ）
// ============================
function animateCounter(el, target, duration = 1200, prefix = "", suffix = "") {
  const start = 0;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
    const value = Math.round(start + (target - start) * eased);
    el.textContent = prefix + String(value).padStart(3, "0") + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }

  requestAnimationFrame(update);
}

function initStatCounters() {
  const statEl = document.getElementById("stat-exp");
  if (!statEl) return;

  const observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        animateCounter(statEl, 1, 1000);
        observer.disconnect();
      }
    },
    { threshold: 0.5 }
  );

  observer.observe(statEl);
}

// ============================
// プログレスバーアニメーション
// ============================
function initProgressBar() {
  const fill = document.querySelector(".goal-progress-fill");
  if (!fill) return;

  const observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        // 実験1/100 = 1%
        fill.style.width = "1%";
        observer.disconnect();
      }
    },
    { threshold: 0.3 }
  );

  observer.observe(fill);
}

// ============================
// マウスパラレックス（Hero グロー）
// ============================
function initParallax() {
  const glow = document.querySelector(".hero-glow");
  if (!glow) return;

  document.addEventListener("mousemove", (e) => {
    const x = (e.clientX / window.innerWidth - 0.5) * 30;
    const y = (e.clientY / window.innerHeight - 0.5) * 20;
    glow.style.transform = `translateX(calc(-50% + ${x}px)) translateY(${y}px)`;
  }, { passive: true });
}

// ============================
// メインの初期化
// ============================
document.addEventListener("DOMContentLoaded", () => {
  // ターミナルアニメーション
  setTimeout(typeTerminal, 800);

  // スクロールイベント
  window.addEventListener("scroll", handleHeaderScroll, { passive: true });
  handleHeaderScroll();

  // フェードイン
  initFadeIn();

  // ハンバーガー
  initHamburger();

  // カウンター
  initStatCounters();

  // プログレスバー
  initProgressBar();

  // パラレックス
  initParallax();

  console.log(`
  ╔═══════════════════════════════╗
  ║       AGENT LAB               ║
  ║  Build. Experiment. Automate. ║
  ╚═══════════════════════════════╝
  `);
});
