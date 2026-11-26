param([long]$WindowHandle)

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$window = [Windows.Automation.AutomationElement]::FromHandle([IntPtr]::new($WindowHandle))
$descendants = [Windows.Automation.TreeScope]::Descendants
$elementType = [Windows.Automation.AutomationElement]::ControlTypeProperty
$isDocument = [Windows.Automation.PropertyCondition]::new(
    $elementType, [Windows.Automation.ControlType]::Document)
$deadline = [DateTime]::UtcNow.AddSeconds(5)

# Chromium can build the accessibility tree on the first accessibility request.
do {
    $document = $window.FindFirst($descendants, $isDocument)
    if ($null -ne $document) {
        $cache = [Windows.Automation.CacheRequest]::new()
        $cache.Add([Windows.Automation.AutomationElement]::NameProperty)
        $cache.Add([Windows.Automation.AutomationElement]::IsPasswordProperty)
        $cache.Add($elementType)
        $cache.AutomationElementMode = [Windows.Automation.AutomationElementMode]::None
        $scope = $cache.Activate()
        try {
            $nodes = $document.FindAll($descendants, [Windows.Automation.Condition]::TrueCondition)
        } finally {
            $scope.Dispose()
        }
        $lines = [Text.StringBuilder]::new()
        $last = ''
        foreach ($node in $nodes) {
            $properties = $node.Cached
            if ($properties.IsPassword -or $properties.ControlType -eq [Windows.Automation.ControlType]::Edit) {
                continue
            }
            $name = $properties.Name
            if ([string]::IsNullOrWhiteSpace($name) -or $name -ceq $last) { continue }
            $last = $name
            $remaining = 16000 - $lines.Length
            [void]$lines.AppendLine($name.Substring(0, [Math]::Min($remaining, $name.Length)))
            if ($lines.Length -ge 16000) { break }
        }
        if ($lines.Length -gt 0) {
            [Console]::Write($lines.ToString())
            exit 0
        }
    }
    Start-Sleep -Milliseconds 300
} while ([DateTime]::UtcNow -lt $deadline)
exit 2
