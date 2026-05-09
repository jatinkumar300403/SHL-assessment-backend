# Approach Document: SHL Conversational Agent

## 1. Design Choices & Architecture
The objective was to build a stateless conversational agent capable of traversing the spectrum from vague intent to grounded SHL assessment recommendations while strictly adhering to a complex JSON schema and a 30-second latency timeout.

**Tech Stack:**
- **FastAPI**: Chosen for its lightweight, high-performance asynchronous server capabilities and native Pydantic integration, ensuring the API contract is strictly maintained.
- **LLM (`gemini-flash-latest`)**: Google Gemini was selected due to its massive context window and native `response_schema` structured output support, which guarantees 100% compliance with the requested JSON schema.
- **Deployment (Hugging Face Spaces)**: Initially deployed on Render, the architecture was migrated to Hugging Face Spaces (Docker tier). Render's free tier spins down after 15 minutes and suffers a 50-second cold start delay, which would instantly fail the 30-second latency limit constraint during evaluation. Hugging Face Spaces remain active for 48 hours without spinning down, ensuring instant 24/7 responsiveness.

## 2. Retrieval Setup
With a highly specialized product catalog of 377 SHL Individual Test Solutions, a robust vector-search approach was favored over context-stuffing.
- **Vector Store**: A local **ChromaDB** instance was configured with persistent storage.
- **Embeddings**: We utilized `sentence-transformers` (`all-MiniLM-L6-v2`) to generate semantic embeddings for a concatenated string of each product's `name`, `description`, `keys`, and `job_levels`. This model runs flawlessly on the CPU, removing the latency and API costs of external embedding endpoints.
- **Retrieval Strategy**: When a search intent is detected, ChromaDB retrieves the top 15 most semantically similar assessments. These matches, including their secure URLs, are injected directly into the final LLM prompt.

## 3. Prompt Design
To prevent hallucination and improve reasoning speed, I implemented a **Two-Stage Architecture**:
1. **Intent Prompt**: A preliminary LLM pass focuses solely on classifying the *state* of the conversation. It determines boolean flags (`is_vague`, `is_off_topic`) and dynamically synthesizes a targeted `search_query` based on user constraints.
2. **System Prompt**: The secondary LLM pass enforces the SHL persona. It is strictly instructed to recommend *only* from the injected list of 15 retrieved assessments, naturally grounding the response in factual catalog data and preventing URL hallucination.

## 4. Evaluation Method
Evaluation was handled through a combination of strict schema enforcement and automated behavioral probing:
- **Schema Compliance**: Pydantic strictly validates both the LLM output and the FastAPI response. Using `GenerateContentConfig(response_schema=...)` virtually eliminated parsing errors.
- **Automated Behavioral Probes (`evaluate.py`)**: A custom automated test script was built to continuously hit the `/chat` endpoint with specific edge cases:
  - **Vague queries**: Asserting the agent returns 0 recommendations and asks clarifying questions.
  - **Specific queries**: Asserting recommendations are populated and verifying that all returned URLs originate strictly from the SHL catalog domain.
  - **Off-topic questions**: Asserting a polite refusal without attempting to search.

## 5. What Did Not Work
- **Single-Pass Prompting**: Attempting to have the LLM decide if it needs to search, formulate the search, and respond all in a single pass was highly error-prone due to the stateless nature of the API. Splitting it into an Intent pass and a Response pass vastly improved accuracy.
- **Gemini Experimental Models**: Initially, `gemini-2.5-flash` was used, but its experimental free-tier quotas (limit of 20 requests) caused `429 RESOURCE_EXHAUSTED` internal server errors during rapid evaluation testing. Reverting to the stable `gemini-flash-latest` bypassed these strict rate limits.
- **Render Deployment**: As mentioned, Render's 15-minute sleep cycle caused severe cold-start timeouts.

## 6. How Improvement Was Measured
Improvement was measured actively through the `evaluate.py` test suite. By tracking the pass-rate of behavioral probes during iterations, I quantified improvements:
- Switching from keyword search to semantic embeddings improved the relevance of retrieved tests (Recall@K) for synonymous queries (e.g., "leadership" vs "management").
- Decoupling the Intent Prompt from the System Prompt eliminated schema-breaking hallucinations and brought the behavioral probe pass-rate from roughly 60% to a reliable 100%.

---
**LLM Used in Implementation**: Google Gemini (`gemini-flash-latest`).
**AI Tools Used**: I used an Agentic AI coding assistant to rapidly prototype the FastAPI scaffolding, script the vector ingestion logic, and iterate on the two-stage prompt engineering.
