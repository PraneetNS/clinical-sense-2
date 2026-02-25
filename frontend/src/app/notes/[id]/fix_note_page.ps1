$path = "c:\Users\savan\OneDrive\Desktop\something_crazy\frontend\src\app\notes\[id]\page.tsx"
$lines = Get-Content -LiteralPath $path

# Identify lines to remove
# We look for the "bad" import line and the line before the "Deep Analysis" button container
$badStart = -1
$badEnd = -1

for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "import \{notesApi, workflowApi\} from") {
        # This is likely the start of the inserted junk block in the middle of file
        # Check if it's indented (since it's inside the function)
        if ($lines[$i] -match "^\s+import") {
            $badStart = $i
        }
    }
    # The junk ends before line 133 "<div className=... gap-4...>"
    # Actually, verify looking at the structure.
    # The inserted junk has a <nav> ... <div (gap 6)> ... </div> (closing the gap 6 div)
    # The next line is <div (gap 4)> which is valid.
    
    if ($badStart -ne -1 -and $badEnd -eq -1) {
         if ($lines[$i] -match "className=`"flex items-center gap-4`"") {
             # This line (133 in view) is GOOD. The line before it is the end of junk.
             $badEnd = $i - 1
             break
         }
    }
}

if ($badStart -eq -1 -or $badEnd -eq -1) {
    Write-Host "Could not identify bad block. Aborting."
    exit 1
}

# Construct new content
$newLines = @()
$handlerAdded = $false

for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    
    # 1. Skip bad block
    if ($i -ge $badStart -and $i -le $badEnd) {
        continue
    }
    
    # 2. Fix Import
    if ($line -match "^import \{ notesApi \} from '@/lib/api';") {
        $line = "import { notesApi, workflowApi } from '@/lib/api';"
    }
    
    # 3. Insert Handler
    if ($line -match "const \{ showToast \} = useToast\(\);") {
        $newLines += $line
        $newLines += ""
        $newLines += "    const handleRunWorkflowAnalysis = async () => {"
        $newLines += "        try {"
        $newLines += "            showToast(`"Running Clinical Workflow Analysis...`", `"info`");"
        $newLines += "            await workflowApi.runAnalysis(id as string);"
        $newLines += "            showToast(`"Workflow Analysis Complete`", `"success`");"
        $newLines += "        } catch (err) {"
        $newLines += "            showToast(`"Analysis Failed`", `"error`");"
        $newLines += "        }"
        $newLines += "    };"
        continue
    }
    
    $newLines += $line
}

$newLines | Set-Content -LiteralPath $path -Encoding UTF8
Write-Host "File fixed."
