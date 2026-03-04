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
from PIL import ImageGrab

user32 = ctypes.windll.user32

WHATSAPP_LAUNCH_CMD = r"explorer.exe shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"

def force_focus(hwnd):
    """Hostile Focus: Uses Thread Attachment and Alt-key bypass."""
    if not hwnd or not win32gui.IsWindow(hwnd):
        return False
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

def ensure_whatsapp_open():
    hwnd = win32gui.FindWindow("ApplicationFrameWindow", "WhatsApp")
    if not hwnd: hwnd = win32gui.FindWindow(None, "WhatsApp")
    if hwnd and win32gui.IsWindowVisible(hwnd): return hwnd
    subprocess.Popen(WHATSAPP_LAUNCH_CMD, shell=True)
    for _ in range(20):
        time.sleep(1)
        hwnd = win32gui.FindWindow("ApplicationFrameWindow", "WhatsApp")
        if not hwnd: hwnd = win32gui.FindWindow(None, "WhatsApp")
        if hwnd and win32gui.IsWindowVisible(hwnd):
            time.sleep(2)
            return hwnd
    return None

def is_whatsapp_window(hwnd):
    try:
        class_name = win32gui.GetClassName(hwnd)
        title = win32gui.GetWindowText(hwnd)
        return "WhatsApp" in title or class_name == "ApplicationFrameWindow"
    except:
        return False

def is_timestamp(text):
    # WhatsApp timestamp heuristic
    patterns = [
        r"^\d{1,2}:\d{2}\s?(AM|PM|am|pm)?$",
        r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)",
        r"^Yesterday",
        r"^\d{1,2}/\d{1,2}/\d{2,4}"
    ]
    for p in patterns:
        if re.search(p, text): return True
    return False

def read_whatsapp_context(target_chat, message_count=30):
    hwnd = ensure_whatsapp_open()
    if not hwnd:
        print("ERROR: WhatsApp not running")
        return
    
    force_focus(hwnd)
    wa_win = auto.ControlFromHandle(hwnd)
    
    # --- TARGETED ATOMIC SEARCH ---
    search_box = wa_win.EditControl(Name="Search input textbox")
    if not search_box.Exists(0):
        win32api.keybd_event(0x11, 0, 0, 0) # Ctrl
        win32api.keybd_event(0x46, 0, 0, 0) # F
        time.sleep(0.1)
        win32api.keybd_event(0x46, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.5)
        search_box = wa_win.EditControl(Name="Search input textbox")

    if search_box.Exists(0):
        search_box.Click(simulateMove=False)
        time.sleep(0.2)
        # Atomic Clear
        win32api.keybd_event(0x11, 0, 0, 0)
        win32api.keybd_event(0x41, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(0x41, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x08, 0, 0, 0)
        win32api.keybd_event(0x08, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        pyperclip.copy(target_chat)
        
        # Paste
        win32api.keybd_event(0x11, 0, 0, 0)
        win32api.keybd_event(0x56, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(0x56, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.1)
        win32api.keybd_event(0x0D, 0, 0, 0) # Enter
        win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        time.sleep(2.0) # Wait for chat switch and UWP rendering
        
        # Re-sync window after switch
        active_hwnd = win32gui.GetForegroundWindow()
        target_hwnd = active_hwnd if is_whatsapp_window(active_hwnd) else hwnd
        target_win = auto.ControlFromHandle(target_hwnd)
        
        print(f"--- TEMPORAL CONTEXT PACKAGE: {target_chat} ---")
        print(f"SCRAPE_TIME: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")
        
        # In WhatsApp UWP, messages are often in a list called "Message list"
        messages_list = target_win.ListControl(Name="Message list")
        if not messages_list.Exists(0):
            # Fallback: Find the largest list or group
            for ctrl, _ in auto.WalkControl(target_win, maxDepth=10):
                if ctrl.ControlTypeName in ["ListControl", "GroupControl"] and "Message" in ctrl.Name:
                    messages_list = ctrl
                    break
                    
        if messages_list and messages_list.Exists(0):
            # Collect TextControls within the message list
            texts = []
            for ctrl, _ in auto.WalkControl(messages_list, maxDepth=5):
                if ctrl.ControlTypeName == "TextControl" and ctrl.Name:
                    # Filter out reaction buttons or read receipts if possible
                    if len(ctrl.Name.strip()) > 0 and ctrl.Name != "Read":
                        texts.append(ctrl.Name)
            
            slice_msgs = texts[-message_count:]
            
            for i, text in enumerate(slice_msgs):
                if is_timestamp(text):
                    print(f"T_{i} [TIME_ANCHOR]: {text}")
                else:
                    print(f"M_{i}: {text}")
            print("--- END PACKAGE ---")
            return True
        else:
            print("ERROR: Could not identify WhatsApp message list area.")
            return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("chat_name")
    parser.add_argument("--count", type=int, default=30)
    args = parser.parse_args()
    read_whatsapp_context(args.chat_name, args.count)
