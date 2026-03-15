"""Answer generation for RAG pipeline.

This module provides LLM-based answer generation with source citation
and grounding in retrieved context.
"""

from typing import List, Dict, Any

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

from config import get_settings


class AnswerGenerator:
    """Answer generator using Ollama LLM.

    Generates grounded answers with source citations based on retrieved context.
    """

    def __init__(self, model_name: str = None):
        """Initialize answer generator.

        Args:
            model_name: Ollama model name.
        """
        settings = get_settings()
        self.model_name = model_name or settings.llm_model
        self.ollama_base_url = settings.ollama_base_url

        # Initialize Ollama LLM
        self.llm = OllamaLLM(
            base_url=self.ollama_base_url,
            model=self.model_name,
            temperature=0.1,
        )

        # System prompt for grounded answers
        self.system_prompt = """You are a helpful AI assistant that answers questions based on the provided context.

IMPORTANT RULES:
1. Only use information from the provided context to answer questions
2. Cite sources by referencing the source name in brackets, e.g., [Source: document.pdf]
3. If the context doesn't contain enough information, clearly state "I don't have enough information to answer this question based on the provided documents"
4. Do not make up or hallucinate information
5. Be concise and direct in your answers
6. If multiple sources support your answer, cite all relevant sources

Context:
{context}

Question: {question}

Answer:"""

        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template=self.system_prompt,
        )

    def generate(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate answer based on query and retrieved contexts.

        Args:
            query: User question.
            contexts: List of retrieved context dictionaries with content, source, and score.

        Returns:
            Dictionary with answer, sources, and metadata.
        """
        if not contexts:
            return {
                "answer": "I don't have any relevant information to answer this question. Please upload relevant documents first.",
                "sources": [],
                "num_sources": 0,
            }

        # Format context with source attribution
        context_parts = []
        sources = []

        for i, ctx in enumerate(contexts, 1):
            content = ctx.get("content", "")
            source = ctx.get("source", "Unknown")
            score = ctx.get("score", 0)

            context_parts.append(f"[Source {i}: {source}]\n{content}")
            sources.append({
                "id": i,
                "source": source,
                "content": content[:200] + "..." if len(content) > 200 else content,
                "score": round(score, 3),
            })

        # Combine contexts
        full_context = "\n\n".join(context_parts)

        # Generate answer
        prompt = self.prompt_template.format(
            context=full_context,
            question=query,
        )

        try:
            answer = self.llm.invoke(prompt)

            return {
                "answer": answer.strip(),
                "sources": sources,
                "num_sources": len(sources),
            }

        except Exception as e:
            return {
                "answer": f"Error generating answer: {str(e)}",
                "sources": sources,
                "num_sources": len(sources),
                "error": str(e),
            }

    def generate_with_conversation_history(
        self,
        query: str,
        contexts: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Generate answer with conversation history.

        Args:
            query: User question.
            contexts: List of retrieved contexts.
            conversation_history: Optional conversation history.

        Returns:
            Dictionary with answer, sources, and metadata.
        """
        # For now, just use basic generation
        # TODO(#1): Implement conversation-aware generation with history context
        return self.generate(query, contexts)

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Ollama server.

        Returns:
            Dictionary with connection status.
        """
        try:
            response = self.llm.invoke("Hello")
            return {
                "status": "success",
                "message": "Connected to Ollama successfully",
                "model": self.model_name,
                "response": response[:100] if response else None,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to connect to Ollama: {str(e)}",
                "model": self.model_name,
            }


# Global generator instance
_generator: AnswerGenerator = None


def get_generator() -> AnswerGenerator:
    """Get global answer generator instance.

    Returns:
        Singleton AnswerGenerator instance.
    """
    global _generator
    if _generator is None:
        _generator = AnswerGenerator()
    return _generator
