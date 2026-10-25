"""Yapin' Ultimate Customizable Sticky Bot (Smart Image Edition)."""

import json, os, time, urllib.request, ssl, re

# 1. YOUR TOKEN
TOKEN = "yb_1485279f._a6Wklb_cV7uKiCCVxnyi0B4VImESrGR3j-hrhFh"
BASE = "https://www.yapin.gg/api/bot/v1"
SERVER_ID = "88a7b7d7-c2f6-4cc5-8208-ffed9c3093c6"

DATA_FILE = "sticky_data.json"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40, context=ctx) as r:
        return json.load(r)

def send(channel_id, content="", embed=None, components=None):
    body = {"content": content}
    if embed:
        body["embeds"] = [embed]
    if components:
        body["components"] = components
    return api("POST", f"/channels/{channel_id}/messages", body)

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        sticky_data = json.load(f)
else:
    sticky_data = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(sticky_data, f)

# 2. REGISTER THE COMMANDS
api("PUT", "/commands", {"commands": [
    {"name": "help", "description": "See all the commands the bot can do!"},
    {"name": "ping", "description": "Check if the bot is awake!"},
    {"name": "setsticky", "description": "Set a sticky. Optional color at the end! Ex: /setsticky #rules Rules! #FF0000"},
    {"name": "removesticky", "description": "Remove a sticky. Ex: /removesticky #rules"},
    {"name": "editsticky", "description": "Edit a sticky. Ex: /editsticky #rules New message! #00FF00"},
    {"name": "setlink", "description": "Add a link button. Ex: /setlink #rules https://google.com | Click Me!"},
]})

my_id = api("GET", "/me")["id"]
print("online as", api("GET", "/me")["username"])
print("Waiting for commands...")

# SMARTER helper function to find the image and color ANYWHERE in the message!
def parse_sticky_data(raw_message):
    image_url = None
    color = "#ff6b4a"
    
    # 1. Look for an image link ANYWHERE in the text
    img_match = re.search(r"(https?://\S+\.(?:png|jpg|jpeg|gif|webp))", raw_message, re.IGNORECASE)
    
    # Yapin' sometimes strips the file extension, so look for imgur links too!
    if not img_match:
        img_match = re.search(r"(https?://(?:i\.)?imgur\.com/\S+)", raw_message, re.IGNORECASE)

    if img_match:
        image_url = img_match.group(1)
        raw_message = raw_message.replace(image_url, "").strip() # Remove the link from the text
    
    # 2. Look for a hex color ANYWHERE in the text (like #FF0000)
    color_match = re.search(r"(#[0-9a-fA-F]{6})\b", raw_message)
    if color_match:
        color = color_match.group(1)
        raw_message = raw_message.replace(color, "").strip() # Remove the color from the text
        
    return raw_message.strip(), color, image_url

# Helper function to find a channel by name or blue bubble
def get_channel_id(target_raw):
    match = re.search(r"<#([a-zA-Z0-9-]+)>", target_raw)
    if match:
        return match.group(1)
    else:
        target_channel_name = target_raw.replace("#", "").lower()
        try:
            channels = api("GET", f"/servers/{SERVER_ID}/channels")["channels"]
            for c in channels:
                if c["name"].lower() == target_channel_name:
                    return c["id"]
        except Exception as e:
            print("REAL ERROR:", e)
    return None

