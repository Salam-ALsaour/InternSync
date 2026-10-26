/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** The API's address when the web app is hosted apart from it, e.g. https://owner-internsync-api.hf.space */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
