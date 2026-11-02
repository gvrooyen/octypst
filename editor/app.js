import { EditorView } from "@codemirror/view";
import { Compartment } from "@codemirror/state";
import { basicSetup } from "codemirror";
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { tags } from "@lezer/highlight";
import { autocompletion } from "@codemirror/autocomplete";
import { typst_lezer, typstTags } from "codemirror-lang-typst/lezer";
import { Vim, vim } from "@replit/codemirror-vim";

const gruvboxDarkHard = [
  EditorView.theme({
    "&": { color: "#ebdbb2", backgroundColor: "#1d2021" },
    ".cm-content": { caretColor: "#fe8019" },
    ".cm-cursor, .cm-dropCursor": { borderLeftColor: "#fe8019" },
    "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection": { backgroundColor: "#504945" },
    ".cm-panels, .cm-tooltip": { color: "#ebdbb2", backgroundColor: "#3c3836" },
    ".cm-tooltip": { border: "1px solid #665c54" },
    ".cm-tooltip-autocomplete > ul > li[aria-selected]": { color: "#fbf1c7", backgroundColor: "#504945" },
    ".cm-searchMatch": { backgroundColor: "#fabd2f55", outline: "1px solid #fabd2f" },
    ".cm-activeLine": { backgroundColor: "#282828" },
    ".cm-selectionMatch": { backgroundColor: "#8ec07c33" },
    ".cm-matchingBracket": { backgroundColor: "#504945" },
    ".cm-gutters": { color: "#928374", backgroundColor: "#282828", border: "none" },
    ".cm-activeLineGutter": { color: "#fabd2f", backgroundColor: "#3c3836" },
    ".cm-foldPlaceholder": { color: "#a89984", backgroundColor: "#3c3836", border: "none" },
  }, { dark: true }),
  // Typst support also installs a light syntax style; keep its parser but override its colours.
  syntaxHighlighting(HighlightStyle.define([
    { tag: tags.keyword, color: "#fb4934 !important" },
    { tag: [tags.name, tags.propertyName, tags.macroName], color: "#fabd2f !important" },
    { tag: tags.function(tags.variableName), color: "#8ec07c !important" },
    { tag: [tags.number, tags.bool, tags.atom], color: "#d3869b !important" },
    { tag: [tags.string, tags.inserted], color: "#b8bb26 !important" },
    { tag: [tags.operator, tags.escape, tags.url, tags.link], color: "#83a598 !important" },
    { tag: [tags.comment, tags.meta], color: "#928374 !important" },
    { tag: tags.heading, color: "#fabd2f !important", fontWeight: "bold" },
    { tag: tags.monospace, color: "#b8bb26 !important" },
    { tag: typstTags.mathDelimiter, color: "#8ec07c !important" },
    { tag: [typstTags.listMarker, typstTags.interpolated], color: "#fe8019 !important" },
    { tag: tags.strong, fontWeight: "bold" },
    { tag: tags.emphasis, fontStyle: "italic" },
    { tag: tags.invalid, color: "#fb4934 !important" },
  ])),
];

const status = document.querySelector("#status");
const saveButton = document.querySelector("#save");
const reloadButton = document.querySelector("#reload");
const previewStatus = document.querySelector("#preview-status");
const preview = document.querySelector("#preview");
const workspace = document.querySelector("#workspace");
const divider = document.querySelector("#divider");
const keymapToggle = document.querySelector("#keymap-toggle");
const keymap = new Compartment();
let keymapMode = localStorage.getItem("octypst-editor-keymap") === "normal" ? "normal" : "vim";
let view;
let revision;
let savedText;
let saving = false;
let previewVersion;

function updateKeymapUI() {
  keymapToggle.dataset.mode = keymapMode;
  keymapToggle.setAttribute("aria-checked", String(keymapMode === "vim"));
  document.querySelector("#vim-hints").hidden = keymapMode !== "vim";
  document.querySelector("#normal-hints").hidden = keymapMode !== "normal";
}

function setStatus(message, state) {
  status.textContent = message;
  status.dataset.state = state;
}

function dirty() {
  return view && view.state.doc.toString() !== savedText;
}

function updateStatus() {
  if (saving) return;
  saveButton.disabled = !dirty();
  setStatus(dirty() ? "Unsaved changes" : "All changes saved", dirty() ? "dirty" : "saved");
  if (dirty() && !previewStatus.hasAttribute("data-error")) previewStatus.textContent = "Preview shows the last saved version.";
  if (!dirty() && previewStatus.textContent === "Preview shows the last saved version.") previewStatus.textContent = "";
}

