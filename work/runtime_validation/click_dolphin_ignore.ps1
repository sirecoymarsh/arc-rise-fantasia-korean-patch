param([int]$ProcessId)

Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;

public static class DolphinDialogClick {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
    [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr parent, EnumWindowsProc callback, IntPtr lParam);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] static extern IntPtr SendMessage(IntPtr hWnd, uint message, IntPtr wParam, IntPtr lParam);
    const uint BM_CLICK = 0x00F5;

    static string Text(IntPtr hWnd) {
        var b = new StringBuilder(1024);
        GetWindowText(hWnd, b, b.Capacity);
        return b.ToString();
    }

    public static string Click(uint targetPid) {
        IntPtr found = IntPtr.Zero;
        string foundText = "";
        EnumWindows((top, lp) => {
            uint pid;
            GetWindowThreadProcessId(top, out pid);
            if (pid != targetPid) return true;
            EnumChildWindows(top, (child, childLp) => {
                string text = Text(child);
                if (text.Contains("이 세션을 무시")) {
                    found = child;
                    foundText = text;
                    return false;
                }
                return true;
            }, IntPtr.Zero);
            return found == IntPtr.Zero;
        }, IntPtr.Zero);
        if (found == IntPtr.Zero) return "NOT_FOUND";
        SendMessage(found, BM_CLICK, IntPtr.Zero, IntPtr.Zero);
        return "CLICKED|0x" + found.ToInt64().ToString("X") + "|" + foundText;
    }
}
"@

[DolphinDialogClick]::Click([uint32]$ProcessId)
