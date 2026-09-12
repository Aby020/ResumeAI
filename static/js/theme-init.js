/**
 * ResumeAI — theme bootstrap (runs synchronously in <head>).
 *
 * Applies the saved (or OS-preferred) theme to <html> before first paint so
 * there is no flash of the wrong theme and no inconsistent Bootstrap theme
 * on auth pages. Mirrors the storage/fallback logic in main.js.
 */
(function () {
  "use strict";

  var themeStorageKey = "resumeAI.theme";

  function canUseStorage() {
    try {
      var testKey = themeStorageKey + ".test";
      window.localStorage.setItem(testKey, "1");
      window.localStorage.removeItem(testKey);
      return true;
    } catch (e) {
      return false;
    }
  }

  function getPreferredTheme() {
    if (canUseStorage()) {
      var saved = window.localStorage.getItem(themeStorageKey);
      if (saved === "dark" || saved === "light") {
        return saved;
      }
    }
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      return "dark";
    }
    return "light";
  }

  var theme = getPreferredTheme();
  document.documentElement.setAttribute("data-theme", theme);
  document.documentElement.setAttribute("data-bs-theme", theme);
})();