import re
from collections.abc import AsyncGenerator


class SemanticBuffer:
    """Accumulates LLM tokens and yields complete phrases/sentences."""
    
    def __init__(self) -> None:
        self.buffer = ""
        # Split on sentence boundaries: . ! ? followed by space or end of string, or newline
        self.boundary_pattern = re.compile(r'([.!?]+(?:\s+|$))|(\n+)')
        
    async def process_stream(self, token_stream: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """Reads a token stream and yields complete semantic chunks."""
        async for token in token_stream:
            self.buffer += token
            
            matches = list(self.boundary_pattern.finditer(self.buffer))
            if matches:
                last_match = matches[-1]
                split_point = last_match.end()
                
                phrase = self.buffer[:split_point].strip()
                if phrase:
                    yield phrase
                    
                self.buffer = self.buffer[split_point:]
                
        final_phrase = self.buffer.strip()
        if final_phrase:
            yield final_phrase
            self.buffer = ""
