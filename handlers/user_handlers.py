from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, StartMode

from database.action_data_class import DataInteraction
from states.state_groups import startSG

user_router = Router()


@user_router.message(CommandStart())
async def start_dialog(msg: Message, dialog_manager: DialogManager):
    await dialog_manager.start(state=startSG.start, mode=StartMode.RESET_STACK)
