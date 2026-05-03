# 🏥 MedAI Pro - Stable Setup Instructions

This application is designed to behave like professional, installed software. Follow these steps to set up your permanent desktop access.

## 🚀 One-Time Setup

1.  **Install Dependencies**:
    Open a terminal in this folder and run:
    ```bash
    pip install flask pandas scikit-learn openpyxl qrcode winshell pywin32
    ```

2.  **Create Desktop Shortcut**:
    Run the following command to create a "MedAI Pro" icon on your desktop:
    ```bash
    python create_shortcut.py
    ```

## 🛠️ Daily Usage

- **Start the App**: Just double-click the **MedAI Pro** icon on your desktop.
- **Background Running**: The server starts automatically in the background. You won't see a terminal window.
- **Auto-Restart**: If the backend ever stops, the built-in watchdog will restart it automatically within 10 seconds.
- **PWA Installation**: Once the app opens in your browser, click the **"Install App"** button in the sidebar to add it to your Taskbar or Home Screen.

## 📱 Mobile Access

- The login page displays a **QR Code**. Scan it with your phone to access the dashboard on your local network.
- Add to Home Screen on your phone for a full-screen app experience.

## ⚡ Performance Features

- **Model Caching**: The ML model is trained once per dataset and cached in memory.
- **Efficient Processing**: Optimized for datasets up to 10MB.
- **Offline Support**: If the server goes down, you'll see a friendly offline page instead of a browser error.

---
*MedAI Pro - Empowering Healthcare with AI Stability.*
