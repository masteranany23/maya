import asyncio
from collections.abc import AsyncGenerator

from maya.voice.models import AudioFrame


class AudioRouter:
    """
    Fans out a single incoming AudioFrame stream into multiple independent subscriber streams.
    Ensures that multiple consumers (like VAD and STT) can read the same microphone data
    without draining a shared generator competitively.
    """
    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue[AudioFrame | None]] = []
        self._router_task: asyncio.Task[None] | None = None
        self._running = False

    def subscribe(self) -> AsyncGenerator[AudioFrame, None]:
        """Creates and returns a new subscriber stream."""
        queue: asyncio.Queue[AudioFrame | None] = asyncio.Queue()
        self._subscribers.append(queue)
        
        async def _generator() -> AsyncGenerator[AudioFrame, None]:
            try:
                while True:
                    frame = await queue.get()
                    if frame is None:
                        break
                    yield frame
            finally:
                if queue in self._subscribers:
                    self._subscribers.remove(queue)
                    
        return _generator()

    async def start(self, source_stream: AsyncGenerator[AudioFrame, None]) -> None:
        """Starts reading from the source and broadcasting to subscribers."""
        self._running = True
        
        async def _route_loop() -> None:
            try:
                async for frame in source_stream:
                    if not self._running:
                        break
                    # Broadcast to all active subscribers
                    for queue in self._subscribers:
                        queue.put_nowait(frame)
            finally:
                await self.stop()
                
        self._router_task = asyncio.create_task(_route_loop())

    async def stop(self) -> None:
        """Stops the router and closes all subscriber streams."""
        self._running = False
        if self._router_task and not self._router_task.done():
            self._router_task.cancel()
            
        # Send sentinel to close all subscribers
        for queue in list(self._subscribers):
            queue.put_nowait(None)
        
        self._subscribers.clear()
