"use strict";

(function () {
  var sidebarStorageKey = "resumeAI.sidebarMini";
  var themeStorageKey = "resumeAI.theme";
  var desktopMedia = "(min-width: 992px)";

  function onReady(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback);
      return;
    }

    callback();
  }

  function isDesktop() {
    return window.matchMedia(desktopMedia).matches;
  }

  function canUseStorage() {
    try {
      var testKey = sidebarStorageKey + ".test";
      window.localStorage.setItem(testKey, "1");
      window.localStorage.removeItem(testKey);
      return true;
    } catch (error) {
      return false;
    }
  }

  function getSavedMiniState(storageAvailable) {
    if (!storageAvailable) {
      return false;
    }

    return window.localStorage.getItem(sidebarStorageKey) === "true";
  }

  function saveMiniState(storageAvailable, isMini) {
    if (storageAvailable) {
      window.localStorage.setItem(sidebarStorageKey, String(isMini));
    }
  }

  function getPreferredTheme(storageAvailable) {
    var savedTheme = storageAvailable ? window.localStorage.getItem(themeStorageKey) : "";

    if (savedTheme === "dark" || savedTheme === "light") {
      return savedTheme;
    }

    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }

    return "light";
  }

  function initPasswordToggles() {
    var buttons = document.querySelectorAll("[data-password-toggle]");
    Array.prototype.forEach.call(buttons, function (button) {
      var target = document.querySelector(button.getAttribute("data-password-target"));
      if (!target) {
        return;
      }

      button.addEventListener("click", function () {
        var isPassword = target.type === "password";
        target.type = isPassword ? "text" : "password";
        button.setAttribute("aria-label", isPassword ? "Hide password" : "Show password");

        var icon = button.querySelector("i");
        if (icon) {
          icon.className = isPassword ? "bi bi-eye-slash" : "bi bi-eye";
        }
      });
    });
  }

  function initDropZones() {
    var zones = document.querySelectorAll("[data-drop-zone]");
    Array.prototype.forEach.call(zones, function (zone) {
      var input = document.querySelector(zone.getAttribute("data-drop-input") || 'input[type="file"]');
      var filenameEl = zone.querySelector("[data-drop-filename]");
      if (!input) {
        return;
      }

      function syncFile() {
        var file = input.files && input.files[0];
        if (file) {
          zone.classList.add("has-file");
          if (filenameEl) {
            filenameEl.textContent = file.name;
          }
        } else {
          zone.classList.remove("has-file");
          if (filenameEl) {
            filenameEl.textContent = "";
          }
        }
      }

      input.addEventListener("change", syncFile);

      zone.addEventListener("click", function () {
        input.click();
      });

      ["dragenter", "dragover"].forEach(function (eventName) {
        zone.addEventListener(eventName, function (event) {
          event.preventDefault();
          zone.classList.add("dragover");
        });
      });

      ["dragleave", "drop"].forEach(function (eventName) {
        zone.addEventListener(eventName, function (event) {
          event.preventDefault();
          zone.classList.remove("dragover");
        });
      });

      zone.addEventListener("drop", function (event) {
        var files = event.dataTransfer && event.dataTransfer.files;
        if (files && files.length) {
          input.files = files;
          syncFile();
        }
      });
    });
  }

  onReady(function () {
    var body = document.body;
    var sidebarToggle = document.querySelector("[data-sidebar-toggle]");
    var themeToggles = document.querySelectorAll("[data-theme-toggle]");
    var themeIcons = document.querySelectorAll("[data-theme-icon]");
    var closeButtons = document.querySelectorAll("[data-sidebar-close]");
    var sidebarLinks = document.querySelectorAll(".sidebar-nav .nav-link");
    var mediaQuery = window.matchMedia(desktopMedia);
    var storageAvailable = canUseStorage();




    function updateThemeControls(theme) {
      var nextTheme = theme === "dark" ? "light" : "dark";
      var label = "Switch to " + nextTheme + " mode";
      var iconClass = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";

      Array.prototype.forEach.call(themeToggles, function (button) {
        button.setAttribute("aria-label", label);
        button.setAttribute("title", label);
      });

      Array.prototype.forEach.call(themeIcons, function (icon) {
        icon.className = iconClass;
      });
    }

    function applyTheme(theme) {
      document.documentElement.setAttribute("data-theme", theme);
      document.documentElement.setAttribute("data-bs-theme", theme);

      if (storageAvailable) {
        window.localStorage.setItem(themeStorageKey, theme);
      }

      updateThemeControls(theme);
    }

    function initThemeToggle() {
      applyTheme(getPreferredTheme(storageAvailable));

      Array.prototype.forEach.call(themeToggles, function (button) {
        button.addEventListener("click", function () {
          var currentTheme = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
          applyTheme(currentTheme === "dark" ? "light" : "dark");
        });
      });
    }

    initThemeToggle();
    initPasswordToggles();
    initDropZones();

    if (!sidebarToggle) {
      return;
    }

    function setClass(element, className, enabled) {
      if (enabled) {
        element.classList.add(className);
      } else {
        element.classList.remove(className);
      }
    }

    function setToggleExpanded() {
      var expanded = isDesktop()
        ? !body.classList.contains("sidebar-mini")
        : body.classList.contains("sidebar-open");

      sidebarToggle.setAttribute("aria-expanded", String(expanded));
    }

    function closeMobileSidebar() {
      body.classList.remove("sidebar-open");
      setToggleExpanded();
    }

    function toggleSidebar() {
      if (isDesktop()) {
        body.classList.toggle("sidebar-mini");
        saveMiniState(storageAvailable, body.classList.contains("sidebar-mini"));
      } else {
        body.classList.toggle("sidebar-open");
      }

      setToggleExpanded();
    }

    function addCloseHandlers(items) {
      Array.prototype.forEach.call(items, function (item) {
        item.addEventListener("click", function () {
          if (!isDesktop()) {
            closeMobileSidebar();
          }
        });
      });
    }

    if (getSavedMiniState(storageAvailable) && isDesktop()) {
      body.classList.add("sidebar-mini");
    }

    sidebarToggle.addEventListener("click", toggleSidebar);
    addCloseHandlers(closeButtons);
    addCloseHandlers(sidebarLinks);
    setToggleExpanded();

    function handleBreakpointChange() {
      if (isDesktop()) {
        body.classList.remove("sidebar-open");
        setClass(body, "sidebar-mini", getSavedMiniState(storageAvailable));
      } else {
        body.classList.remove("sidebar-mini");
      }

      setToggleExpanded();
    }

    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener("change", handleBreakpointChange);
    } else if (mediaQuery.addListener) {
      mediaQuery.addListener(handleBreakpointChange);
    }
  });
})();
