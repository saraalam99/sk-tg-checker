import asyncio
import logging
import random
from telethon.sync import TelegramClient, errors, functions
from telethon.tl import types
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
load_dotenv()

def get_human_readable_user_status(status: types.TypeUserStatus):
    if isinstance(status, types.UserStatusOnline):
        return "Currently online"
    elif isinstance(status, types.UserStatusOffline):
        return status.was_online.strftime("%Y-%m-%d %H:%M:%S %Z")
    elif isinstance(status, types.UserStatusRecently):
        return "Last seen recently"
    elif isinstance(status, types.UserStatusLastWeek):
        return "Last seen last week"
    elif isinstance(status, types.UserStatusLastMonth):
        return "Last seen last month"
    else:
        return "Unknown"

async def get_names(client: TelegramClient, phone_number: str, download_profile_photos: bool = False) -> dict:
    result = {}
    logger.info(f"Checking: {phone_number=} ...")
    try:
        contact = types.InputPhoneContact(client_id=0, phone=phone_number, first_name="", last_name="")
        contacts = await client(functions.contacts.ImportContactsRequest([contact]))
        if contacts.users:
            user = contacts.users[0]
            result = {
                "number": phone_number,
                "status": "Registered",
                "username": user.username if user.username else "No username",
                "last_seen": get_human_readable_user_status(user.status)
            }
            if download_profile_photos and user.photo:
                photo = await client.download_profile_photo(user)
                result["profile_photo"] = photo
        else:
            result = {"number": phone_number, "status": "Not Registered", "username": None, "last_seen": None}
    except errors.FloodWaitError as e:
        result = {"number": phone_number, "status": f"Flood wait: {e.seconds} seconds", "username": None, "last_seen": None}
    except Exception as e:
        result = {"number": phone_number, "status": f"Error: {str(e)}", "username": None, "last_seen": None}
    finally:
        return result

async def login(api_id, api_hash, phone_number):
    client = TelegramClient("anon", api_id, api_hash)
    await client.start(phone=phone_number)
    return client

async def validate_users(client, phone_numbers, download_profile_photos):
    results = []
    for number in phone_numbers:
        result = await get_names(client, number, download_profile_photos)
        results.append(result)
    return results

class TelegramPhoneNumberChecker:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = None

    async def __aenter__(self):
        self.client = await login(self.api_id, self.api_hash, self.phone_number)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.client.disconnect()

    async def check_numbers(self, phone_numbers, download_profile_photos=False):
        results = []
        for number in phone_numbers:
            result = await get_names(self.client, number, download_profile_photos)
            results.append(result)
            await asyncio.sleep(random.uniform(1, 3))  # Add delay between requests
        return results