# 3. LISTEN FOR EVENTS
last = api("GET", "/events?after=0&wait=0")["last"]
while True:
    try:
        out = api("GET", f"/events?after={last}&wait=25")
    except Exception as e:
        print("retrying:", e)
        time.sleep(3)
        continue

    for ev in out["events"]:
        last = ev["id"]
        d = ev["data"]

        if ev["type"] == "message":
            command = d.get("command")
            args = (d.get("args") or "").strip()

            # --- COMMAND: HELP ---
            if command == "help":
                help_embed = {
                    "title": "｡𖦹°‧ Stickynote Commands",
                    "description": "Here is everything I can do to help your server!",
                    "color": "#F2EBCB",
                    "fields": [
                        {
                            "name": "𐐂 /setsticky",
                            "value": "Sets a sticky message in a channel. You can add an optional hex color or image link at the end.\n*Example: `/setsticky #rules Read the rules! #FF0000`*",
                            "inline": False
                        },
                        {
                            "name": "𐐂 /editsticky",
                            "value": "Edits an existing sticky message in a channel.\n*Example: `/editsticky #rules New rules! #00FF00`*",
                            "inline": False
                        },
                        {
                            "name": "𐐂 /setlink",
                            "value": "Adds a custom link button to a sticky message. Type `none` to remove it.\n*Example: `/setlink #rules https://yapin.gg | Click Me!`*",
                            "inline": False
                        },
                        {
                            "name": "𐐂 /removesticky",
                            "value": "Deletes the sticky message from a channel.\n*Example: `/removesticky #rules`*",
                            "inline": False
                        },
                        {
                            "name": "𐐂 /ping",
                            "value": "Checks if I'm awake and listening!",
                            "inline": False
                        }
                    ],
                    "footer": {
                        "text": "Made with Python ഒ·˚ | Yapin' Stickynote"
                    }
                }
                send(d["channel_id"], "", embed=help_embed)

            # --- COMMAND: PING ---
            elif command == "ping":
                send(d["channel_id"], "im right here! just waiting for ur command <3")

            # --- COMMANDS: SET & EDIT ---
            elif command == "setsticky" or command == "editsticky":
                parts = args.split(" ", 1)
                
                if len(parts) < 2:
                    send(d["channel_id"], f"｡𖦹°‧ Usage: `/{command} #channel-name Your message here (Optional image link or #Color)`")
                else:
                    target_raw = parts[0]
                    full_message_raw = parts[1]
                    
                    clean_message, embed_color, image_url = parse_sticky_data(full_message_raw)
                    found_id = get_channel_id(target_raw)
                    
                    if found_id:
                        old_link = None
                        old_link_name = "Read More!"
                        if found_id in sticky_data:
                            old_link = sticky_data[found_id].get("link")
                            old_link_name = sticky_data[found_id].get("link_name", "Read More!")
                            
                        sticky_data[found_id] = {
                            "message": clean_message,
                            "color": embed_color,
                            "link": old_link,
                            "link_name": old_link_name,
                            "image": image_url # Saves the image!
                        }
                        save_data()
                        
                        action_word = "set" if command == "setsticky" else "edited"
                        send(d["channel_id"], f"｡𖦹°‧ Sticky message {action_word} for that channel with color {embed_color}!")
                    else:
                        send(d["channel_id"], f"｡𖦹°‧ I couldn't find that channel :(. Make sure I have permission to see it!")

            # --- COMMAND: SETLINK ---
            elif command == "setlink":
                parts = args.split(" ", 1)
                
                if len(parts) < 2:
                    send(d["channel_id"], f"｡𖦹°‧ Usage: `/setlink #channel URL | Button Name` (or `none` to remove)")
                else:
                    target_raw = parts[0]
                    link_data = parts[1].strip()
                    
                    found_id = get_channel_id(target_raw)
                    
                    if found_id and found_id in sticky_data:
                        if link_data.lower() == "none" or link_data.lower() == "remove":
                            sticky_data[found_id]["link"] = None
                            save_data()
                            send(d["channel_id"], f"｡𖦹°‧ Link button removed from that sticky!")
                        else:
                            if "|" in link_data:
                                link_url, link_name = link_data.split("|", 1)
                                link_url = link_url.strip()
                                link_name = link_name.strip()
                            else:
                                link_url = link_data
                                link_name = "Read More!" 
                            
                            sticky_data[found_id]["link"] = link_url
                            sticky_data[found_id]["link_name"] = link_name
                            save_data()
                            send(d["channel_id"], f"｡𖦹°‧ Link button updated to **{link_name}**!")
                    else:
                        send(d["channel_id"], f"｡𖦹°‧ I couldn't find a sticky message set for that channel. Set one first!")

            # --- COMMAND: REMOVE ---
            elif command == "removesticky":
                found_id = get_channel_id(args)
                        
                if found_id and found_id in sticky_data:
                    del sticky_data[found_id]
                    save_data()
                    send(d["channel_id"], f"｡𖦹°‧ Sticky message removed!")
                else:
                    send(d["channel_id"], f"｡𖦹°‧ No sticky message found for that channel :(")

            # --- STICKY LOGIC ---
            elif command is None:
                channel_id = d.get("channel_id")
                author_id = d.get("author_id")
                
                if channel_id in sticky_data and author_id != my_id:
                    time.sleep(0.5) 
                    
                    saved_data = sticky_data[channel_id]
                    sticky_msg = saved_data.get("message", "No message saved")
                    sticky_color = saved_data.get("color", "#ff6b4a")
                    sticky_link = saved_data.get("link")
                    sticky_link_name = saved_data.get("link_name", "Read More!")
                    sticky_image = saved_data.get("image") # Gets the saved image!
                    
                    my_embed = {
                        "title": "💭 Sticky Message",
                        "description": sticky_msg,
                        "color": sticky_color
                    }
                    
                    # If we have an image, add it to the embed box!
                    if sticky_image:
                        my_embed["image"] = {"url": sticky_image}
                    
                    my_buttons = None
                    if sticky_link:
                        my_buttons = [
                            {
                                "type": "row",
                                "components": [
                                    {
                                        "type": "button",
                                        "style": "link",
                                        "label": sticky_link_name,
                                        "url": sticky_link
                                    }
                                ]
                            }
                        ]
                    
                    send(channel_id, "", embed=my_embed, components=my_buttons)
