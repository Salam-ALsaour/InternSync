/** Arabic (default, RTL) and English (LTR) interface texts (FR-LOC-01, FR-LOC-02). */
import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import ar from "./ar.json";
import en from "./en.json";

const LANG_KEY = "internsync.lang";

function stored(): "ar" | "en" {
  try {
    return localStorage.getItem(LANG_KEY) === "en" ? "en" : "ar";
  } catch {
    return "ar";
  }
}

export function applyLanguage(lang: string): void {
  const value = lang === "en" ? "en" : "ar";
  document.documentElement.lang = value;
  document.documentElement.dir = value === "ar" ? "rtl" : "ltr";
  try {
    localStorage.setItem(LANG_KEY, value);
  } catch {
    /* preference kept for this page only */
  }
  if (i18n.language !== value) void i18n.changeLanguage(value);
}

void i18n.use(initReactI18next).init({
  resources: { ar: { translation: ar }, en: { translation: en } },
  lng: stored(),
  fallbackLng: false,
  interpolation: { escapeValue: false },
  returnNull: false,
});
applyLanguage(stored());

export default i18n;
