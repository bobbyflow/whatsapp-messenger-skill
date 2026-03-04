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
import ctypes

user32 = ctypes.windll.user32

# WhatsApp Microsoft Store App Protocol
WHATSAPP_LAUNCH_CMD = r"explorer.exe shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"

def block_input(block=True):
    """Freezes hardware input (Keyboard/Mouse). Requires Admin."""
    try:
        user32.BlockInput(block)
    except:
        pass

def set_topmost(hwnd, is_topmost=True):
    """Forces window to absolute Z-order priority (Always on Top)."""
    if not hwnd or not win32gui.IsWindow(hwnd): return
    z_order = win32con.HWND_TOPMOST if is_topmost else win32con.HWND_NOTOPMOST
    win32gui.SetWindowPos(hwnd, z_order, 0, 0, 0, 0, 
                         win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW)

def ensure_whatsapp_open():
    hwnd = win32gui.FindWindow("ApplicationFrameWindow", "WhatsApp")
    if not hwnd:
        hwnd = win32gui.FindWindow(None, "WhatsApp")
    
    if hwnd and win32gui.IsWindowVisible(hwnd):
        return hwnd
    
    print("WhatsApp is hidden or closed. Attempting to launch/wake...")
    subprocess.Popen(WHATSAPP_LAUNCH_CMD, shell=True)
    
    for i in range(25):
        time.sleep(1)
        hwnd = win32gui.FindWindow("ApplicationFrameWindow", "WhatsApp")
        if not hwnd:
            hwnd = win32gui.FindWindow(None, "WhatsApp")
        if hwnd and win32gui.IsWindowVisible(hwnd):
            print("WhatsApp window is now visible.")
            time.sleep(3) # Extra time for UWP rendering
            return hwnd
    return None

def is_whatsapp_window(hwnd):
    try:
        class_name = win32gui.GetClassName(hwnd)
        title = win32gui.GetWindowText(hwnd)
        return "WhatsApp" in title or class_name == "ApplicationFrameWindow"
    except:
        return False

def get_whatsapp_search_box(wa_win):
    """Specifically targets the WhatsApp Search box."""
    search = wa_win.EditControl(Name="Search input textbox")
    if search.Exists(0):
        return search
    return None

def get_whatsapp_msg_box(wa_win, contact):
    """Specifically targets the WhatsApp Message box which is dynamic."""
    for ctrl, _ in auto.WalkControl(wa_win, maxDepth=30):
        if ctrl.ControlTypeName == "EditControl" and "Type to" in ctrl.Name:
            return ctrl
    
    # Fallback heuristic: bottom-most EditControl
    edits = []
    win_rect = wa_win.BoundingRectangle
    for ctrl, _ in auto.WalkControl(wa_win, maxDepth=30):
        if ctrl.ControlTypeName == "EditControl" and "Search" not in ctrl.Name:
            rect = ctrl.BoundingRectangle
            if rect.top > (win_rect.top + (win_rect.bottom - win_rect.top) * 0.5):
                edits.append((ctrl, rect.bottom))
    
    if edits:
        edits.sort(key=lambda x: x[1], reverse=True)
        return edits[0][0]
    return None

def atomic_paste(with_enter=False):
    win32api.keybd_event(0x11, 0, 0, 0) # Ctrl
    win32api.keybd_event(0x56, 0, 0, 0) # V
    time.sleep(0.05)
    win32api.keybd_event(0x56, 0, win32con.KEYEVENTF_KEYUP, 0)
    win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
    if with_enter:
        time.sleep(0.1)
        win32api.keybd_event(0x0D, 0, 0, 0) # Enter
        win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)

def force_focus(hwnd, fast=False):
    """Hostile Focus: Uses Thread Attachment and Alt-key bypass to force window to front."""
    if not hwnd or not win32gui.IsWindow(hwnd):
        return False
        
    try:
        if not fast: win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        
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
            
        iterations = 3 if fast else 15
        for _ in range(iterations):
            if win32gui.GetForegroundWindow() == hwnd:
                if not fast: time.sleep(0.3)
                return True
            time.sleep(0.1 if fast else 0.2)
            win32gui.SetForegroundWindow(hwnd)
            
    except Exception as e:
        print(f"Force Focus Error: {e}")
    return False

def send_whatsapp_message(contact, message=None, image_path=None, auto_send=False):
    hwnd = ensure_whatsapp_open()
    if not hwnd: return False

    print("--- INITIATING AGGRESSIVE WHATSAPP BRIDGE ---")
    block_input(True)
    set_topmost(hwnd, True)
    
    try:
        if not force_focus(hwnd):
            print("ABORT: Could not seize focus from previous application.")
            return False
            
        time.sleep(1.0)
        wa_win = auto.ControlFromHandle(hwnd)
        
        # --- TARGETED ATOMIC SEARCH ---
        print(f"Searching for WhatsApp contact: {contact}")
        search_box = get_whatsapp_search_box(wa_win)
        if not search_box:
            # Try Ctrl+F fallback
            win32api.keybd_event(0x11, 0, 0, 0)
            win32api.keybd_event(0x46, 0, 0, 0)
            time.sleep(0.1)
            win32api.keybd_event(0x46, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.5)
            search_box = get_whatsapp_search_box(wa_win)

        if search_box:
            search_box.Click(simulateMove=False)
            time.sleep(0.2)
            # Atomic Clear
            win32api.keybd_event(0x11, 0, 0, 0)
            win32api.keybd_event(0x41, 0, 0, 0)
            win32api.keybd_event(0x41, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(0x08, 0, 0, 0)
            win32api.keybd_event(0x08, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            pyperclip.copy(contact)
            atomic_paste(with_enter=True)
            time.sleep(2.0) # Wait for chat switch
        
        # Re-sync window after switch
        active_hwnd = win32gui.GetForegroundWindow()
        target_hwnd = active_hwnd if is_whatsapp_window(active_hwnd) else hwnd
        target_win = auto.ControlFromHandle(target_hwnd)
        set_topmost(target_hwnd, True)
        force_focus(target_hwnd, fast=True)
        
        # --- DELIVERY ---
        msg_box = get_whatsapp_msg_box(target_win, contact)
        if msg_box:
            msg_box.SetFocus()
            time.sleep(0.3)
            
            if image_path and os.path.exists(image_path):
                print(f"Pasting image: {image_path}")
                p_path = image_path.replace("'", "''")
                subprocess.run(["powershell.exe", "-NoProfile", "-Command", f"Set-Clipboard -Path '{p_path}'"])
                time.sleep(1.0)
                force_focus(target_hwnd, fast=True)
                atomic_paste(with_enter=False)
                time.sleep(2.0)

            if message:
                print("Pasting message...")
                pyperclip.copy(message)
                msg_box.SetFocus()
                force_focus(target_hwnd, fast=True)
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
    finally:
        set_topmost(hwnd, False)
        block_input(False)
        print("--- AGGRESSIVE WHATSAPP BRIDGE COMPLETE ---")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("contact")
    parser.add_argument("--message", default=None)
    parser.add_argument("--image", default=None)
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()
    send_whatsapp_message(args.contact, args.message, args.image, auto_send=args.send)
