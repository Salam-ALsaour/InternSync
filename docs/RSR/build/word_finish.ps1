param([string]$InDocx, [string]$OutDocx, [string]$OutPdf)
$ErrorActionPreference = "Stop"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($InDocx, $false, $false)
    foreach ($id in -20, -21, -22) {   # wdStyleTOC1..3: compact entries
        $st = $doc.Styles.Item($id)
        $st.ParagraphFormat.SpaceBefore = 0
        $st.ParagraphFormat.SpaceAfter = 2
        $st.ParagraphFormat.LineSpacingRule = 0
    }
    $doc.Fields.Update() | Out-Null
    foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
    $doc.Repaginate()
    foreach ($toc in $doc.TablesOfContents) { $toc.UpdatePageNumbers() }
    $doc.SaveAs2($OutDocx, 16)
    $doc.ExportAsFixedFormat($OutPdf, 17)
    "pages: " + $doc.ComputeStatistics(2)
    $doc.Close($false)
} finally {
    try { $word.Quit() } catch {}
}
