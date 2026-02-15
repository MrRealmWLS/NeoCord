# NeoCord

**NeoCord** is a Python-based Discord client built with **CustomTkinter** that connects to the **real Discord API**. It is designed for **educational purposes, proof-of-concept demonstrations, and learning how Discord clients work**.

> ⚠️ **Disclaimer:** NeoCord is intended for **educational purposes only**. Using it with real Discord accounts may violate Discord's Terms of Service. Use it **at your own risk**.

---

## Features

* **Token Management**

  * Enter your Discord token at startup if not already set.
  * Change your token anytime via the **“Set Token”** button.
  * Tokens are saved locally in `token.db` for convenience.

* **Server & Channel Browsing**

  * Display all servers the account is part of.
  * Expand/collapse server channels, including categories.
  * Click on channels to view messages.

* **Message Viewing**

  * Scrollable interface for channel messages.
  * Displays author name, avatar, and message content.
  * Messages are sorted by timestamp.

* **User Info Panel**

  * Displays username and profile picture.
  * Quick access to set or update token.

* **Custom Tkinter UI**

  * Dark mode by default.
  * Responsive layout with scrollable frames and styled buttons.
  * Clean, Discord-like interface for educational exploration.

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/neocord.git
cd neocord
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

**Dependencies include:**

* `customtkinter`
* `Pillow`
* `requests`

3. Run NeoCord:

```bash
python app.py
```

---

## Usage

1. **Set Your Token**

   * Enter your Discord token when prompted.
   * Tokens are stored locally in `token.db`.

2. **Explore Servers & Channels**

   * Click a server to expand its channels.
   * Click a channel to load messages in the main frame.

3. **View Messages**

   * See author, avatar, and message content in a scrollable frame.
   * Messages are sorted by timestamp for readability.

4. **Update Token**

   * Use the **“Set Token”** button to change tokens.
   * A message will appear: **“Restart to make it take effect”**.

---

## Project Structure

```
NeoCord/
│
├── assets/             # Icons and default images (nopfp.png, settings.png)
├── client.py           # Discord API client logic
├── main.py             # Main application UI and logic
├── token.db            # Saved user token (auto-created)
├── README.md           # This file
└── requirements.txt    # Python dependencies
```

---

## Disclaimer

NeoCord **connects to the real Discord API**. It is **strictly for educational purposes** and proof-of-concept testing. Misuse can result in account termination or violation of Discord Terms of Service. **Use at your own risk.**

---

## License

MIT License © 2026 RealmWLS