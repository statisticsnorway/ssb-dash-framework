(() => {
  const initializedWindows = new WeakSet();
  let topZIndex = 1050;
  let snapPreview = null;

  let pendingModalOrigin = null;

  const modalOrigins = new WeakMap();
  const positionedModals = new Set();

  const TASKBAR_ID = "desktop-taskbar";
  const SNAP_THRESHOLD = 24;
  const MIN_WINDOW_WIDTH = 320;
  const MIN_WINDOW_HEIGHT = 220;
  const STORAGE_PREFIX = "nspek-desktop-window-";
  const MODAL_ORIGIN_TIMEOUT = 15000;

  // --------------------------------------------------
  // Oppgavelinje og vindusidentifikasjon
  // --------------------------------------------------

  function getTaskbar() {
    let taskbar = document.getElementById(TASKBAR_ID);

    if (!taskbar) {
      taskbar = document.createElement("div");
      taskbar.id = TASKBAR_ID;
      taskbar.className = "desktop-taskbar";
      taskbar.setAttribute("aria-label", "Åpne vinduer");
      document.body.appendChild(taskbar);
    }

    return taskbar;
  }

  function getModuleId(win) {
    return win.id.replace(/-window$/, "");
  }

  function getTaskbarButton(win) {
    return document.getElementById(
      `${getModuleId(win)}-taskbar-button`
    );
  }

  function getStorageKey(win) {
    return `${STORAGE_PREFIX}${getModuleId(win)}`;
  }

  function getWindowRect(win) {
    const rect = win.getBoundingClientRect();

    return {
      left: rect.left,
      top: rect.top,
      width: rect.width,
      height: rect.height,
    };
  }

  // --------------------------------------------------
  // Dynamiske forelder- og barnevinduer
  // --------------------------------------------------

  function getOwningWindow(element) {
    return element.closest(".desktop-window");
  }

  function setWindowParent(childWindow, parentWindow) {
    if (!childWindow) return;

    if (
      parentWindow &&
      parentWindow !== childWindow
    ) {
      childWindow.dataset.parentWindow = parentWindow.id;
    } else {
      delete childWindow.dataset.parentWindow;
    }
  }

  function closeDesktopWindow(win, visited = new Set()) {
    if (!win || visited.has(win)) return;

    visited.add(win);

    // Lukk alle direkte barn først.
    // Rekursjonen håndterer også eventuelle etterkommere.
    document
      .querySelectorAll(".desktop-window[data-parent-window]")
      .forEach((childWindow) => {
        if (
          childWindow.dataset.parentWindow === win.id
        ) {
          closeDesktopWindow(childWindow, visited);
        }
      });

    saveWindowState(win);

    win.style.display = "none";
    win.dataset.minimized = "false";
    win.dataset.closed = "true";
    win.classList.remove("active-window");

    removeTaskbarButton(win);
  }


  // --------------------------------------------------
  // Lukk historikkvinduer ved nytt søk
  // --------------------------------------------------

  let lastSearchWindowCloseSignal = null;

  window.nspekCloseSearchWindows = function (signal) {
    if (
      signal === null ||
      signal === undefined ||
      signal === lastSearchWindowCloseSignal
    ) {
      return;
    }

    lastSearchWindowCloseSignal = signal;

    const windowIds = [
      "editeringslogg-window",
      "generell-kommentar-historikk-window",
    ];

    windowIds.forEach((windowId) => {
      const win = document.getElementById(windowId);

      if (win) {
        closeDesktopWindow(win);
      }
    });
  };

  // --------------------------------------------------
  // Arbeidsområde: sidebar til venstre, oppgavelinje
  // nederst og vinduer i området mellom disse.
  // --------------------------------------------------

  function getWorkArea() {
    const sidebar = document.getElementById("main-layout-sidebar");
    const taskbar = document.getElementById(TASKBAR_ID);

    const sidebarStyle = sidebar
      ? window.getComputedStyle(sidebar)
      : null;

    const sidebarRect = sidebar?.getBoundingClientRect();

    const sidebarVisible = Boolean(
      sidebar &&
      sidebarStyle?.display !== "none" &&
      sidebarStyle?.visibility !== "hidden" &&
      sidebarRect &&
      sidebarRect.width > 0
    );

    const left = sidebarVisible
      ? Math.max(0, sidebarRect.right)
      : 0;

    const taskbarVisible = Boolean(
      taskbar &&
      taskbar.getClientRects().length > 0 &&
      window.getComputedStyle(taskbar).display !== "none" &&
      taskbar.offsetHeight > 0 &&
      taskbar.children.length > 0
    );

    const taskbarHeight = taskbarVisible
      ? taskbar.getBoundingClientRect().height
      : 0;

    const width = Math.max(0, window.innerWidth - left);
    const height = Math.max(0, window.innerHeight - taskbarHeight);

    document.documentElement.style.setProperty(
      "--desktop-workarea-left",
      `${left}px`
    );

    document.documentElement.style.setProperty(
      "--desktop-taskbar-height",
      `${taskbarHeight}px`
    );

    return {
      left,
      top: 0,
      width,
      height,
      right: left + width,
      bottom: height,
    };
  }

  function clampWindowToWorkArea(win) {
    const area = getWorkArea();
    const rect = getWindowRect(win);
    const titlebar = win.querySelector(".desktop-window-titlebar");
    const titlebarHeight = titlebar?.offsetHeight || 36;

    const width = Math.min(rect.width, area.width);
    const height = Math.min(rect.height, area.height);

    const left = Math.min(
      Math.max(rect.left, area.left - width + 80),
      Math.max(area.left, area.right - Math.min(width, 80))
    );

    const top = Math.min(
      Math.max(rect.top, area.top),
      Math.max(area.top, area.bottom - Math.min(titlebarHeight, height))
    );

    win.style.left = `${left}px`;
    win.style.top = `${top}px`;
    win.style.width = `${width}px`;
    win.style.height = `${height}px`;
  }

  // --------------------------------------------------
  // Lagring og gjenoppretting av vindustilstand
  // --------------------------------------------------

  function saveWindowState(win) {
    try {
      const state = {
        ...getWindowRect(win),
        maximized: win.classList.contains("maximized"),
        snapped: win.dataset.snapped === "true",
        restoreRect: win._desktopRestoreRect || null,
      };

      localStorage.setItem(
        getStorageKey(win),
        JSON.stringify(state)
      );
    } catch (error) {
      console.warn("Kunne ikke lagre vindusposisjon:", error);
    }
  }

  function restoreWindowState(win) {
    if (win.dataset.stateRestored === "true") return;

    win.dataset.stateRestored = "true";

    try {
      const saved = localStorage.getItem(getStorageKey(win));
      if (!saved) return;

      const state = JSON.parse(saved);

      if (
        Number.isFinite(state.left) &&
        Number.isFinite(state.top) &&
        Number.isFinite(state.width) &&
        Number.isFinite(state.height)
      ) {
        win.style.left = `${state.left}px`;
        win.style.top = `${state.top}px`;
        win.style.width = `${state.width}px`;
        win.style.height = `${state.height}px`;
      }

      if (
        state.restoreRect &&
        Number.isFinite(state.restoreRect.left) &&
        Number.isFinite(state.restoreRect.top) &&
        Number.isFinite(state.restoreRect.width) &&
        Number.isFinite(state.restoreRect.height)
      ) {
        win._desktopRestoreRect = state.restoreRect;
      }

      win.dataset.snapped = state.snapped ? "true" : "false";
      win.classList.toggle("maximized", Boolean(state.maximized));

      const maximizeButton = document.getElementById(
        `${getModuleId(win)}-window-maximize`
      );

      if (maximizeButton) {
        maximizeButton.title = state.maximized
          ? "Gjenopprett vindu"
          : "Maksimer vindu";
      }
    } catch (error) {
      console.warn("Kunne ikke gjenopprette vindusposisjon:", error);
    }
  }

  // --------------------------------------------------
  // Oppgavelinje og hovedlayout
  // --------------------------------------------------

  function updateMainLayoutHeight() {
    const taskbar = document.getElementById(TASKBAR_ID);
    const mainLayout = document.getElementById("main-layout");

    if (!mainLayout) return;

    const taskbarVisible = Boolean(
      taskbar &&
      taskbar.getClientRects().length > 0 &&
      window.getComputedStyle(taskbar).display !== "none" &&
      taskbar.offsetHeight > 0 &&
      taskbar.children.length > 0
    );

    mainLayout.classList.toggle(
      "taskbar-visible",
      taskbarVisible
    );
  }

  function updateTaskbarMode() {
    const taskbar = document.getElementById(TASKBAR_ID);
    if (!taskbar) return;

    const buttons = Array.from(
      taskbar.querySelectorAll(".desktop-taskbar-button")
    );

    if (buttons.length === 0) {
      taskbar.classList.remove("compact");
      updateMainLayoutHeight();
      return;
    }

    const styles = window.getComputedStyle(taskbar);
    const horizontalPadding =
      parseFloat(styles.paddingLeft) +
      parseFloat(styles.paddingRight);

    const availableWidth = taskbar.clientWidth - horizontalPadding;
    const buttonWidth = 180;
    const gap = 6;

    const requiredWidth =
      buttons.length * buttonWidth +
      (buttons.length - 1) * gap;

    taskbar.classList.toggle(
      "compact",
      requiredWidth > availableWidth
    );
  }

  function bringToFront(win) {
    topZIndex += 1;
    win.style.zIndex = String(topZIndex);

    document.querySelectorAll(".desktop-window").forEach((otherWin) => {
      otherWin.classList.toggle("active-window", otherWin === win);
    });

    const taskbarButton = getTaskbarButton(win);

    document.querySelectorAll(".desktop-taskbar-button").forEach((button) => {
      button.classList.toggle("active", button === taskbarButton);
    });
  }

  // --------------------------------------------------
  // Modalhåndtering for desktop-vinduer
  // --------------------------------------------------

  function resetModalPosition(modal) {
    const dialog = modal.querySelector(".modal-dialog");

    if (modal.classList.contains("desktop-window-modal")) {
      modal.classList.remove("desktop-window-modal");
    }

    if (dialog) {
      if (dialog.style.left) {
        dialog.style.removeProperty("left");
      }

      if (dialog.style.top) {
        dialog.style.removeProperty("top");
      }
    }

    modalOrigins.delete(modal);
    positionedModals.delete(modal);
  }

  function positionModalInDesktopWindow(modal, win) {
    const dialog = modal.querySelector(".modal-dialog");

    if (!dialog || !win || !win.isConnected) {
      resetModalPosition(modal);
      return;
    }

    const winStyle = window.getComputedStyle(win);
    const winRect = win.getBoundingClientRect();

    // Ikke plasser en modal i et skjult eller minimert vindu.
    if (
      winStyle.display === "none" ||
      winStyle.visibility === "hidden" ||
      win.dataset.minimized === "true" ||
      win.dataset.closed === "true" ||
      winRect.width === 0 ||
      winRect.height === 0
    ) {
      resetModalPosition(modal);
      return;
    }

    const centerX = winRect.left + winRect.width / 2;
    const centerY = winRect.top + winRect.height / 2;

    if (!modal.classList.contains("desktop-window-modal")) {
      modal.classList.add("desktop-window-modal");
    }

    // Unngå unødvendige DOM-endringer som kan utløse
    // MutationObserver på nytt.
    const left = `${centerX}px`;
    const top = `${centerY}px`;

    if (dialog.style.left !== left) {
      dialog.style.left = left;
    }

    if (dialog.style.top !== top) {
      dialog.style.top = top;
    }

    modalOrigins.set(modal, win);
    positionedModals.add(modal);
  }

  function isModalOpen(modal) {
    return (
      modal.classList.contains("show") &&
      window.getComputedStyle(modal).display !== "none"
    );
  }

  function handleModalChange(modal) {
    if (!modal) return;

    if (!isModalOpen(modal)) {
      if (positionedModals.has(modal)) {
        resetModalPosition(modal);
      }

      return;
    }

    // Behold koblingen dersom modalen allerede er knyttet
    // til et vindu.
    const existingOrigin = modalOrigins.get(modal);

    if (existingOrigin) {
      positionModalInDesktopWindow(modal, existingOrigin);
      return;
    }

    const pending = pendingModalOrigin;

    if (
      pending &&
      Date.now() - pending.timestamp <= MODAL_ORIGIN_TIMEOUT &&
      pending.win.isConnected
    ) {
      positionModalInDesktopWindow(modal, pending.win);

      // Bruk klikkhendelsen bare én gang.
      pendingModalOrigin = null;
      return;
    }

    // Ingen kjent opprinnelse: behold Bootstrap-standard.
    resetModalPosition(modal);
  }

  function trackModalOrigin(event) {
    if (!(event.target instanceof Element)) return;

    const win = event.target.closest(".desktop-window");

    if (
      win &&
      win.style.display !== "none" &&
      win.dataset.minimized !== "true" &&
      win.dataset.closed !== "true"
    ) {
      pendingModalOrigin = {
        win,
        timestamp: Date.now(),
      };
    } else {
      // Ikke arve opphavsvindu fra et tidligere klikk.
      pendingModalOrigin = null;
    }
  }

  function inspectModalNode(node) {
    if (!(node instanceof Element)) return;

    const parentModal = node.matches(".modal")
      ? node
      : node.closest(".modal");

    if (parentModal) {
      handleModalChange(parentModal);
    }

    node.querySelectorAll(".modal").forEach(handleModalChange);
  }

  function repositionDesktopModals() {
    positionedModals.forEach((modal) => {
      const win = modalOrigins.get(modal);

      if (!modal.isConnected || !win) {
        resetModalPosition(modal);
        return;
      }

      if (isModalOpen(modal)) {
        positionModalInDesktopWindow(modal, win);
      } else {
        resetModalPosition(modal);
      }
    });
  }

  // Registrer opphavsvindu før Dash behandler klikket.
  document.addEventListener("click", trackModalOrigin, true);

  // Oppdag både nye modaler og eksisterende modaler som åpnes.
  const modalObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === "attributes") {
        inspectModalNode(mutation.target);
        return;
      }

      mutation.addedNodes.forEach(inspectModalNode);

      if (
        mutation.target instanceof Element &&
        mutation.target.matches(".modal")
      ) {
        handleModalChange(mutation.target);
      }
    });
  });

  modalObserver.observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["class", "style", "aria-hidden"],
  });

  // --------------------------------------------------
  // Oppgavelinjeknapper
  // --------------------------------------------------

  function updateTaskbarButtonTitle(win) {
    const button = getTaskbarButton(win);
    if (!button) return;

    const title = win.querySelector(".desktop-window-title");
    const titleText = title?.innerText.trim() || getModuleId(win);

    const label = button.querySelector(".desktop-taskbar-label");
    const closeButton = button.querySelector(".desktop-taskbar-close");

    if (label && label.textContent !== titleText) {
      label.textContent = titleText;
    }

    button.title = titleText;
    button.setAttribute("aria-label", `Vis vindu: ${titleText}`);

    if (closeButton) {
      closeButton.setAttribute("aria-label", `Lukk ${titleText}`);
    }
  }

  function removeTaskbarButton(win) {
    getTaskbarButton(win)?.remove();
    updateTaskbarMode();
    updateMainLayoutHeight();
  }

  function createTaskbarButton(win) {
    let button = getTaskbarButton(win);

    if (button) {
      updateTaskbarButtonTitle(win);
      return button;
    }

    const titlebarTitle = win.querySelector(".desktop-window-title");
    const titleText = titlebarTitle?.innerText.trim() || getModuleId(win);
    const titleIcon = titlebarTitle?.querySelector("svg");

    button = document.createElement("button");
    button.id = `${getModuleId(win)}-taskbar-button`;
    button.className = "desktop-taskbar-button";
    button.type = "button";
    button.title = titleText;
    button.setAttribute("aria-label", `Vis vindu: ${titleText}`);

    if (titleIcon) {
      button.appendChild(titleIcon.cloneNode(true));
    }

    const label = document.createElement("span");
    label.className = "desktop-taskbar-label";
    label.textContent = titleText;
    button.appendChild(label);

    // Lukkeknapp som vises ved hover.
    const closeButton = document.createElement("span");
    closeButton.className = "desktop-taskbar-close";
    closeButton.setAttribute("role", "button");
    closeButton.setAttribute("tabindex", "0");
    closeButton.setAttribute("aria-label", `Lukk ${titleText}`);
    closeButton.title = "Lukk vindu";
    closeButton.textContent = "×";

    function closeWindow(event) {
      event.preventDefault();
      event.stopPropagation();

      closeDesktopWindow(win);
    }

    closeButton.addEventListener("click", closeWindow);

    closeButton.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        closeWindow(event);
      }
    });

    button.appendChild(closeButton);

    // Klikk på oppgavelinjeknappen minimerer eller gjenoppretter.
    button.addEventListener("click", () => {
      const isVisible = win.style.display !== "none";
      const isMinimized = win.dataset.minimized === "true";

      if (isVisible && !isMinimized) {
        saveWindowState(win);

        win.style.display = "none";
        win.dataset.minimized = "true";
        button.classList.remove("active");
        win.classList.remove("active-window");

        updateMainLayoutHeight();
        return;
      }

      win.style.display = "flex";
      win.dataset.minimized = "false";
      win.dataset.closed = "false";

      clampWindowToWorkArea(win);
      bringToFront(win);
      updateMainLayoutHeight();
    });

    getTaskbar().appendChild(button);

    updateTaskbarMode();
    updateMainLayoutHeight();

    return button;
  }

  // --------------------------------------------------
  // Åpning av desktop-vinduer
  // --------------------------------------------------

  function openWindow(win, parentWindow = null) {
    if (!win) return;

    // Relasjonen bestemmes av vinduet som faktisk åpner
    // målvinduet, ikke av hvilket vindu som tilfeldigvis er aktivt.
    setWindowParent(win, parentWindow);

    initializeWindow(win);
    createTaskbarButton(win);

    win.style.display = "flex";
    win.dataset.minimized = "false";
    win.dataset.closed = "false";

    getWorkArea();
    clampWindowToWorkArea(win);
    bringToFront(win);
    updateMainLayoutHeight();
  }

  // --------------------------------------------------
  // Snap-forhåndsvisning
  // --------------------------------------------------

  function showSnapPreview(rect) {
    if (!rect) {
      snapPreview?.remove();
      snapPreview = null;
      return;
    }

    if (!snapPreview) {
      snapPreview = document.createElement("div");
      snapPreview.className = "desktop-snap-preview";
      snapPreview.setAttribute("aria-hidden", "true");
      document.body.appendChild(snapPreview);
    }

    Object.assign(snapPreview.style, {
      left: `${rect.left}px`,
      top: `${rect.top}px`,
      width: `${rect.width}px`,
      height: `${rect.height}px`,
    });
  }

  // --------------------------------------------------
  // Snap-posisjoner
  // --------------------------------------------------

  function getSnapRect(x, y) {
    const area = getWorkArea();

    const nearLeft = x <= area.left + SNAP_THRESHOLD;
    const nearRight = x >= area.right - SNAP_THRESHOLD;
    const nearTop = y <= area.top + SNAP_THRESHOLD;
    const nearBottom = y >= area.bottom - SNAP_THRESHOLD;

    const halfWidth = area.width / 2;
    const halfHeight = area.height / 2;

    // Hjørnene prioriteres foran sidekantene.
    if (nearLeft && nearTop) {
      return {
        left: area.left,
        top: area.top,
        width: halfWidth,
        height: halfHeight,
      };
    }

    if (nearRight && nearTop) {
      return {
        left: area.left + halfWidth,
        top: area.top,
        width: halfWidth,
        height: halfHeight,
      };
    }

    if (nearLeft && nearBottom) {
      return {
        left: area.left,
        top: area.top + halfHeight,
        width: halfWidth,
        height: halfHeight,
      };
    }

    if (nearRight && nearBottom) {
      return {
        left: area.left + halfWidth,
        top: area.top + halfHeight,
        width: halfWidth,
        height: halfHeight,
      };
    }

    if (nearLeft) {
      return {
        left: area.left,
        top: area.top,
        width: halfWidth,
        height: area.height,
      };
    }

    if (nearRight) {
      return {
        left: area.left + halfWidth,
        top: area.top,
        width: halfWidth,
        height: area.height,
      };
    }

    // Dra til toppen for å maksimere.
    if (nearTop) {
      return {
        left: area.left,
        top: area.top,
        width: area.width,
        height: area.height,
        maximized: true,
      };
    }

    return null;
  }

  function applyWindowRect(win, rect) {
    win.style.left = `${rect.left}px`;
    win.style.top = `${rect.top}px`;
    win.style.width = `${rect.width}px`;
    win.style.height = `${rect.height}px`;
  }

  function snapWindow(win, rect) {
    if (rect.maximized) {
      if (!win.classList.contains("maximized")) {
        if (win.dataset.snapped !== "true") {
          win._desktopRestoreRect = getWindowRect(win);
        }
      }

      win.dataset.snapped = "false";
      win.classList.add("maximized");

      const maximizeButton = document.getElementById(
        `${getModuleId(win)}-window-maximize`
      );

      if (maximizeButton) {
        maximizeButton.title = "Gjenopprett vindu";
      }

      saveWindowState(win);
      return;
    }

    if (!win._desktopRestoreRect) {
      win._desktopRestoreRect = getWindowRect(win);
    }

    win.classList.remove("maximized");
    win.dataset.snapped = "true";

    applyWindowRect(win, rect);

    const maximizeButton = document.getElementById(
      `${getModuleId(win)}-window-maximize`
    );

    if (maximizeButton) {
      maximizeButton.title = "Maksimer vindu";
    }

    saveWindowState(win);
  }

  function restoreSnappedWindowForDrag(win, event) {
    if (win.dataset.snapped !== "true") return;

    const area = getWorkArea();

    const restoreRect = win._desktopRestoreRect || {
      left: area.left + 40,
      top: 40,
      width: Math.min(900, area.width),
      height: Math.min(600, area.height),
    };

    const oldRect = getWindowRect(win);

    const pointerRatio = oldRect.width > 0
      ? (event.clientX - oldRect.left) / oldRect.width
      : 0.5;

    const horizontalOffset = Math.min(
      Math.max(20, restoreRect.width - 40),
      Math.max(20, pointerRatio * restoreRect.width)
    );

    const titlebar = win.querySelector(".desktop-window-titlebar");
    const titlebarHeight = titlebar?.offsetHeight || 36;

    const verticalOffset = Math.min(
      titlebarHeight / 2,
      Math.max(0, restoreRect.height - 20)
    );

    const restoredWidth = Math.min(restoreRect.width, area.width);
    const restoredHeight = Math.min(restoreRect.height, area.height);

    const restoredRect = {
      ...restoreRect,
      width: restoredWidth,
      height: restoredHeight,
      left: Math.max(
        area.left,
        Math.min(
          area.right - restoredWidth,
          event.clientX - horizontalOffset
        )
      ),
      top: Math.max(
        area.top,
        Math.min(
          area.bottom - restoredHeight,
          event.clientY - verticalOffset
        )
      ),
    };

    win.dataset.snapped = "false";
    applyWindowRect(win, restoredRect);
  }

  // --------------------------------------------------
  // Initialisering av hvert vindu
  // --------------------------------------------------

  function initializeWindow(win) {
    if (initializedWindows.has(win)) return;

    initializedWindows.add(win);
    restoreWindowState(win);

    win.addEventListener("pointerdown", () => bringToFront(win));

    const titlebar = win.querySelector(".desktop-window-titlebar");
    if (!titlebar) return;

    // Dobbeltklikk på tittellinjen maksimerer/gjenoppretter.
    titlebar.addEventListener("dblclick", (event) => {
      if (event.target.closest("button")) return;

      const maximizeButton = document.getElementById(
        `${getModuleId(win)}-window-maximize`
      );

      maximizeButton?.click();
    });

    // Flytting, gjenoppretting og snapping.
    titlebar.addEventListener("pointerdown", (event) => {
      if (
        event.button !== 0 ||
        event.target.closest("button")
      ) {
        return;
      }

      const wasMaximized = win.classList.contains("maximized");
      const wasSnapped = win.dataset.snapped === "true";

      // Gjenopprett et maksimert vindu før det dras.
      if (wasMaximized) {
        const area = getWorkArea();

        const saved = win._desktopRestoreRect || {
          left: area.left + 40,
          top: 40,
          width: Math.min(900, area.width),
          height: Math.min(600, area.height),
        };

        const currentRect = getWindowRect(win);

        const pointerRatio = Math.max(
          0.1,
          Math.min(
            0.9,
            (event.clientX - currentRect.left) /
              Math.max(1, currentRect.width)
          )
        );

        const restoredWidth = Math.min(saved.width, area.width);
        const restoredHeight = Math.min(saved.height, area.height);

        win.classList.remove("maximized");
        win.dataset.snapped = "false";

        applyWindowRect(win, {
          ...saved,
          width: restoredWidth,
          height: restoredHeight,
          left: Math.max(
            area.left,
            Math.min(
              area.right - restoredWidth,
              event.clientX - restoredWidth * pointerRatio
            )
          ),
          top: Math.max(
            area.top,
            Math.min(
              area.bottom - restoredHeight,
              event.clientY - 20
            )
          ),
        });

        const maximizeButton = document.getElementById(
          `${getModuleId(win)}-window-maximize`
        );

        if (maximizeButton) {
          maximizeButton.title = "Maksimer vindu";
        }
      } else if (wasSnapped) {
        restoreSnappedWindowForDrag(win, event);
      }

      const startX = event.clientX;
      const startY = event.clientY;

      // Bruk vinduets faktiske viewport-posisjon.
      const startRect = getWindowRect(win);
      const startLeft = startRect.left;
      const startTop = startRect.top;

      try {
        titlebar.setPointerCapture(event.pointerId);
      } catch (error) {
        // Pointer capture er ikke tilgjengelig i alle miljøer.
      }

      function move(moveEvent) {
        const area = getWorkArea();
        const titlebarHeight = titlebar.offsetHeight || 36;

        const left = startLeft + moveEvent.clientX - startX;
        const top = startTop + moveEvent.clientY - startY;

        // Hold alltid en del av vinduet og tittellinjen synlig.
        win.style.left = `${
          Math.min(
            Math.max(left, area.left - win.offsetWidth + 80),
            Math.max(area.left, area.right - Math.min(80, win.offsetWidth))
          )
        }px`;

        win.style.top = `${
          Math.min(
            Math.max(top, area.top),
            Math.max(area.top, area.bottom - titlebarHeight)
          )
        }px`;

        showSnapPreview(
          getSnapRect(moveEvent.clientX, moveEvent.clientY)
        );
      }

      function stop(stopEvent) {
        titlebar.removeEventListener("pointermove", move);
        titlebar.removeEventListener("pointerup", stop);
        titlebar.removeEventListener("pointercancel", cancel);

        showSnapPreview(null);

        if (stopEvent.type === "pointerup") {
          const snapRect = getSnapRect(
            stopEvent.clientX,
            stopEvent.clientY
          );

          if (snapRect) {
            snapWindow(win, snapRect);
          } else {
            win.dataset.snapped = "false";
            clampWindowToWorkArea(win);
            saveWindowState(win);
          }
        } else {
          clampWindowToWorkArea(win);
          saveWindowState(win);
        }

        repositionDesktopModals();
      }

      function cancel(cancelEvent) {
        stop(cancelEvent);
      }

      titlebar.addEventListener("pointermove", move);
      titlebar.addEventListener("pointerup", stop);
      titlebar.addEventListener("pointercancel", cancel);
    });

    // Endring av vindusstørrelse.
    win.querySelectorAll("[data-resize-edge]").forEach((handle) => {
      handle.addEventListener("pointerdown", (event) => {
        if (
          event.button !== 0 ||
          win.classList.contains("maximized")
        ) {
          return;
        }

        event.preventDefault();
        event.stopPropagation();
        bringToFront(win);

        const edge = handle.dataset.resizeEdge;
        const startRect = getWindowRect(win);

        const startX = event.clientX;
        const startY = event.clientY;
        const startLeft = startRect.left;
        const startTop = startRect.top;
        const startWidth = startRect.width;
        const startHeight = startRect.height;

        // Manuell resizing opphever snap.
        win.dataset.snapped = "false";

        try {
          handle.setPointerCapture(event.pointerId);
        } catch (error) {
          // Pointer capture er ikke tilgjengelig i alle miljøer.
        }

        function resize(moveEvent) {
          const area = getWorkArea();
          const dx = moveEvent.clientX - startX;
          const dy = moveEvent.clientY - startY;

          let left = startLeft;
          let top = startTop;
          let width = startWidth;
          let height = startHeight;

          if (edge.includes("e")) {
            width = Math.max(MIN_WINDOW_WIDTH, startWidth + dx);
          }

          if (edge.includes("s")) {
            height = Math.max(MIN_WINDOW_HEIGHT, startHeight + dy);
          }

          if (edge.includes("w")) {
            width = Math.max(MIN_WINDOW_WIDTH, startWidth - dx);
            left = startLeft + startWidth - width;
          }

          if (edge.includes("n")) {
            height = Math.max(MIN_WINDOW_HEIGHT, startHeight - dy);
            top = startTop + startHeight - height;
          }

          // Begrens størrelsen og posisjonen til arbeidsområdet.
          width = Math.min(width, area.width);
          height = Math.min(height, area.height);

          left = Math.max(
            area.left,
            Math.min(left, area.right - width)
          );

          top = Math.max(
            area.top,
            Math.min(top, area.bottom - height)
          );

          win.style.left = `${left}px`;
          win.style.top = `${top}px`;
          win.style.width = `${width}px`;
          win.style.height = `${height}px`;

          repositionDesktopModals();
        }

        function stop() {
          handle.removeEventListener("pointermove", resize);
          handle.removeEventListener("pointerup", stop);
          handle.removeEventListener("pointercancel", stop);

          win._desktopRestoreRect = null;
          saveWindowState(win);
        }

        handle.addEventListener("pointermove", resize);
        handle.addEventListener("pointerup", stop);
        handle.addEventListener("pointercancel", stop);
      });
    });
  }

  // --------------------------------------------------
  // Klikkhåndtering: generisk åpning, sidebar og vindusknapper
  // --------------------------------------------------

  document.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;

    const button = event.target.closest("button[id]");
    if (!button) return;

    // Finn vinduet knappen ligger i.
    // Dette brukes som forelder når knappen åpner et annet vindu.
    const sourceWindow = getOwningWindow(button);

    // Åpne desktop-vindu fra en knapp deklarert i vinduet.
    // Koblingen defineres i Python via data-open-button-id.
    const launchWindow = Array.from(
      document.querySelectorAll(".desktop-window[data-open-button-id]")
    ).find(
      (win) => win.dataset.openButtonId === button.id
    );

    if (launchWindow) {
      openWindow(launchWindow, sourceWindow);
      return;
    }

    const sidebarPrefix = "sidebar-";
    const sidebarSuffix = "-modal-button";

    // Åpne vindu fra sidebaren.
    if (
      button.id.startsWith(sidebarPrefix) &&
      button.id.endsWith(sidebarSuffix)
    ) {
      const moduleId = button.id.slice(
        sidebarPrefix.length,
        -sidebarSuffix.length
      );

      const win = document.getElementById(`${moduleId}-window`);

      if (win) {
        // Sidebar-knapper er utenfor desktop-vinduene.
        // De åpner derfor et vindu uten forelder.
        openWindow(win, null);
      }

      return;
    }

    const actions = [
      ["-window-close", "close"],
      ["-window-minimize", "minimize"],
      ["-window-maximize", "maximize"],
    ];

    for (const [suffix, action] of actions) {
      if (!button.id.endsWith(suffix)) continue;

      const moduleId = button.id.slice(0, -suffix.length);
      const win = document.getElementById(`${moduleId}-window`);

      if (!win) return;

      if (action === "close") {
        closeDesktopWindow(win);
      }

      if (action === "minimize") {
        saveWindowState(win);
        createTaskbarButton(win);

        win.style.display = "none";
        win.dataset.minimized = "true";
        win.classList.remove("active-window");

        getTaskbarButton(win)?.classList.remove("active");

        updateMainLayoutHeight();
      }

      if (action === "maximize") {
        getWorkArea();

        if (!win.classList.contains("maximized")) {
          // Behold opprinnelig størrelse for gjenoppretting.
          if (win.dataset.snapped !== "true") {
            win._desktopRestoreRect = getWindowRect(win);
          }

          win.dataset.snapped = "false";
          win.classList.add("maximized");
          button.title = "Gjenopprett vindu";
        } else {
          win.classList.remove("maximized");
          win.dataset.snapped = "false";

          if (win._desktopRestoreRect) {
            applyWindowRect(win, win._desktopRestoreRect);
          }

          clampWindowToWorkArea(win);
          button.title = "Maksimer vindu";
        }

        saveWindowState(win);
        bringToFront(win);
        repositionDesktopModals();
      }

      return;
    }
  });

  // --------------------------------------------------
  // Oppstart og observasjon av dynamisk opprettede vinduer
  // --------------------------------------------------

  function scanWindows() {
    document.querySelectorAll(".desktop-window").forEach(initializeWindow);
  }

  function initialize() {
    getTaskbar();
    getWorkArea();
    scanWindows();
    updateTaskbarMode();
    updateMainLayoutHeight();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize);
  } else {
    initialize();
  }

  const observer = new MutationObserver(() => {
    getTaskbar();
    getWorkArea();
    scanWindows();

    // Dash kan endre tittelen etter at vinduet er opprettet.
    // Synkroniser derfor eksisterende oppgavelinjeknapper.
    document.querySelectorAll(".desktop-window").forEach((win) => {
      updateTaskbarButtonTitle(win);
    });

    updateTaskbarMode();
    updateMainLayoutHeight();
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
  });

  window.addEventListener("resize", () => {
    getWorkArea();
    updateTaskbarMode();
    updateMainLayoutHeight();

    // Hold åpne vinduer innenfor det nye arbeidsområdet.
    document.querySelectorAll(".desktop-window").forEach((win) => {
      if (
        win.style.display !== "none" &&
        !win.classList.contains("maximized") &&
        win.dataset.snapped !== "true"
      ) {
        clampWindowToWorkArea(win);
      }
    });

    repositionDesktopModals();
  });
})();