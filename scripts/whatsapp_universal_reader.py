import win32gui
import win32con
import win32api
import win32process
import time
import sys
import os
import uiautomation as auto
import pyperclip
import ctypes
import re
from datetime import datetime

user32 = ctypes.windll.user32

def force_focus(hwnd):
    if not hwnd or not win32gui.IsWindow(hwnd): return False
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        foreground_thread_id = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[0]
        current_thread_id = win32api.GetCurrentThreadId()
        if foreground_thread_id != current_thread_id:
            win32process.AttachThreadInput(current_thread_id, foreground_thread_id, True)
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32gui.SetForegroundWindow(hwnd)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32process.AttachThreadInput(current_thread_id, foreground_thread_id, False)
        else:
            win32gui.SetForegroundWindow(hwnd)
        for _ in range(10):
            if win32gui.GetForegroundWindow() == hwnd: return True
            time.sleep(0.1)
    except: pass
    return False

def is_timestamp(text):
    patterns = [r"^\d{1,2}:\d{2}\s?(AM|PM|am|pm)?$", r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)", r"^Yesterday"]
    for p in patterns:
        if re.search(p, text): return True
    return False

def read_whatsapp_context(target_chat, message_count=30):
    hwnds = []
    win32gui.EnumWindows(lambda h, _: hwnds.append(h) if "WhatsApp" in win32gui.GetWindowText(h) and win32gui.IsWindowVisible(h) else None, None)
    if not hwnds: return
    
    hwnd = hwnds[0]
    force_focus(hwnd)
    wa_win = auto.ControlFromHandle(hwnd)
    
    # 1. Force Search and Selection
    search_box = wa_win.EditControl(searchDepth=10, Name="Search or start a new chat")
    if not search_box.Exists(0): search_box = wa_win.EditControl(searchDepth=10, Name="Search input textbox")
    
    if search_box.Exists(0):
        search_box.Click(simulateMove=False)
        time.sleep(0.1)
        win32api.keybd_event(0x11, 0, 0, 0) # Ctrl+A
        win32api.keybd_event(0x41, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(0x41, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x08, 0, 0, 0)
        win32api.keybd_event(0x08, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        pyperclip.copy(target_chat)
        win32api.keybd_event(0x11, 0, 0, 0) # Ctrl+V
        win32api.keybd_event(0x56, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(0x56, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.5)
        win32api.keybd_event(0x0D, 0, 0, 0) # Enter
        win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(2.0) # Wait for chat to load

    print(f"--- TEMPORAL CONTEXT PACKAGE (WhatsApp): {target_chat} ---")
    
    # 2. Extract Message Bubbles with Virtualization Resilience
    messages = []
    
    try:
        # We walk the entire window up to a specific depth, catching COM errors caused by UWP virtualization
        for ctrl, depth in auto.WalkControl(wa_win, maxDepth=15):
            try:
                if ctrl.ControlTypeName == "TextControl" and ctrl.Name:
                    txt = ctrl.Name.strip()
                    if len(txt) > 1 and txt not in ["Read", "Delivered", "Sent", "Type a message", "Search or start a new chat", "Chats", "Unread", "All", "Groups"]:
                        # Filter out single emojis if they are just reaction buttons
                        if not re.match(r"^[\u2600-\u27BF]$", txt):
                            messages.append(txt)
            except Exception as e:
                # Catch specific element destruction errors
                continue
    except Exception as e:
        print(f"Tree Walk Interrupted (UWP Virtualization): {e}")

    slice_msgs = messages[-message_count:]
    for i, m in enumerate(slice_msgs):
        if is_timestamp(m):
            print(f"T_{i} [TIME_ANCHOR]: {m}")
        else:
            print(f"M_{i}: {m}")
    print("--- END PACKAGE ---")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("chat_name")
    parser.add_argument("--count", type=int, default=30)
    args = parser.parse_args()
    read_whatsapp_context(args.chat_name, args.count)
