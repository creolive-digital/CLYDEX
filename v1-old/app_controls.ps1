# Discover or operate on one accessibility control in a selected Windows window.
$ErrorActionPreference = 'Stop'
$utf8 = [Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = $utf8
[Console]::OutputEncoding = $utf8
$request = [Console]::In.ReadToEnd() | ConvertFrom-Json
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$root = [Windows.Automation.AutomationElement]::FromHandle([IntPtr]::new([long]$request.hwnd))
if ($root.Current.ProcessId -ne $request.pid) { throw 'The selected window changed.' }

$element = [Windows.Automation.AutomationElement]
$cache = [Windows.Automation.CacheRequest]::new()
foreach ($key in @('Name','AutomationId','ControlType','IsEnabled','IsPassword','IsOffscreen',
                   'RuntimeId','IsInvokePatternAvailable','IsTogglePatternAvailable',
                   'IsExpandCollapsePatternAvailable','IsSelectionItemPatternAvailable',
                   'IsValuePatternAvailable','ClassName','NativeWindowHandle')) {
    $property = $key + 'Property'
    $cache.Add($element::$property)
}
$scope = $cache.Activate()
try {
    $nodes = $root.FindAll([Windows.Automation.TreeScope]::Descendants,
                           [Windows.Automation.Condition]::TrueCondition)
} finally {
    $scope.Dispose()
}
if ($request.mode -ne 'inspect') {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class ClydexNativeControl {
    const uint BM_CLICK = 0xF5, WM_GETTEXTLENGTH = 14, EM_SETSEL = 0xB1, EM_REPLACESEL = 0xC2;
    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr SendMessageTimeout(IntPtr hwnd, uint msg, IntPtr w, string text,
        uint flags, uint timeout, out IntPtr result);
    [DllImport("user32.dll", EntryPoint="SendMessageTimeoutW", SetLastError=true)]
    static extern IntPtr SendNumber(IntPtr hwnd, uint msg, IntPtr w, IntPtr l,
        uint flags, uint timeout, out IntPtr result);
    [DllImport("user32.dll", EntryPoint="GetWindowLongW")]
    static extern int GetStyle(IntPtr hwnd, int index);
    [DllImport("user32.dll")] static extern bool IsChild(IntPtr parent, IntPtr child);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint processId);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)]
    static extern int GetWindowText(IntPtr hwnd, StringBuilder title, int length);
    public static bool MatchesWindow(IntPtr hwnd, uint expectedPid, string expectedTitle) {
        uint pid;
        var title = new StringBuilder(expectedTitle.Length + 2);
        GetWindowText(hwnd, title, title.Capacity);
        return GetWindowThreadProcessId(hwnd, out pid) != 0 &&
            pid == expectedPid && title.ToString() == expectedTitle;
    }
    public static void Click(IntPtr parent, IntPtr hwnd) {
        IntPtr ignored;
        if (!IsChild(parent, hwnd) ||
            SendNumber(hwnd, BM_CLICK, IntPtr.Zero, IntPtr.Zero, 2, 2000, out ignored) == IntPtr.Zero)
            throw new InvalidOperationException("The button did not confirm the operation.");
    }
    public static void Append(IntPtr parent, IntPtr hwnd, string text) {
        if (!IsChild(parent, hwnd) || (GetStyle(hwnd, -16) & 0x820) != 0)
            throw new InvalidOperationException("The field cannot be edited.");
        IntPtr length, ignored;
        if (SendNumber(hwnd, WM_GETTEXTLENGTH, IntPtr.Zero, IntPtr.Zero, 2, 2000, out length) == IntPtr.Zero ||
            SendNumber(hwnd, EM_SETSEL, length, length, 2, 2000, out ignored) == IntPtr.Zero ||
            SendMessageTimeout(hwnd, EM_REPLACESEL, new IntPtr(1), text, 2, 2000, out ignored) == IntPtr.Zero ||
            SendNumber(hwnd, WM_GETTEXTLENGTH, IntPtr.Zero, IntPtr.Zero, 2, 2000, out ignored) == IntPtr.Zero ||
            ignored.ToInt64() < length.ToInt64() + text.Replace("\r\n", "\n").Length)
            throw new InvalidOperationException("The editor did not confirm the operation.");
    }
}
'@
}
$choices = [Collections.Generic.List[object]]::new()
foreach ($node in $nodes) {
    $item = $node.Cached
    if ($item.IsOffscreen -or !$item.IsEnabled -or $item.IsPassword) { continue }
    $kind = $item.ControlType.ProgrammaticName.Replace('ControlType.', '')
    $nativeEdit = $item.NativeWindowHandle -and $item.ClassName -match '^(Edit$|RichEdit)'
    $name = $item.Name
    if ($nativeEdit -and $kind -eq 'Pane') {
        # A legacy edit's window caption is its document text.
        $kind = 'Edit'
        $name = ''
    }
    $editable = $nativeEdit -or ($kind -in 'Edit','Document' -and
                $node.GetCachedPropertyValue($element::IsValuePatternAvailableProperty))
    $action = ''
    foreach ($pattern in @('Invoke','Toggle','ExpandCollapse','SelectionItem')) {
        $property = 'Is' + $pattern + 'PatternAvailableProperty'
        if ($node.GetCachedPropertyValue($element::$property)) { $action = $pattern; break }
    }
    if (!$action -and $item.NativeWindowHandle -and $item.ClassName -eq 'Button') {
        $action = 'NativeButton'
        if ($kind -eq 'Pane') { $kind = 'Button' }
    }
    if (!$editable -and !$action) { continue }
    $id = $node.GetCachedPropertyValue($element::RuntimeIdProperty) -join '.'
    if (!$id) { continue }
    $choice = [ordered]@{ id=$id; name=$name; key=$item.AutomationId; kind=$kind
                          action=$action; editable=[bool]$editable }
    if ($request.mode -eq 'inspect') {
        $choices.Add($choice)
        continue
    }
    if ($id -cne $request.control.id -or $name -cne $request.control.name -or
        $kind -ne $request.control.kind -or $item.AutomationId -cne $request.control.key) { continue }
    if (!$node.Current.IsEnabled -or $node.Current.IsOffscreen -or $node.Current.IsPassword) {
        throw 'The control is no longer available.'
    }
    if (![ClydexNativeControl]::MatchesWindow([IntPtr]::new([long]$request.hwnd),
                                             [uint32]$request.pid, $request.title)) {
        throw 'The reviewed window changed.'
    }
    if ($request.mode -eq 'append' -and $editable) {
        if ($nativeEdit) {
            [ClydexNativeControl]::Append([IntPtr]::new([long]$request.hwnd),
                                    [IntPtr]::new($item.NativeWindowHandle), [string]$request.text)
        } else {
            $value = $node.GetCurrentPattern([Windows.Automation.ValuePattern]::Pattern)
            if ($value.Current.IsReadOnly) { throw 'The field is read-only.' }
            $expected = $value.Current.Value + [string]$request.text
            $value.SetValue($expected)
            if ($value.Current.Value -cne $expected) { throw 'The app did not confirm the complete text.' }
        }
    } elseif ($request.mode -eq 'press' -and $action -and $action -eq $request.control.action) {
        switch ($action) {
            'NativeButton' {
                [ClydexNativeControl]::Click([IntPtr]::new([long]$request.hwnd), [IntPtr]::new($item.NativeWindowHandle))
            }
            'Invoke' { $node.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke() }
            'Toggle' { $node.GetCurrentPattern([Windows.Automation.TogglePattern]::Pattern).Toggle() }
            'SelectionItem' { $node.GetCurrentPattern([Windows.Automation.SelectionItemPattern]::Pattern).Select() }
            'ExpandCollapse' {
                $menu = $node.GetCurrentPattern([Windows.Automation.ExpandCollapsePattern]::Pattern)
                if ($menu.Current.ExpandCollapseState -eq 'Expanded') { $menu.Collapse() } else { $menu.Expand() }
            }
        }
    } else { throw 'The requested operation is no longer available.' }
    [Console]::Write('true')
    exit 0
}
if ($request.mode -ne 'inspect') { throw 'The selected control changed. Ask again to select it.' }
[Console]::Write((ConvertTo-Json -InputObject $choices.ToArray() -Compress))
