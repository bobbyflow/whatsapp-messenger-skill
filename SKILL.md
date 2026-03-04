---
name: whatsapp-messenger
description: Send results and images to your local WhatsApp Desktop account via a surgical Python bridge. Use when you need to output data to WhatsApp contacts or groups without UI interference.
---

# WhatsApp Messenger

This skill allows AI agents to send text output and images directly to your local WhatsApp Desktop client using a hardware-resilient Python bridge.

## 🌟 Key Features
- **⚡ Atomic Delivery**: Uses high-speed clipboard injection to bypass physical keyboard interference.
- **🛠️ Self-Healing**: Automatically launches WhatsApp if it's closed or hidden in the system tray.
- **🛡️ Absolute Zero Aggression**: Forces WhatsApp to front and locks hardware input (Requires Admin).
- **🔄 Follow-the-Focus**: Automatically detects and re-binds if a chat is in a standalone window.
- **🧠 Universal Intelligence**: Dynamic 4-way research synthesis for professional replies (v3.0).

## Tools

### send_to_whatsapp
Sends a message or image to a specific WhatsApp contact.

- **Arguments**:
  - `contact`: The name of the contact or group (e.g., "Bobby").
  - `message` (optional): The text to send.
  - `image` (optional): The absolute local path to an image file.
  - `send` (optional): Set to true to actually transmit (default: false / Halt mode).

- **Command**:
  `python "%USERPROFILE%\.gemini\skills\whatsapp-messenger\scripts\whatsapp_bridge.py" "<contact>" [--message "<message>"] [--image "<path>"] [--send]`

### help_me_reply
Performs deep context extraction and intelligence synthesis to draft a reply.
- **Arguments**:
  - `chat_name`: The name of the group or contact.
  - `intensity`: `quick` (1 search), `standard` (2 searches), `deep` (4 searches + research skill).
- **Workflow**: 
  1. Scrapes last 30 messages using UWP UI traversal.
  2. Fuses parallel research with internal reasoning.
  3. Pastes draft into chat (Halt Mode).

## Workflow
1.  Identify the target contact and content.
2.  Use the `send_to_whatsapp` command to deliver.
3.  **Default (HALT Mode):** The script MUST stay in Halt Mode (pastes but doesn't send).
4.  **Bypass Rule:** The AI Agent is STRICTLY FORBIDDEN from using the `--send` flag unless the user explicitly includes the phrase **"BYPASS HALT"** in their request.

## Constraints
- **WhatsApp Desktop Required**: The Windows Desktop application must be installed.
- **Phone Connection**: Your phone must be connected to ensure the desktop client is in an active state.

---
Bobby Choi (Sovereign) | Opal (Architect)
