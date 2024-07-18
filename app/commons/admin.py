from sqladmin import ModelView

from app.models import Chat, Message, User


class UserAdmin(ModelView, model=User):
    column_list = [column.key for column in User.__table__.columns]
    column_searchable_list = [column.key for column in User.__table__.columns]
    column_filters = [column.key for column in User.__table__.columns]
    form_columns = [column.key for column in User.__table__.columns]

    async def scaffold_list(self):
        return await super().scaffold_list()

    async def scaffold_form(self):
        return await super().scaffold_form()


class ChatAdmin(ModelView, model=Chat):
    column_list = [column.key for column in Chat.__table__.columns]
    column_searchable_list = [column.key for column in Chat.__table__.columns]
    column_filters = [column.key for column in Chat.__table__.columns]
    form_columns = [column.key for column in Chat.__table__.columns]

    async def scaffold_list(self):
        return await super().scaffold_list()

    async def scaffold_form(self):
        return await super().scaffold_form()


class MessageAdmin(ModelView, model=Message):
    column_list = [column.key for column in Message.__table__.columns]
    column_searchable_list = [column.key for column in Message.__table__.columns]
    column_filters = [column.key for column in Message.__table__.columns]
    form_columns = [column.key for column in Message.__table__.columns]

    async def scaffold_list(self):
        return await super().scaffold_list()

    async def scaffold_form(self):
        return await super().scaffold_form()


admins = [UserAdmin, ChatAdmin, MessageAdmin]
