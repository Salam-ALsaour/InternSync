"""Finish a document made by gen_docx.py with LibreOffice instead of Microsoft Word: compact the table-of-contents
entries, build the table of contents, and save the Word file and its PDF. word_finish.ps1 does the same with Word.

    python3 docs/tools/lo_finish.py <in.docx> <out.docx> <out.pdf>

With `-` for <out.docx>, only the PDF is written (for a document whose Word file is final as generated).

Needs LibreOffice (soffice) and its Python bridge (python3-uno). The fonts of the course templates (Calibri, Cambria)
are replaced by their metric-compatible stand-ins (Carlito, Caladea), so line breaks and page numbers match Word."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

import uno
from com.sun.star.beans import PropertyValue

LABEL_WIDTH = 1100000  # EMU (about 1.2 in) for the "Public - عام" box; the template's 0.6 in fits Aptos, not its stand-in


def widen_label(src, dst):
    """Copy the document, widening the centred classification label in the header and footer so it stays on one line.
    (Resizing it through the LibreOffice API makes the layout loop.)"""
    anchor = re.compile(r"<wp:anchor\b.*?</wp:anchor>", re.S)

    def widen(m):
        block = m.group(0)
        if 'descr="Public' not in block:
            return block
        return re.sub(r'(<(?:wp:extent|a:ext)\b[^>]*\bcx=")\d+(")', rf"\g<1>{LABEL_WIDTH}\g<2>", block)

    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if re.fullmatch(r"word/(header|footer)\d*\.xml", item.filename):
                data = anchor.sub(widen, data.decode("utf-8")).encode("utf-8")
            zout.writestr(item, data)


def prop(name, value):
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


def url(path):
    return uno.systemPathToFileUrl(os.path.abspath(path))


def main(src, out_docx, out_pdf):
    profile = tempfile.mkdtemp(prefix="lo-finish-")
    pipe = f"lofinish{os.getpid()}"
    office = subprocess.Popen(["soffice", f"-env:UserInstallation={url(profile)}", "--headless", "--invisible",
                               "--nologo", "--norestore", f"--accept=pipe,name={pipe};urp;"])
    desktop = None
    try:
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
        for _ in range(120):
            try:
                remote = resolver.resolve(f"uno:pipe,name={pipe};urp;StarOffice.ComponentContext")
                break
            except Exception:  # not listening yet
                time.sleep(0.5)
        else:
            raise SystemExit("LibreOffice did not start")
        desktop = remote.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", remote)
        work = os.path.join(profile, "in.docx")
        widen_label(src, work)
        doc = desktop.loadComponentFromURL(url(work), "_blank", 0, (prop("Hidden", True),))
        styles = doc.getStyleFamilies().getByName("ParagraphStyles")
        for name in ("Contents 1", "Contents 2", "Contents 3"):  # compact entries, as word_finish.ps1 does
            if styles.hasByName(name):
                st = styles.getByName(name)
                st.ParaTopMargin, st.ParaBottomMargin = 0, 71  # 1/100 mm: 0 pt before, 2 pt after
        indexes = doc.getDocumentIndexes()
        for _ in range(2):  # the second pass settles page numbers moved by the first
            for i in range(indexes.getCount()):
                indexes.getByIndex(i).update()
            doc.getTextFields().refresh()
            doc.refresh()
        if out_docx != "-":
            doc.storeToURL(url(out_docx), (prop("FilterName", "MS Word 2007 XML"),))
        doc.storeToURL(url(out_pdf), (prop("FilterName", "writer_pdf_Export"),))
        print("pages:", doc.getCurrentController().getPropertyValue("PageCount"))
        doc.close(True)
    finally:
        if desktop is not None:
            try:
                desktop.terminate()
            except Exception:  # the bridge closes as LibreOffice exits
                pass
        try:
            office.wait(timeout=30)
        except subprocess.TimeoutExpired:
            office.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
