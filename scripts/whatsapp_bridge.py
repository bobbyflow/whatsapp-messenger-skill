import win32gui
import win32con
import win32api
import win32process
import time
import sys
import os
import subprocess
import uiautomation as auto
import pyperclip

# WhatsApp Microsoft Store App Protocol
WHATSAPP_LAUNCH_CMD = "explorer.exe shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"

def ensure_whatsapp_open():
    # 1. Look for the window handle (Title: WhatsApp, Class: ApplicationFrameWindow)
    hwnd = win32gui.FindWindow("ApplicationFrameWindow", "WhatsApp")
    if not hwnd:
        hwnd = win32gui.FindWindow(None, "WhatsApp")
    
    if hwnd and win32gui.IsWindowVisible(hwnd):
        return hwnd
    
    print("WhatsApp is hidden or closed. Attempting to launch/wake...")
    subprocess.Popen(WHATSAPP_LAUNCH_CMD, shell=True)
    
    # Wait for window to become visible (UWP apps can be slow to start)
    for i in range(25):
        time.sleep(1)
        hwnd = win32gui.FindWindow("ApplicationFrameWindow", "WhatsApp")
        if not hwnd:
            hwnd = win32gui.FindWindow(None, "WhatsApp")
        if hwnd and win32gui.IsWindowVisible(hwnd):
            print("WhatsApp window is now visible.")
            time.sleep(2) # Extra time for UWP to render content
            return hwnd
            
    print("Error: Could not bring WhatsApp to the foreground.")
    return None

def is_whatsapp_window(hwnd):
    try:
        class_name = win32gui.GetClassName(hwnd)
        title = win32gui.GetWindowText(hwnd)
        return "WhatsApp" in title or class_name == "ApplicationFrameWindow"
    except:
        return False

def get_target_msg_box(win_ctrl):
    """Finds the WhatsApp message box using heuristic verification."""
    max_area = 0
    target = None
    try:
        win_rect = win_ctrl.BoundingRectangle
        win_height = win_rect.bottom - win_rect.top
        # UWP apps often hide text boxes inside nested Panes
        for ctrl, _ in auto.WalkControl(win_ctrl, maxDepth=25):
            # WhatsApp text box is usually an EditControl with specific names or no name
            if ctrl.ControlTypeName == "EditControl":
                rect = ctrl.BoundingRectangle
                # Must be in the lower part of the window
                if rect.top > (win_rect.top + win_height * 0.4):
                    area = (rect.right - rect.left) * (rect.bottom - rect.top)
                    if area > max_area:
                        max_area = area
                        target = ctrl
    except:
        pass
    return target

def verify_chat_header(win_ctrl, contact):
    """Verifies that the WhatsApp chat header matches the intended contact."""
    try:
        win_rect = win_ctrl.BoundingRectangle
        top_boundary = win_rect.top + (win_rect.bottom - win_rect.top) * 0.3
        
        for ctrl, _ in auto.WalkControl(win_ctrl, maxDepth=20):
            # WhatsApp headers are usually TextControls at the top
            if ctrl.ControlTypeName == "TextControl":
                if ctrl.BoundingRectangle.bottom < top_boundary:
                    if contact.lower() in ctrl.Name.lower():
                        print(f"Identity Verified: Found '{ctrl.Name}' in WhatsApp header.")
                        return True
    except:
        pass
    return False

def atomic_paste(with_enter=False):
    """Ultra-fast Ctrl+V."""
    win32api.keybd_event(0x11, 0, 0, 0) # Ctrl
    win32api.keybd_event(0x56, 0, 0, 0) # V
    time.sleep(0.05)
    win32api.keybd_event(0x56, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
    if with_enter:
        time.sleep(0.1)
        win32api.keybd_event(0x0D, 0, 0, 0) # Enter
        win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)

def send_whatsapp_message(contact, message=None, image_path=None, auto_send=False):
    hwnd = ensure_whatsapp_open()
    if not hwnd: return False

    try:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.8)
        
        wa_win = auto.ControlFromHandle(hwnd)
        
        # --- ATOMIC SEARCH ---
        print(f"Searching for WhatsApp contact: {contact}")
        # WhatsApp Search shortcut: Ctrl+F
        win32api.keybd_event(0x11, 0, 0, 0)
        win32api.keybd_event(0x46, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(0x46, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.3)
        
        # Clear search bar (Atomic Ctrl+A + Backspace)
        win32api.keybd_event(0x11, 0, 0, 0)
        win32api.keybd_event(0x41, 0, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(0x41, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(0x08, 0, 0, 0)
        win32api.keybd_event(0x08, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        # Paste contact and ENTER
        pyperclip.copy(contact)
        atomic_paste(with_enter=True)
        time.sleep(1.5) # Wait for results and switch
        
        # Follow focus (if popped out)
        active_hwnd = win32gui.GetForegroundWindow()
        target_hwnd = active_hwnd if is_whatsapp_window(active_hwnd) else hwnd
        target_win = auto.ControlFromHandle(target_hwnd)
        
        if not verify_chat_header(target_win, contact):
            print(f"ABORT: WhatsApp Identity Lock failed for '{contact}'.")
            # We don't return False here yet as UWP headers can be tricky, 
            # let's try finding the msg box anyway.
        
        # --- DELIVERY ---
        msg_box = get_target_msg_box(target_win)
        if msg_box:
            msg_box.SetFocus()
            time.sleep(0.2)
            
            if image_path and os.path.exists(image_path):
                # Paste image
                p_path = image_path.replace("'", "''")
                subprocess.run(["powershell.exe", "-NoProfile", "-Command", f"Set-Clipboard -Path '{p_path}'"])
                time.sleep(1.0)
                atomic_paste(with_enter=False)
                time.sleep(2.0)

            if message:
                print("Pasting message via Atomic Paste...")
                pyperclip.copy(message)
                msg_box.SetFocus()
                atomic_paste(with_enter=False)
            
            if auto_send:
                time.sleep(0.5)
                win32api.keybd_event(0x0D, 0, 0, 0)
                win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
                print(f"Successfully SENT to WhatsApp: {contact}")
            else:
                print(f"DONE: Message pasted for {contact} on WhatsApp. (Halt mode)")
            return True
        else:
            print("Error: Could not identify WhatsApp message input area.")
            return False
            
    except Exception as e:
        print(f"WhatsApp Bridge Error: {e}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("contact")
    parser.add_argument("--message", default=None)
    parser.add_argument("--image", default=None)
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()
    send_whatsapp_message(args.contact, args.message, args.image, auto_send=args.send)
