"""Small Windows helper for deterministic Dolphin runtime evidence capture.

The helper only targets an already-running Dolphin process.  It can enumerate
windows, activate a chosen window, inject the configured keyboard/mouse input,
and capture that exact HWND with Pillow's Windows Graphics Capture backend.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import sys
import time

from PIL import ImageGrab


user32 = ctypes.WinDLL("user32", use_last_error=True)

EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.BringWindowToTop.argtypes = [wintypes.HWND]
user32.BringWindowToTop.restype = wintypes.BOOL
user32.GetForegroundWindow.restype = wintypes.HWND
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
user32.AttachThreadInput.restype = wintypes.BOOL
user32.SetFocus.argtypes = [wintypes.HWND]
user32.SetFocus.restype = wintypes.HWND
user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL
user32.SwitchToThisWindow.argtypes = [wintypes.HWND, wintypes.BOOL]
user32.SwitchToThisWindow.restype = None
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetClientRect.restype = wintypes.BOOL
user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
user32.ClientToScreen.restype = wintypes.BOOL
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.SetCursorPos.restype = wintypes.BOOL
user32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
user32.keybd_event.argtypes = [wintypes.BYTE, wintypes.BYTE, wintypes.DWORD, ctypes.c_void_p]
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.GetCurrentThreadId.restype = wintypes.DWORD

SW_RESTORE = 9
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
HWND_TOPMOST = wintypes.HWND(-1)
HWND_NOTOPMOST = wintypes.HWND(-2)
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_SHOWWINDOW = 0x0040

VK = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "alt": 0x12,
    "escape": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "pagedown": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "insert": 0x2D,
    "delete": 0x2E,
}
for code in range(ord("0"), ord("9") + 1):
    VK[chr(code).lower()] = code
for code in range(ord("A"), ord("Z") + 1):
    VK[chr(code).lower()] = code
for number in range(1, 13):
    VK[f"f{number}"] = 0x6F + number


def title_for(hwnd: int) -> str:
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value


def enumerate_windows(pid: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    callback_errors: list[str] = []

    @EnumWindowsProc
    def callback(hwnd: int, _lparam: int) -> bool:
        try:
            target_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(target_pid))
            if target_pid.value == pid:
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                rows.append(
                    {
                        "hwnd": int(hwnd),
                        "hwnd_hex": f"0x{int(hwnd):X}",
                        "title": title_for(hwnd),
                        "visible": bool(user32.IsWindowVisible(hwnd)),
                        "rect": [rect.left, rect.top, rect.right, rect.bottom],
                    }
                )
        except Exception as exc:  # ctypes suppresses callback exceptions.
            callback_errors.append(repr(exc))
        return 1

    success = user32.EnumWindows(callback, 0)
    if callback_errors:
        raise RuntimeError(f"EnumWindows callback failures: {callback_errors[:5]}")
    if not success:
        raise ctypes.WinError(ctypes.get_last_error())
    return rows


def choose_window(pid: int, title_contains: str | None) -> int:
    windows = enumerate_windows(pid)
    candidates = [row for row in windows if row["visible"]]
    if title_contains:
        candidates = [row for row in candidates if title_contains.casefold() in str(row["title"]).casefold()]
    if len(candidates) != 1:
        raise RuntimeError(f"expected exactly one window, got {len(candidates)}: {windows}")
    return int(candidates[0]["hwnd"])


def activate(hwnd: int) -> None:
    foreground = user32.GetForegroundWindow()
    foreground_pid = wintypes.DWORD()
    target_pid = wintypes.DWORD()
    foreground_thread = user32.GetWindowThreadProcessId(foreground, ctypes.byref(foreground_pid))
    target_thread = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(target_pid))
    current_thread = kernel32.GetCurrentThreadId()
    attached: list[tuple[int, int]] = []
    for left, right in ((current_thread, foreground_thread), (current_thread, target_thread)):
        if left and right and left != right and user32.AttachThreadInput(left, right, True):
            attached.append((left, right))
    user32.ShowWindow(hwnd, SW_RESTORE)
    flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)
    user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, flags)
    # A synthetic Alt press unlocks the foreground transition under Windows'
    # normal focus-stealing protection for this local validation helper.
    user32.keybd_event(VK["alt"], 0, 0, None)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.SwitchToThisWindow(hwnd, True)
    user32.SetFocus(hwnd)
    user32.keybd_event(VK["alt"], 0, KEYEVENTF_KEYUP, None)
    for left, right in reversed(attached):
        user32.AttachThreadInput(left, right, False)
    time.sleep(0.3)
    if int(user32.GetForegroundWindow()) != hwnd:
        raise RuntimeError(
            f"could not focus hwnd 0x{hwnd:X}; foreground is 0x{int(user32.GetForegroundWindow()):X}"
        )


def press(hwnd: int, key: str, hold_ms: int = 80) -> None:
    key = key.casefold()
    if key not in VK:
        raise ValueError(f"unsupported key: {key}")
    activate(hwnd)
    code = VK[key]
    # Arrow/navigation keys are extended keys on Windows.  DirectInput (used
    # by Dolphin's emulated controller backend) ignores a synthetic arrow if
    # this flag is omitted even though regular GUI applications may accept it.
    extended = KEYEVENTF_EXTENDEDKEY if key in {
        "insert", "delete", "home", "end", "pageup", "pagedown",
        "left", "right", "up", "down",
    } else 0
    user32.keybd_event(code, 0, extended, None)
    time.sleep(max(hold_ms, 1) / 1000)
    user32.keybd_event(code, 0, extended | KEYEVENTF_KEYUP, None)


def click(
    hwnd: int,
    button: str = "left",
    hold_ms: int = 80,
    client_x: int | None = None,
    client_y: int | None = None,
) -> None:
    activate(hwnd)
    rect = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError(ctypes.get_last_error())
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    x = width // 2 if client_x is None else max(0, min(client_x, width - 1))
    y = height // 2 if client_y is None else max(0, min(client_y, height - 1))
    point = wintypes.POINT(x, y)
    if not user32.ClientToScreen(hwnd, ctypes.byref(point)):
        raise ctypes.WinError(ctypes.get_last_error())
    user32.SetCursorPos(point.x, point.y)
    if button == "left":
        down, up = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
    elif button == "right":
        down, up = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
    else:
        raise ValueError(button)
    user32.mouse_event(down, 0, 0, 0, None)
    time.sleep(max(hold_ms, 1) / 1000)
    user32.mouse_event(up, 0, 0, 0, None)


def capture(hwnd: int, output: Path) -> dict[str, object]:
    # Dolphin's Direct3D swap chain is not returned by PrintWindow on this
    # build, so capture the on-screen client rectangle after raising it.
    activate(hwnd)
    time.sleep(0.2)
    rect = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError(ctypes.get_last_error())
    upper_left = wintypes.POINT(rect.left, rect.top)
    lower_right = wintypes.POINT(rect.right, rect.bottom)
    if not user32.ClientToScreen(hwnd, ctypes.byref(upper_left)):
        raise ctypes.WinError(ctypes.get_last_error())
    if not user32.ClientToScreen(hwnd, ctypes.byref(lower_right)):
        raise ctypes.WinError(ctypes.get_last_error())
    image = ImageGrab.grab(
        bbox=(upper_left.x, upper_left.y, lower_right.x, lower_right.y),
        all_screens=True,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)
    return {"path": str(output.resolve()), "width": image.width, "height": image.height}


def main() -> None:
    # Dolphin's Japanese window title cannot be represented by every Windows
    # console code page.  Keep the helper's JSON output deterministic instead
    # of failing after the requested input/capture has already completed.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--title-contains")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    sub.add_parser("focus")
    key_parser = sub.add_parser("key")
    key_parser.add_argument("key")
    key_parser.add_argument("--hold-ms", type=int, default=80)
    click_parser = sub.add_parser("click")
    click_parser.add_argument("--button", choices=["left", "right"], default="left")
    click_parser.add_argument("--hold-ms", type=int, default=80)
    click_parser.add_argument("--x", type=int, help="client-relative X coordinate")
    click_parser.add_argument("--y", type=int, help="client-relative Y coordinate")
    shot_parser = sub.add_parser("screenshot")
    shot_parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if args.command == "list":
        print(json.dumps(enumerate_windows(args.pid), ensure_ascii=False, indent=2))
        return
    hwnd = choose_window(args.pid, args.title_contains)
    if args.command == "focus":
        activate(hwnd)
        result = {"hwnd": hwnd, "title": title_for(hwnd)}
    elif args.command == "key":
        press(hwnd, args.key, args.hold_ms)
        result = {"hwnd": hwnd, "key": args.key}
    elif args.command == "click":
        click(hwnd, args.button, args.hold_ms, args.x, args.y)
        result = {
            "hwnd": hwnd,
            "button": args.button,
            "hold_ms": args.hold_ms,
            "client_x": args.x,
            "client_y": args.y,
        }
    elif args.command == "screenshot":
        result = {"hwnd": hwnd, "title": title_for(hwnd), **capture(hwnd, args.output)}
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
