from dataclasses import dataclass, field


@dataclass
class DocumentBlock:
    block_id: int
    text: str
    source_type: str
    source_number: int
    start_offset: int
    end_offset: int


@dataclass
class ParsedDocument:
    filename: str
    file_type: str
    blocks: list[DocumentBlock]
    total_characters: int
    warnings: list[str] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n".join(block.text for block in self.blocks)
@dataclass
class DocumentChunk:
    chunk_id: int
    text: str
    start_offset: int
    end_offset: int
    estimated_tokens: int
    source_block_ids: list[int] = field(
        default_factory=list
    )