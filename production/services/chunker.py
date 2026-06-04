import re
from typing import List, Dict, Any
from config import get_settings

settings = get_settings()

# ── Token Estimator (rough: 1 token ≈ 4 chars) ──────────
def estimate_tokens(text: str) -> int:
    return len(text) // 4

# ── Text Chunker ─────────────────────────────────────────
def chunk_text(
    text: str,
    chunk_size: int = 4000,
    overlap: int = 200
) -> List[Dict[str, Any]]:
    
    if estimate_tokens(text) <= chunk_size:
        return [{"chunk_id": 0, "content": text, "tokens": estimate_tokens(text)}]

    # Split by paragraphs first
    paragraphs = re.split(r'\n\s*\n', text)
    
    chunks = []
    current_chunk = ""
    chunk_id = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        test_chunk = current_chunk + "\n\n" + para if current_chunk else para

        if estimate_tokens(test_chunk) <= chunk_size:
            current_chunk = test_chunk
        else:
            # Save current chunk
            if current_chunk:
                chunks.append({
                    "chunk_id": chunk_id,
                    "content": current_chunk,
                    "tokens": estimate_tokens(current_chunk)
                })
                chunk_id += 1
                # Overlap — keep last part
                words = current_chunk.split()
                overlap_text = " ".join(words[-overlap:]) if len(words) > overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + para
            else:
                # Single paragraph too large — split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sent in sentences:
                    test = current_chunk + " " + sent if current_chunk else sent
                    if estimate_tokens(test) <= chunk_size:
                        current_chunk = test
                    else:
                        if current_chunk:
                            chunks.append({
                                "chunk_id": chunk_id,
                                "content": current_chunk,
                                "tokens": estimate_tokens(current_chunk)
                            })
                            chunk_id += 1
                        current_chunk = sent

    # Last chunk
    if current_chunk:
        chunks.append({
            "chunk_id": chunk_id,
            "content": current_chunk,
            "tokens": estimate_tokens(current_chunk)
        })

    return chunks

# ── Page Chunker (for PDFs) ──────────────────────────────
def chunk_pages(
    pages: List[str],
    chunk_size: int = 4000
) -> List[Dict[str, Any]]:
    
    chunks = []
    current_chunk = ""
    current_pages = []
    chunk_id = 0

    for page_num, page_text in enumerate(pages):
        test = current_chunk + "\n" + page_text if current_chunk else page_text

        if estimate_tokens(test) <= chunk_size:
            current_chunk = test
            current_pages.append(page_num + 1)
        else:
            if current_chunk:
                chunks.append({
                    "chunk_id": chunk_id,
                    "content": current_chunk,
                    "pages": current_pages,
                    "tokens": estimate_tokens(current_chunk)
                })
                chunk_id += 1
            current_chunk = page_text
            current_pages = [page_num + 1]

    if current_chunk:
        chunks.append({
            "chunk_id": chunk_id,
            "content": current_chunk,
            "pages": current_pages,
            "tokens": estimate_tokens(current_chunk)
        })

    return chunks

# ── Merge Chunk Results ──────────────────────────────────
def merge_json_results(results: List[dict]) -> dict:
    if not results:
        return {}
    if len(results) == 1:
        return results[0]

    merged = {}
    for result in results:
        for key, value in result.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, list) and isinstance(merged[key], list):
                merged[key].extend(value)
            elif isinstance(value, (int, float)) and isinstance(merged[key], (int, float)):
                merged[key] = max(merged[key], value)
            elif value and not merged[key]:
                merged[key] = value
    return merged

def merge_text_results(results: List[str]) -> str:
    return "\n\n".join(r for r in results if r.strip())
