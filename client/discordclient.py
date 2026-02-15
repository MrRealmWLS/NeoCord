import requests
import json
import threading
import select
import multiprocessing
import time
import websocket
from functools import cache
class DiscordClient:
    def __init__(self):
        self.login_url = 'https://discord.com/api/v10/auth/login'
        self.me_url = 'https://discord.com/api/v10/users/@me'
        self.settings_url = 'https://discord.com/api/v10/users/@me/settings'
        self.guilds_url = 'https://discord.com/api/v10/users/@me/guilds'
        self.gateway_url = 'https://discord.com/api/v10/gateway'
        self.logout_url = 'https://discord.com/api/v10/auth/logout'
        self.members_url = 'https://discord.com/api/v10/guilds/{}/members'
        
        self.ws_gateway_query_params = '/?encoding=json&v=10'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36'
        }
        
        self.ws = None
        self.ws_send_queue = multiprocessing.Queue()
        self.message_counter = 0
        self.requester = requests.Session()
        self.servers_viewing = []
        self.print_traffic = False
        self.token = None
        self.heartbeat_interval = 0
        self.ws_ping_thread = None

    def do_request(self, method: str, url: str, data=None, headers=None, params=None):
        headers = {**self.headers, **(headers or {})}
        try:
            resp = self.requester.request(method, url, data=data, headers=headers, params=params)
            if self.print_traffic:
                print(f'{method} {url} with data {data} -- {resp.status_code}\n')
            return resp
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None
    def send_json_request(self, ws, request):
        ws.send(json.dumps(request))
    def receive_json_response(self, ws):
        response = ws.recv()
        if response:
            return json.loads(response)
    def heartbeat(self,interval,ws):
        print("Heartbeat started")
        while True:
            time.sleep(interval)
            heartbeatJson={
                "op": 1,
                "d": "null"
            }
            self.send_json_request(ws,heartbeatJson)
            print("Heartbeat sent")
    def connect_websocket(self):
        self.ws = websocket.WebSocket()
        self.ws.connect(self.retrieve_websocket_gateway())
        heartbeat_interval = self.receive_json_response(self.ws)['d']['heartbeat_interval'] / 1000
        threading.Thread(target=self.heartbeat, args=(heartbeat_interval, self.ws)).start()
        pyload= {
            "op": 2,
            "d": {
                "token": self.token,
                "properties": {
                    "$os": "windows",
                    "$browser": "chrome",
                    "$device": "pc"
                }
            }
        }
        self.send_json_request(self.ws,pyload)
        print("Websocket connected")

    def retrieve_server_channels(self, serverid: str):
        """ Retrieve a list of channels in the server. """
        req = self.do_request('GET', f'https://discord.com/api/v10/guilds/{serverid}/channels', headers={**self.headers, 'Authorization': self.token})
        
        if req:
            if req.status_code == 200:
                return req.json()
        
        return None

    def retrieve_websocket_gateway(self) -> str:
        """Attempts to get the websocket URL."""
        req = self.do_request('GET', self.gateway_url, headers={'Authorization': self.token})
        return req.json().get('url') if req and req.status_code == 200 else None
    def web_login(self, email: str, password: str) -> bool:
        """Attempts to login with the given credentials and stores the authtoken in self.token."""
        data = json.dumps({'email': email, 'password': password}).encode('utf-8')
        print(f'Attempting login of {email}: {"*" * len(password)}')

        req = self.do_request('POST', self.login_url, data=data, headers={'Content-Type': 'application/json'})
        if req and req.status_code == 200:
            self.token = req.json().get('token')
            return True
        return False
    def token_login(self, token: str) -> bool:
        """Attempts to login with the given token."""
        self.token = token
        return True

    def get_server_icon(self, server_id: str, guilds) -> str:
        """Retrieves the server icon URL if available."""
        for guild in guilds:
            if guild['id'] == server_id:
                icon_hash = guild.get('icon')
                if icon_hash:
                    return f"https://cdn.discordapp.com/icons/{server_id}/{icon_hash}.png"
        print("Server not found or has no icon.")
        return None
    def logout(self) -> bool:
        """Attempts to logout and closes the websocket client if opened."""
        data = json.dumps({'provider': None, 'token': None})

        if self.ws and self.ws.connected:
            self.ws.close()
            self.ws_send_queue.put('nosend')

        req = self.do_request('POST', self.logout_url, headers={'Authorization': self.token, 'Content-Type': 'application/json'}, data=data)
        return req.status_code == 204 if req else False

    def get_me(self) -> bool:
        """Downloads information about the client and stores it in self.me."""
        req = self.do_request('GET', self.me_url, headers={'Authorization': self.token})
        if req and req.status_code == 200:
            self.me = req.json()
            return True
        return False
    def get_dms(self):
        channels_response = self.do_request('GET',"https://discord.com/api/v9/users/@me/channels", headers={'Authorization': self.token})
        return channels_response
    def retrieve_channel_messages(self, channel_id: str):
        """Downloads messages for a specific channel ID."""
        request_url = f'https://discord.com/api/v10/channels/{channel_id}/messages'
        req = self.do_request('GET', request_url, headers={'Authorization': self.token})
        return req.json() if req and req.status_code == 200 else None

    def retrieve_servers(self):
        """Retrieves the list of servers (guilds) the bot is connected to."""
        req = self.do_request('GET', self.guilds_url, headers={'Authorization': self.token})
        return req.json() if req and req.status_code == 200 else []

    def send_message(self, channel_id: str, message: str, tts=False, nonce="123") -> bool:
        """Sends a message to a specific channel."""
        data = json.dumps({"content": message, "tts": tts, "nonce": nonce})
        request_url = f'https://discord.com/api/v10/channels/{channel_id}/messages'
        req = self.do_request('POST', request_url, headers={'Authorization': self.token, 'Content-Type': 'application/json'}, data=data)
        return req.status_code == 200 if req else False

    def send_start_typing(self, channel_id: str) -> bool:
        """Sends a signal to start typing in a specific channel."""
        request_url = f'https://discord.com/api/v10/channels/{channel_id}/typing'
        req = self.do_request('POST', request_url, headers={'Authorization': self.token})
        return req.status_code == 204 if req else False

    def send_presence_change(self, presence: str) -> bool:
        """Sends a presence update."""
        data = json.dumps({
            'op': 3,
            'd': {
                'status': presence,
                'since': 0,
                'activities': None,
                'afk': False
            }
        })
        self.send_json_request(self.ws,data)

        data = json.dumps({'status': presence})
        req = self.do_request('PATCH', self.settings_url, headers={'Authorization': self.token, 'Content-Type': 'application/json'}, data=data)
        return req.status_code == 200 if req else False

    def start_rpc(self):
        """Sends a game change update with bot avatar as image."""
        presence_payload = {
            "op": 3,
            "d": {
                "since": None,
                "activities": [
                    {
                        "name": "NeoCord",
                        "type": 0, 
                        "details": "Custom Cord",
                    }
                ],
                "status": "online",
                "afk": False
            }
        }

        self.send_json_request(self.ws, presence_payload)


    def send_view_server(self, server_id: str):
        """Sends a server-viewing update (OP 12) packet."""
        if server_id not in self.servers_viewing:
            self.servers_viewing.append(server_id)

        data = json.dumps({'op': 12, 'd': self.servers_viewing})
        self.websocket_send(data)

    def remove_view_server(self, server_id: str):
        """Removes a server from the view list and sends update."""
        if server_id in self.servers_viewing:
            self.servers_viewing.remove(server_id)

        data = json.dumps({'op': 12, 'd': self.servers_viewing})
        self.websocket_send(data)

    def set_print_traffic(self, print_traffic: bool):
        """Sets the traffic print setting."""
        self.print_traffic = print_traffic

    def get_guild_members(self, guild_id: str):
        """Retrieves members of a guild."""
        request_url = self.members_url.format(guild_id)
        req = self.do_request('GET', request_url, headers={'Authorization': self.token})
        return req.json() if req and req.status_code == 200 else None

    def start_typing_in_channel(self, channel_id: str):
        """Starts typing in a channel."""
        self.send_start_typing(channel_id)


    @cache
    def get_me_pfp(self) -> str:
        """Retrieves the profile picture URL for a specific user by ID."""
        headers = {
            'Authorization': self.token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        req = self.do_request('GET', self.me_url, headers=headers)

        if req.status_code == 200:
            user_data = req.json()
            avatar_hash = user_data.get('avatar')
            user_id = user_data.get('id')
            if avatar_hash:
                return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png?size=32"
            else:
                print("User has no avatar.")
                return None
        else:
            print(f"Failed to retrieve user data. Status code: {req.status_code}")
            return None
    @cache
    def get_user_pfp(self, user_id: str, size: int = 32) -> str:
        """
        Retrieves the profile picture URL for a specified user by ID.
        
        :param user_id: The Discord user ID.
        :param size: The desired avatar size (default is 32).
        :return: A string with the avatar URL or None if retrieval fails.
        """
        headers = {
            'Authorization': self.token,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        url = f"https://discord.com/api/v9/users/{user_id}"
        req = self.do_request('GET', url, headers=headers)
        
        if req.status_code == 200:
            user_data = req.json()
            avatar_hash = user_data.get('avatar')
            
            if avatar_hash:
                extension = "gif" if avatar_hash.startswith("a_") else "png"
                return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.{extension}?size={size}"
            else:
                discriminator = user_data.get('discriminator', '0')
                default_avatar = int(discriminator) % 5
                return f"https://cdn.discordapp.com/embed/avatars/{default_avatar}.png"
        else:
            print(f"Failed to retrieve user data. Status code: {req.status_code}")
            return None