function showPreview(result) {
  if (!result.ok) {
    previewStatus.dataset.error = "";
    previewStatus.textContent = `Preview could not compile. Your changes are saved.${preview.childElementCount ? " The last successful preview remains visible." : ""}\n${result.message}`;
    return;
  }
  delete previewStatus.dataset.error;
  previewStatus.textContent = dirty() ? "Preview shows the last saved version." : "";
  if (result.version === previewVersion) return;
  previewVersion = result.version;
  const scrollPosition = preview.scrollTop;
  preview.replaceChildren(...Array.from({ length: result.pageCount }, (_, index) => {
    const page = document.createElement("img");
    page.className = "preview-page";
    page.alt = `Report page ${index + 1}`;
    page.src = `/preview/page/${index + 1}.png?v=${result.version}`;
    return page;
  }));
  requestAnimationFrame(() => { preview.scrollTop = scrollPosition; });
}

async function refreshPreview() {
  previewStatus.textContent = "Rendering saved document…";
  try {
    const response = await fetch("/preview/status", { cache: "no-store" });
    if (!response.ok) throw new Error("Preview unavailable. Try reloading the page.");
    showPreview(await response.json());
  } catch (error) {
    previewStatus.dataset.error = "";
    previewStatus.textContent = error.message;
  }
}

async function load() {
  const response = await fetch("/document", { cache: "no-store" });
  if (!response.ok) throw new Error("Could not load the document.");
  const data = await response.json();
  revision = data.revision;
  savedText = data.text;
  if (view) {
    view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: savedText } });
  } else {
    view = new EditorView({
      doc: savedText,
      parent: document.querySelector("#editor"),
      extensions: [
        keymap.of(keymapMode === "vim" ? vim() : []), basicSetup, typst_lezer(), gruvboxDarkHard, autocompletion(),
        EditorView.lineWrapping,
        EditorView.updateListener.of(update => { if (update.docChanged) updateStatus(); }),
      ],
    });
    view.focus();
  }
  reloadButton.disabled = false;
  keymapToggle.disabled = false;
  updateStatus();
  await refreshPreview();
}

async function save() {
  if (!view || saving || !dirty()) return;
  saving = true;
  saveButton.disabled = true;
  reloadButton.disabled = true;
  setStatus("Saving…", "dirty");
  const text = view.state.doc.toString();
  let saved = false;
  try {
    const response = await fetch("/document", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Editor-Save": "1" },
      body: JSON.stringify({ text, revision }),
    });
    if (response.status === 409) {
      setStatus("Changed on server — reload to review", "error");
      return;
    }
    if (!response.ok) throw new Error("Save failed. Your edits are still in this browser.");
    const result = await response.json();
    revision = result.revision;
    savedText = text;
    saved = true;
    showPreview(result.preview);
  } catch (error) {
    setStatus(error.message, "error");
  } finally {
    saving = false;
    reloadButton.disabled = false;
    saveButton.disabled = !dirty();
    if (saved) updateStatus();
  }
}

Vim.defineEx("write", "w", save);
updateKeymapUI();
keymapToggle.addEventListener("click", () => {
  keymapMode = keymapMode === "vim" ? "normal" : "vim";
  view.dispatch({ effects: keymap.reconfigure(keymapMode === "vim" ? vim() : []) });
  localStorage.setItem("octypst-editor-keymap", keymapMode);
  updateKeymapUI();
  view.focus();
});
saveButton.addEventListener("click", save);
reloadButton.addEventListener("click", async () => {
  if (dirty() && !confirm("Discard your unsaved changes and reload the server version?")) return;
  try { await load(); } catch (error) { setStatus(error.message, "error"); }
});

function setSplit(percent) {
  const value = Math.max(25, Math.min(75, percent));
  workspace.style.setProperty("--editor-width", `${value}%`);
  divider.setAttribute("aria-valuenow", String(Math.round(value)));
}

divider.addEventListener("pointerdown", event => {
  if (event.button !== 0) return;
  divider.setPointerCapture(event.pointerId);
  workspace.classList.add("resizing");
  event.preventDefault();
});
divider.addEventListener("pointermove", event => {
  if (!divider.hasPointerCapture(event.pointerId)) return;
  const bounds = workspace.getBoundingClientRect();
  setSplit((event.clientX - bounds.left) / bounds.width * 100);
});
divider.addEventListener("lostpointercapture", () => workspace.classList.remove("resizing"));
divider.addEventListener("pointerup", event => divider.releasePointerCapture(event.pointerId));
divider.addEventListener("keydown", event => {
  if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
  setSplit(Number(divider.getAttribute("aria-valuenow")) + (event.key === "ArrowRight" ? 5 : -5));
  event.preventDefault();
});
window.addEventListener("keydown", event => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
    event.preventDefault();
    save();
  }
}, true);
window.addEventListener("beforeunload", event => { if (dirty()) event.preventDefault(); });
load().catch(error => setStatus(error.message, "error"));
