from math import e
from client import DiscordClient
import customtkinter
from PIL import Image, ImageTk, ImageOps, ImageDraw
import datetime
import requests
from io import BytesIO
import json


customtkinter.set_appearance_mode("Dark")

def load_token():
    try:
        with open("token.db", "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

def save_token(token):
    with open("token.db", "w") as file:
        file.write(token)

def main():
    def open_token_popup():
        popup = customtkinter.CTkToplevel()
        popup.title("Set Token")
        popup.geometry("300x150")

        label = customtkinter.CTkLabel(popup, text="Enter your token:")
        label.pack(pady=10)

        token_entry = customtkinter.CTkEntry(popup, width=250)
        token_entry.pack(pady=5)

        def submit():
            token = token_entry.get()
            save_token(token)
            restart_label = customtkinter.CTkLabel(popup, text="Token saved! Please restart app.py", text_color="yellow")
            restart_label.pack(pady=5)
            enter_button.configure(state="disabled")

        enter_button = customtkinter.CTkButton(popup, text="Enter", command=submit)
        enter_button.pack(pady=10)

    customtkinter.set_default_color_theme("dark-blue")
    root = customtkinter.CTk()
    root.title("NeoCord")
    root.geometry("900x600")
    
    token = load_token()
    if token is None:
        print("No token found. Please set your token using the Set Token button.")
        token = "" 
        open_token_popup()
    
    client = DiscordClient()
    client.token_login(token)
    client.print_traffic = True
    client.connect_websocket()
    client.start_rpc()

    MainFrame = customtkinter.CTkFrame(root, width=600, height=500, corner_radius=10)
    MainFrame.pack(side="left", padx=10, pady=10, fill=customtkinter.BOTH, expand=True)

    UserInfoFrame = customtkinter.CTkFrame(MainFrame, width=400, height=50, corner_radius=10)
    UserInfoFrame.pack(side='top', anchor="w", padx=10, pady=10)

    serverlist = customtkinter.CTkFrame(root, width=200, corner_radius=10)
    serverlist.pack(side="left", fill=customtkinter.Y, padx=10, pady=10)

    message_frame = None
    created_message_frame = False
    server_channels_frames = {}
    expanded_states = {}

    def show_message_channel(channel_id, parent_frame, client_obj):
        nonlocal created_message_frame, message_frame
        channel_messages = client_obj.retrieve_channel_messages(channel_id)
        if channel_messages:
            try:
                channel_messages_sorted = sorted(
                    channel_messages,
                    key=lambda msg: datetime.datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00"))
                )
            except:
                channel_messages_sorted = channel_messages
            if created_message_frame:
                for widget in message_frame.winfo_children():
                    widget.destroy()
            else:
                message_frame = customtkinter.CTkScrollableFrame(parent_frame, width=700, height=500, corner_radius=10)
                message_frame.pack(padx=10, pady=20, fill="both", expand=True)
                created_message_frame = True
            for msg in channel_messages_sorted:
                content = msg["content"]
                username = msg["author"]["global_name"]
                userid = msg["author"]["id"]
                pfp_image = Image.open("assets/nopfp.png")
                pfp_image_ctk = customtkinter.CTkImage(light_image=pfp_image, size=(40, 40))
                msg_container = customtkinter.CTkFrame(message_frame)
                msg_container.pack(fill="x", pady=5)
                top_container = customtkinter.CTkFrame(msg_container)
                top_container.pack(fill="x")
                profile_pic_label = customtkinter.CTkLabel(top_container, image=pfp_image_ctk, text="")
                profile_pic_label.image = pfp_image_ctk
                profile_pic_label.pack(side="left", padx=5)
                username_label = customtkinter.CTkLabel(
                    top_container, text=username, font=("Arial", 14, "bold"), anchor="w", text_color="#ffffff"
                )
                username_label.pack(side="left", padx=5)
                content_label = customtkinter.CTkLabel(
                    msg_container, text=content, font=("Arial", 12), anchor="w", text_color="#ffffff", wraplength=500
                )
                content_label.pack(fill="x", padx=10)

    def create_channels_frame(guild_id, parent):
        frame = customtkinter.CTkScrollableFrame(parent)
        channels = client.retrieve_server_channels(guild_id)
        if channels:
            non_category_channels = [ch for ch in channels if ch.get("type") != 4]
            uncategorized_channels = sorted(
                [ch for ch in non_category_channels if not ch.get("parent_id")],
                key=lambda ch: ch.get("position", 0)
            )
            for ch in uncategorized_channels:
                channel_btn = customtkinter.CTkButton(
                    frame,
                    text=ch["name"],
                    command=lambda cid=ch["id"]: show_message_channel(cid, MainFrame, client),
                    fg_color="#36393f",
                    hover_color="#40444b",
                    text_color="#ffffff"
                )
                channel_btn.pack(side="top", padx=20, pady=2, fill="x")

            category_channels = sorted([ch for ch in channels if ch.get("type") == 4], key=lambda ch: ch.get("position", 0))
            for cat in category_channels:
                cat_label = customtkinter.CTkLabel(frame, text=cat["name"], font=("Arial", 12, "bold"), text_color="#ffffff")
                cat_label.pack(pady=(10, 5))
                channels_in_cat = sorted(
                    [c for c in non_category_channels if c.get("parent_id") == cat["id"]],
                    key=lambda c: c.get("position", 0)
                )
                for c in channels_in_cat:
                    channel_btn = customtkinter.CTkButton(
                        frame,
                        text=c["name"],
                        command=lambda cid=c["id"]: show_message_channel(cid, MainFrame, client),
                        fg_color="#36393f",
                        hover_color="#40444b",
                        text_color="#ffffff"
                    )
                    channel_btn.pack(side="top", padx=40, pady=2, fill="x")
        return frame

    def toggle_channels(guild_id):
        if expanded_states.get(guild_id, False):
            server_channels_frames[guild_id].pack_forget()
            expanded_states[guild_id] = False
        else:
            server_channels_frames[guild_id].pack(side="top", fill="x", padx=10)
            expanded_states[guild_id] = True

    if client.get_me():
        username = client.me["global_name"]
        user_id = client.me["id"]
        pfp_url = client.get_me_pfp()
        if pfp_url:
            try:
                response = requests.get(pfp_url)
                if response.status_code == 200:
                    pfp_data = response.content
                    pfp_image = Image.open(BytesIO(pfp_data))
                    pfp_image = pfp_image.resize((32, 32))
                    mask = Image.new("L", (32, 32), 0)
                    ImageDraw.Draw(mask).ellipse((0, 0, 32, 32), fill=255)
                    pfp_image = ImageOps.fit(pfp_image, (32, 32), centering=(0.5, 0.5))
                    pfp_image.putalpha(mask)
                    pfp_tk = ImageTk.PhotoImage(pfp_image)
                    UsernameLabel = customtkinter.CTkLabel(
                        UserInfoFrame, text=username, image=pfp_tk, compound="left", font=("Arial", 14, "bold"),
                        padx=15, text_color="white"
                    )
                    UsernameLabel.image = pfp_tk
                    UsernameLabel.pack(side="left", padx=10, pady=5)
                else:
                    UsernameLabel = customtkinter.CTkLabel(UserInfoFrame, text=username)
                    UsernameLabel.pack(side="left", padx=20)
            except:
                UsernameLabel = customtkinter.CTkLabel(UserInfoFrame, text=username)
                UsernameLabel.pack(side="left", padx=20)
        else:
            UsernameLabel = customtkinter.CTkLabel(UserInfoFrame, text=username)
            UsernameLabel.pack(side="left", padx=20)

    settings_icon = Image.open("assets/settings.png")
    settings_icon_ctk = customtkinter.CTkImage(light_image=settings_icon, size=(20, 20))
    set_Token = customtkinter.CTkButton(
        UserInfoFrame,
        text="Set Token",
        image=settings_icon_ctk,
        compound="left",
        anchor="w",
        fg_color="#2a3439",
        hover_color="#0a0a0a",
        text_color="#ffffff",
        command=open_token_popup
    )
    set_Token.pack(pady=4, padx=4)

    guilds = client.retrieve_servers()
    for guild in guilds:
        server_container = customtkinter.CTkFrame(serverlist)
        server_container.pack(fill="x", pady=5)
        icon_url = client.get_server_icon(guild["id"], guilds)
        if icon_url:
            try:
                response = requests.get(icon_url)
                if response.status_code == 200:
                    icon_data = response.content
                    icon_image = Image.open(BytesIO(icon_data))
                    icon_image = icon_image.resize((30, 30))
                    icon_tk = ImageTk.PhotoImage(icon_image)
                else:
                    icon_tk = None
            except:
                icon_tk = None
        else:
            icon_tk = None
        if icon_tk:
            server_button = customtkinter.CTkButton(
                server_container,
                text=guild["name"],
                image=icon_tk,
                compound="left",
                anchor="w",
                fg_color="#2a3439",
                hover_color="#0a0a0a",
                text_color="#ffffff",
                command=lambda gid=guild["id"]: toggle_channels(gid)
            )
            server_button.image = icon_tk
        else:
            server_button = customtkinter.CTkButton(
                server_container,
                text=guild["name"],
                anchor="w",
                fg_color="#2a3439",
                hover_color="#0a0a0a",
                text_color="#ffffff",
                command=lambda gid=guild["id"]: toggle_channels(gid)
            )
        server_button.pack(side="top", fill="x")

        subframe = create_channels_frame(guild["id"], server_container)
        server_channels_frames[guild["id"]] = subframe
        expanded_states[guild["id"]] = False

    root.mainloop()

if __name__ == "__main__":
    main()
