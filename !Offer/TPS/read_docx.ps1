Add-Type -AssemblyName 'System.IO.Compression.FileSystem'

function Read-Docx($path) {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($path)
    $entry = $zip.Entries | Where-Object { $_.FullName -eq 'word/document.xml' }
    $stream = $entry.Open()
    $reader = New-Object System.IO.StreamReader($stream)
    $xml = [xml]$reader.ReadToEnd()
    $reader.Close()
    $stream.Close()
    $zip.Dispose()
    $ns = New-Object System.Xml.XmlNamespaceManager($xml.NameTable)
    $ns.AddNamespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
    $paragraphs = $xml.SelectNodes('//w:p', $ns)
    $result = @()
    foreach ($p in $paragraphs) {
        $runs = $p.SelectNodes('.//w:r/w:t', $ns)
        $line = ($runs | ForEach-Object { $_.InnerText }) -join ''
        $result += $line
    }
    return $result -join "`n"
}

$file = $args[0]
Write-Output (Read-Docx $file)
