from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import ChatThread
from uuid import UUID




class ChatThreadRepository:

    def __init__(self, session:AsyncSession):
        self.session = session

    #创建新会话
    async def add(self, chat_thread: ChatThread):
        self.session.add(chat_thread)


    #根据用户ID获取用户的所有会话列表
    async def list_by_user(self, user_id: int) -> list[ChatThread]:
        result = await self.session.scalars(
            select(ChatThread)
            .where(ChatThread.user_id == user_id)
            .order_by(
                ChatThread.updated_at.desc(),
                ChatThread.created_at.desc(),
            )
        )
        return list(result.all())


    #根据用户ID和会话ID获取会话
    #直接使用用户ID和会话ID可以从根本上防止用户越权访问其他用户的会话
    async def find_owned(
        self,
        thread_id: UUID,
        user_id: int,
    ) -> ChatThread | None:
        return await self.session.scalar(
            select(ChatThread).where(
                ChatThread.id == thread_id,
                ChatThread.user_id == user_id,
            )
        )

    async def delete(self, thread: ChatThread) -> None:
        await self.session.delete(thread)