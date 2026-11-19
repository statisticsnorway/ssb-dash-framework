(() => {
  const initializedWindows = new WeakSet();
  let topZIndex = 1050;
  let snapPreview = null;
  let snapAssist = null;

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

    if (parentWindow && parentWindow !== childWindow) {
      childWindow.dataset.parentWindow = parentWindow.id;
    } else {
      delete childWindow.dataset.parentWindow;
    }
  }

  function closeDesktopWindow(win, visited = new Set()) {
    if (!win || visited.has(win)) return;

    visited.add(win);

    document
      .querySelectorAll(".desktop-window[data-parent-window]")
      .forEach((childWindow) => {
        if (childWindow.dataset.parentWindow === win.id) {
          closeDesktopWindow(childWindow, visited);
        }
      });

    saveWindowState(win);

    win.style.display = "none";
    win.dataset.minimized = "false";
    win.dataset.closed = "true";
    win.classList.remove("active-window");

    if (win.dataset.snapped === "true") {
      win.dataset.snapped = "false";
      delete win.dataset.snapCells;
    }

    removeTaskbarButton(win);
    closeSnapAssist();
  }

  // --------------------------------------------------
  // Lukk underordnede vinduer ved nytt søk
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

    const childWindows = Array.from(
      document.querySelectorAll(
        ".desktop-window[data-parent-window]"
      )
    );

    const childWindowIds = new Set(
      childWindows.map((win) => win.id)
    );

    childWindows.forEach((win) => {
      if (!childWindowIds.has(win.dataset.parentWindow)) {
        closeDesktopWindow(win);
      }
    });
  };

  // --------------------------------------------------
  // Arbeidsområde
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
        snapCells: win.dataset.snapCells || null,
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

      if (state.snapCells) {
        win.dataset.snapCells = state.snapCells;
      } else {
        delete win.dataset.snapCells;
      }

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
      dialog.style.removeProperty("left");
      dialog.style.removeProperty("top");
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
      pendingModalOrigin = null;
      return;
    }

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

  document.addEventListener("click", trackModalOrigin, true);

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

    button.addEventListener("click", () => {
      const isVisible =
        win.style.display !== "none" &&
        win.dataset.minimized !== "true" &&
        win.dataset.closed !== "true";

      const isActive = win.classList.contains("active-window");

      // Vinduet er synlig, men ligger bak et annet vindu.
      // Hent det frem i stedet for å minimere det.
      if (isVisible && !isActive) {
        bringToFront(win);
        return;
      }

      // Vinduet er allerede aktivt: minimer det.
      if (isVisible && isActive) {
        saveWindowState(win);

        win.style.display = "none";
        win.dataset.minimized = "true";
        win.classList.remove("active-window");
        button.classList.remove("active");

        closeSnapAssist();
        updateMainLayoutHeight();
        return;
      }

      // Vinduet er minimert eller skjult: åpne det igjen.
      win.style.display = "flex";
      win.dataset.minimized = "false";
      win.dataset.closed = "false";

      clampWindowToWorkArea(win);
      bringToFront(win);
      repositionDesktopModals();
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

    setWindowParent(win, parentWindow);

    initializeWindow(win);
    createTaskbarButton(win);

    win.dataset.opened = "true";
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

    if (nearLeft && nearTop) {
      return {
        left: area.left,
        top: area.top,
        width: halfWidth,
        height: halfHeight,
        snapCells: ["tl"],
      };
    }

    if (nearRight && nearTop) {
      return {
        left: area.left + halfWidth,
        top: area.top,
        width: halfWidth,
        height: halfHeight,
        snapCells: ["tr"],
      };
    }

    if (nearLeft && nearBottom) {
      return {
        left: area.left,
        top: area.top + halfHeight,
        width: halfWidth,
        height: halfHeight,
        snapCells: ["bl"],
      };
    }

    if (nearRight && nearBottom) {
      return {
        left: area.left + halfWidth,
        top: area.top + halfHeight,
        width: halfWidth,
        height: halfHeight,
        snapCells: ["br"],
      };
    }

    if (nearLeft) {
      return {
        left: area.left,
        top: area.top,
        width: halfWidth,
        height: area.height,
        snapCells: ["tl", "bl"],
      };
    }

    if (nearRight) {
      return {
        left: area.left + halfWidth,
        top: area.top,
        width: halfWidth,
        height: area.height,
        snapCells: ["tr", "br"],
      };
    }

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

  // --------------------------------------------------
  // Snap Assist: ledige områder
  // --------------------------------------------------

  const SNAP_ZONES = [
    { cells: ["tl", "tr", "bl", "br"], name: "Hele arbeidsområdet" },
    { cells: ["tl", "bl"], name: "Venstre halvdel" },
    { cells: ["tr", "br"], name: "Høyre halvdel" },
    { cells: ["tl", "tr"], name: "Øvre halvdel" },
    { cells: ["bl", "br"], name: "Nedre halvdel" },
    { cells: ["tl"], name: "Øverst til venstre" },
    { cells: ["tr"], name: "Øverst til høyre" },
    { cells: ["bl"], name: "Nederst til venstre" },
    { cells: ["br"], name: "Nederst til høyre" },
  ];

  function getOccupiedSnapCells() {
    const occupied = new Set();

    document.querySelectorAll(
      '.desktop-window[data-snapped="true"]'
    ).forEach((win) => {
      if (
        win.style.display === "none" ||
        win.dataset.minimized === "true" ||
        win.dataset.closed === "true"
      ) {
        return;
      }

      let cells = [];

      try {
        cells = JSON.parse(win.dataset.snapCells || "[]");
      } catch (error) {
        // Ugyldig lagret soneinformasjon ignoreres.
      }

      cells.forEach((cell) => occupied.add(cell));
    });

    return occupied;
  }

  function getAvailableSnapZones() {
    const occupied = getOccupiedSnapCells();

    return SNAP_ZONES
      .filter((zone) =>
        zone.cells.every((cell) => !occupied.has(cell))
      )
      .sort((a, b) => b.cells.length - a.cells.length);
  }

  function getSnapZoneRect(zone) {
    const area = getWorkArea();
    const columns = zone.cells.map((cell) =>
      cell.endsWith("r") ? 1 : 0
    );
    const rows = zone.cells.map((cell) =>
      cell.startsWith("b") ? 1 : 0
    );

    const minColumn = Math.min(...columns);
    const maxColumn = Math.max(...columns);
    const minRow = Math.min(...rows);
    const maxRow = Math.max(...rows);

    const halfWidth = area.width / 2;
    const halfHeight = area.height / 2;

    return {
      left: area.left + minColumn * halfWidth,
      top: area.top + minRow * halfHeight,
      width: (maxColumn - minColumn + 1) * halfWidth,
      height: (maxRow - minRow + 1) * halfHeight,
      snapCells: zone.cells,
    };
  }

  // --------------------------------------------------
  // Snap Assist: vindusforslag
  // --------------------------------------------------

  function closeSnapAssist() {
    snapAssist?.remove();
    snapAssist = null;
  }

  // Klikk utenfor Snap Assist, eller på et område som ikke
  // er et vindusvalg, lukker valgvisningen.
  document.addEventListener("click", (event) => {
    if (!snapAssist) return;

    const clickedElement = event.target;

    if (
      clickedElement instanceof Element &&
      snapAssist.contains(clickedElement) &&
      clickedElement.closest(".desktop-snap-assist-item")
    ) {
      return;
    }

    closeSnapAssist();
  });

  function getSnapCandidates(currentWindow) {
    return Array.from(
      document.querySelectorAll(".desktop-window")
    ).filter((win) => (
      win !== currentWindow &&
      win.dataset.opened === "true" &&
      win.dataset.closed !== "true" &&
      win.dataset.snapped !== "true"
    ));
  }

  function showSnapAssist(currentWindow) {
    closeSnapAssist();

    const availableZones = getAvailableSnapZones();
    if (!availableZones.length) return;

    const candidates = getSnapCandidates(currentWindow);
    if (!candidates.length) return;

    const zone = availableZones[0];
    const rect = getSnapZoneRect(zone);

    snapAssist = document.createElement("div");
    snapAssist.className = "desktop-snap-assist";
    snapAssist.setAttribute("role", "dialog");
    snapAssist.setAttribute("aria-label", "Velg et vindu å snappe");

    Object.assign(snapAssist.style, {
      left: `${rect.left}px`,
      top: `${rect.top}px`,
      width: `${rect.width}px`,
      height: `${rect.height}px`,
    });

    const content = document.createElement("div");
    content.className = "desktop-snap-assist-content";

    const heading = document.createElement("div");
    heading.className = "desktop-snap-assist-heading";
    heading.textContent = "Velg et vindu";

    content.appendChild(heading);

    const list = document.createElement("div");
    list.className = "desktop-snap-assist-list";

    candidates.forEach((win) => {
      const titleElement = win.querySelector(".desktop-window-title");
      const title = titleElement?.innerText.trim() || getModuleId(win);
      const icon = titleElement?.querySelector("svg");

      const button = document.createElement("button");
      button.type = "button";
      button.className = "desktop-snap-assist-item";
      button.title = `Snap ${title}`;

      const thumbnail = document.createElement("div");
      thumbnail.className = "desktop-snap-assist-thumbnail";

      if (icon) {
        thumbnail.appendChild(icon.cloneNode(true));
      } else {
        thumbnail.textContent = title.charAt(0).toUpperCase();
      }

      const label = document.createElement("span");
      label.className = "desktop-snap-assist-label";
      label.textContent = title;

      button.appendChild(thumbnail);
      button.appendChild(label);

      button.addEventListener("click", () => {
        if (
          !win.isConnected ||
          win.dataset.closed === "true"
        ) {
          closeSnapAssist();
          return;
        }

        closeSnapAssist();

        win.style.display = "flex";
        win.dataset.minimized = "false";
        win.dataset.closed = "false";

        snapWindow(win, rect);
        bringToFront(win);
        repositionDesktopModals();

        requestAnimationFrame(() => {
          showSnapAssist(win);
        });
      });

      list.appendChild(button);
    });

    content.appendChild(list);
    snapAssist.appendChild(content);
    document.body.appendChild(snapAssist);
  }

  // --------------------------------------------------
  // Plassering og snapping av vinduer
  // --------------------------------------------------

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
      delete win.dataset.snapCells;
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
    win.dataset.snapCells = JSON.stringify(rect.snapCells || []);

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
    delete win.dataset.snapCells;

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

      const startX = event.clientX;
      const startY = event.clientY;

      const wasMaximized = win.classList.contains("maximized");
      const wasSnapped = win.dataset.snapped === "true";

      const dragThreshold = 5;
      let isDragging = false;

      let startLeft = 0;
      let startTop = 0;

      try {
        titlebar.setPointerCapture(event.pointerId);
      } catch (error) {
        // Pointer capture er ikke tilgjengelig i alle miljøer.
      }

      function startDrag() {
        if (isDragging) return;

        isDragging = true;

        closeSnapAssist();

        // Gjenopprett først når brukeren faktisk begynner å dra.
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
              (startX - currentRect.left) /
                Math.max(1, currentRect.width)
            )
          );

          const restoredWidth = Math.min(saved.width, area.width);
          const restoredHeight = Math.min(saved.height, area.height);

          win.classList.remove("maximized");
          win.dataset.snapped = "false";
          delete win.dataset.snapCells;

          applyWindowRect(win, {
            ...saved,
            width: restoredWidth,
            height: restoredHeight,
            left: Math.max(
              area.left,
              Math.min(
                area.right - restoredWidth,
                startX - restoredWidth * pointerRatio
              )
            ),
            top: Math.max(
              area.top,
              Math.min(
                area.bottom - restoredHeight,
                startY - 20
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
          restoreSnappedWindowForDrag(win, {
            clientX: startX,
            clientY: startY,
          });
        }

        const startRect = getWindowRect(win);
        startLeft = startRect.left;
        startTop = startRect.top;
      }

      function move(moveEvent) {
        const dx = moveEvent.clientX - startX;
        const dy = moveEvent.clientY - startY;

        // Et vanlig klikk skal ikke flytte eller gjenopprette vinduet.
        if (
          !isDragging &&
          Math.hypot(dx, dy) < dragThreshold
        ) {
          return;
        }

        if (!isDragging) {
          startDrag();
        }

        const area = getWorkArea();
        const titlebarHeight = titlebar.offsetHeight || 36;

        const left = startLeft + dx;
        const top = startTop + dy;

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

        // Hvis brukeren bare klikket, skal vinduet beholde
        // nøyaktig samme størrelse og plassering.
        if (!isDragging) {
          return;
        }

        showSnapPreview(null);

        if (stopEvent.type === "pointerup") {
          const snapRect = getSnapRect(
            stopEvent.clientX,
            stopEvent.clientY
          );

          if (snapRect) {
            snapWindow(win, snapRect);

            if (!snapRect.maximized) {
              requestAnimationFrame(() => {
                showSnapAssist(win);
              });
            } else {
              closeSnapAssist();
            }
          } else {
            win.dataset.snapped = "false";
            delete win.dataset.snapCells;

            clampWindowToWorkArea(win);
            saveWindowState(win);
            closeSnapAssist();
          }
        } else {
          clampWindowToWorkArea(win);
          saveWindowState(win);
          closeSnapAssist();
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
        closeSnapAssist();
        bringToFront(win);

        const edge = handle.dataset.resizeEdge;
        const startRect = getWindowRect(win);

        const startX = event.clientX;
        const startY = event.clientY;
        const startLeft = startRect.left;
        const startTop = startRect.top;
        const startWidth = startRect.width;
        const startHeight = startRect.height;

        win.dataset.snapped = "false";
        delete win.dataset.snapCells;

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

    // --------------------------------------------------
    // Generisk åpning via data-open-button-id
    // --------------------------------------------------

    const launchWindow = Array.from(
      document.querySelectorAll(".desktop-window[data-open-button-id]")
    ).find((win) => {
      const openButton = document.getElementById(
        win.dataset.openButtonId
      );

      return openButton && openButton.contains(event.target);
    });

    if (launchWindow) {
      const sourceWindow = getOwningWindow(event.target);
      openWindow(launchWindow, sourceWindow);
      return;
    }

    // --------------------------------------------------
    // Sidebar og vindusknapper
    // --------------------------------------------------

    const button = event.target.closest("button[id]");
    if (!button) return;

    const sidebarPrefix = "sidebar-";
    const sidebarSuffix = "-modal-button";

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

        closeSnapAssist();
        updateMainLayoutHeight();
      }

      if (action === "maximize") {
        closeSnapAssist();
        getWorkArea();

        if (!win.classList.contains("maximized")) {
          if (win.dataset.snapped !== "true") {
            win._desktopRestoreRect = getWindowRect(win);
          }

          win.dataset.snapped = "false";
          delete win.dataset.snapCells;

          win.classList.add("maximized");
          button.title = "Gjenopprett vindu";
        } else {
          win.classList.remove("maximized");
          win.dataset.snapped = "false";
          delete win.dataset.snapCells;

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
    closeSnapAssist();
  });
})();