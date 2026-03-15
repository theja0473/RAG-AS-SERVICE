"""Entity and relationship extraction for knowledge graph construction.

This module uses LLM-based extraction to identify entities and relationships
from document text, building the knowledge graph incrementally.
"""

from typing import List, Dict, Any, Tuple
import json
import logging
import re

from langchain_ollama import OllamaLLM

from config import get_settings

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """Extract entities and relationships from the following text.

Return a JSON object with two arrays:
- "entities": each with "name" (string) and "type" (one of: PERSON, ORGANIZATION, LOCATION, CONCEPT, TECHNOLOGY, EVENT, DATE, PRODUCT, OTHER)
- "relationships": each with "source" (entity name), "target" (entity name), and "type" (a short verb phrase like WORKS_FOR, LOCATED_IN, PART_OF, CREATED_BY, RELATED_TO, etc.)

Rules:
- Entity names should be normalized (e.g., "Dr. Smith" -> "Smith", "New York City" -> "New York City")
- Only extract clearly stated facts, do not infer
- Keep relationship types concise and uppercase with underscores
- Return ONLY valid JSON, no other text

Text:
{text}

JSON:"""


class EntityExtractor:
    """Extracts entities and relationships from text using LLM."""

    def __init__(self, model_name: str = None):
        """Initialize entity extractor.

        Args:
            model_name: Ollama model name for extraction.
        """
        settings = get_settings()
        self.model_name = model_name or settings.llm_model
        self.ollama_base_url = settings.ollama_base_url

        self.llm = OllamaLLM(
            base_url=self.ollama_base_url,
            model=self.model_name,
            temperature=0.0,
        )

    def extract(self, text: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Extract entities and relationships from text.

        Args:
            text: Input text to extract from.

        Returns:
            Tuple of (entities, relationships) where each is a list of dicts.
        """
        if not text or not text.strip():
            return [], []

        # Truncate very long texts to avoid LLM context limits
        max_chars = 3000
        if len(text) > max_chars:
            text = text[:max_chars]

        prompt = EXTRACTION_PROMPT.format(text=text)

        try:
            response = self.llm.invoke(prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.warning("Entity extraction failed: %s", e)
            return [], []

    def _parse_response(
        self, response: str
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Parse LLM response into entities and relationships.

        Args:
            response: Raw LLM response text.

        Returns:
            Tuple of (entities, relationships).
        """
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            logger.warning("No JSON found in extraction response")
            return [], []

        try:
            data = json.loads(json_match.group())
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in extraction response")
            return [], []

        entities = data.get("entities", [])
        relationships = data.get("relationships", [])

        # Validate entity structure
        valid_entities = []
        for e in entities:
            if isinstance(e, dict) and "name" in e and "type" in e:
                valid_entities.append({
                    "name": str(e["name"]).strip(),
                    "type": str(e["type"]).strip().upper(),
                })

        # Validate relationship structure
        valid_relationships = []
        entity_names = {e["name"].lower() for e in valid_entities}
        for r in relationships:
            if (
                isinstance(r, dict)
                and "source" in r
                and "target" in r
                and "type" in r
            ):
                source = str(r["source"]).strip()
                target = str(r["target"]).strip()
                # Only keep relationships where both entities exist
                if source.lower() in entity_names and target.lower() in entity_names:
                    valid_relationships.append({
                        "source": source,
                        "target": target,
                        "type": str(r["type"]).strip().upper().replace(" ", "_"),
                    })

        return valid_entities, valid_relationships

    def extract_from_chunks(
        self,
        chunks: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Extract entities and relationships from multiple chunks.

        Deduplicates entities across chunks.

        Args:
            chunks: List of chunk dicts with 'text' key.

        Returns:
            Tuple of (deduplicated entities, all relationships).
        """
        all_entities: Dict[str, Dict[str, str]] = {}
        all_relationships: List[Dict[str, str]] = []

        for chunk in chunks:
            text = chunk.get("text", "")
            entities, relationships = self.extract(text)

            for entity in entities:
                key = entity["name"].lower()
                if key not in all_entities:
                    all_entities[key] = entity

            all_relationships.extend(relationships)

        # Deduplicate relationships
        seen_rels = set()
        unique_rels = []
        for rel in all_relationships:
            key = (rel["source"].lower(), rel["target"].lower(), rel["type"])
            if key not in seen_rels:
                seen_rels.add(key)
                unique_rels.append(rel)

        return list(all_entities.values()), unique_rels


# Global extractor instance
_extractor: EntityExtractor = None


def get_entity_extractor() -> EntityExtractor:
    """Get global entity extractor instance.

    Returns:
        Singleton EntityExtractor instance.
    """
    global _extractor
    if _extractor is None:
        _extractor = EntityExtractor()
    return _extractor
