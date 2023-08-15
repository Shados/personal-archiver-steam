import sys
import traceback

import steam
from sqlalchemy import MetaData
from sqlalchemy.engine import Connection

from .db import insert_new_message
from .types import MessageRow


class LogClient(steam.Client):
    def __init__(self, metadata: MetaData, connection: Connection):
        super().__init__()
        self.metadata = metadata
        self.connection = connection

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user}")

    async def on_message(self, message: steam.Message) -> None:
        from pprint import pprint

        pprint(message)
        pprint(message.created_at)
        if not isinstance(message.channel, steam.channel.DMChannel):
            # print(f"Message isn't in a DMChannel: {message}")
            return
        author, author_id = message.author.name, message.author.id
        dm_with, dm_with_id = (
            message.channel.participant.name,
            message.channel.participant.id,
        )

        data: MessageRow = (
            message.id,
            dm_with_id,
            author_id,
            dm_with,
            author,
            message.created_at,
            message.content,
        )

        insert_new_message(self.metadata, self.connection, data)
        self.connection.commit()

    # Ensure we actually exit on unhandled errors; in the immortal words of Joe
    # Armstrong, *let it crash!*
    # An external service manager should bring it back up again, thus likely
    # restoring it to a known-good state.
    async def on_error(
        self, event: str, error: Exception, *args: object, **kwargs: object
    ) -> None:
        print(f"Hit exception during event {event}", file=sys.stderr)
        traceback.print_exception(error, file=sys.stderr)
        await self.close()
