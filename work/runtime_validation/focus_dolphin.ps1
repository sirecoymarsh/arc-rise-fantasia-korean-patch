param([int]$ProcessId)

Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;

public static class WindowFocus {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] static extern bool BringWindowToTop(IntPtr hWnd);
    [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint flags);

    public static string Activate(uint targetPid) {
        IntPtr found = IntPtr.Zero;
        string title = "";
        EnumWindows((hWnd, lParam) => {
            uint pid;
            GetWindowThreadProcessId(hWnd, out pid);
            if (pid != targetPid || !IsWindowVisible(hWnd)) return true;
            var buffer = new StringBuilder(1024);
            GetWindowText(hWnd, buffer, buffer.Capacity);
            string candidate = buffer.ToString();
            if (candidate.Contains("RPJJ99")) { found = hWnd; title = candidate; return false; }
            return true;
        }, IntPtr.Zero);
        if (found == IntPtr.Zero) return "NOT_FOUND";
        ShowWindow(found, 9);
        SetWindowPos(found, new IntPtr(-1), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010);
        SetWindowPos(found, new IntPtr(-2), 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010);
        BringWindowToTop(found);
        bool ok = SetForegroundWindow(found);
        return ok + "|0x" + found.ToInt64().ToString("X") + "|" + title;
    }
}
"@

[WindowFocus]::Activate([uint32]$ProcessId)
