$path = "c:\Users\savan\OneDrive\Desktop\something_crazy\frontend\src\app\patients\[id]\page.tsx"
$lines = Get-Content -LiteralPath $path

# Keep top 6 lines (Indices 0-5)
$header = $lines[0..5]

# Add the missing import
# Note: Line 6 (index 5) is "import WorkflowDashboard...", so we add below it.
$missingInput = "import { patientsApi, clinicalApi } from '@/lib/api';"

# Get the rest, skipping the junk lines (Indices 6-25, which are lines 7-26)
# Line 26 is the first "PATIENT SNAPSHOT" comment which we want to delete.
# Line 27 (Index 26) is "import Modal..."
$startRestIndex = 26
if ($lines.Count -le $startRestIndex) {
    Write-Host "File is shorter than expected. Aborting script."
    exit 1
}

$rest = $lines[$startRestIndex..($lines.Count-1)]

# Fix indentation for top-level constructs in the rest of the file
$fixedRest = @()
foreach ($line in $rest) {
    # Check if line matches indented imports/exports
    if ($line -match "^\s+(import|export|const)") {
         $line = $line.TrimStart()
    }
    $fixedRest += $line
}

# Find the insertion point for the dashboard component
# We are looking for "{/* PATIENT SNAPSHOT (Phase 2) */}" which corresponds to the original location
$finalLines = @()
$inserted = $false

foreach ($line in $fixedRest) {
    if ($line -match "PATIENT SNAPSHOT" -and -not $inserted) {
        # Determine indentation from the matched line
        $indent = ""
        if ($line -match "^(\s+)") {
            $indent = $matches[1]
        }
        
        # Add the component usage with correct indentation
        $finalLines += "$indent{/* Workflow Engine Dashboard */}"
        $finalLines += "$indent<WorkflowDashboard patientId={id as string} />"
        $finalLines += "" # Empty line
        
        $inserted = $true
    }
    $finalLines += $line
}

# Combine all parts
$newContent = $header + $missingInput + $finalLines

# Write back to file
$newContent | Set-Content -LiteralPath $path -Encoding UTF8
Write-Host "File updated successfully."
