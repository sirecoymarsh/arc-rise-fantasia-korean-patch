param([Parameter(Mandatory=$true)][int]$ProcessId)

Add-Type @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class DolphinWindowList {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);

    [StructLayout(LayoutKind.Sequential)]
    struct RECT { public int Left, Top, Right, Bottom; }

    static string Text(IntPtr hWnd) {
        var b = new StringBuilder(2048);
        GetWindowText(hWnd, b, b.Capacity);
        return b.ToString();
    }

    public static string[] List(uint targetPid) {
        var rows = new List<string>();
        EnumWindows((hWnd, lParam) => {
            uint pid;
            GetWindowThreadProcessId(hWnd, out pid);
            if (pid == targetPid) {
                RECT r;
                GetWindowRect(hWnd, out r);
                rows.Add(String.Format("0x{0:X}|visible={1}|rect={2},{3},{4},{5}|{6}",
                    hWnd.ToInt64(), IsWindowVisible(hWnd), r.Left, r.Top, r.Right, r.Bottom, Text(hWnd)));
            }
            return true;
        }, IntPtr.Zero);
        return rows.ToArray();
    }
}
"@

[DolphinWindowList]::List([uint32]$ProcessId)
