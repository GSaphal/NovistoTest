# Approach, Assumptions, Next Steps

## Approach

I wanted to work with a test-driven approach where each individual component of the process
could be tested on its own through unit tests, the flows between components could be tested
through integration tests, and the whole thing end-to-end through smoke tests.

Since it's a simple application with few components, I kept everything within the `app`
folder as small, individual Python files, one per step, each easy to test in isolation. There's
a matching `tests` folder with unit/integration/smoke tests for each of those steps.

So, since I had to build an access-controlled RAG system, I started with access management
first. Getting that in place early, and keeping it deliberately simple, meant I could layer
retrieval and the agent on top of it without having to retrofit access control later.

After that I did the PDF reading, where I noticed some documents had a label directly in thetext marking a section as confidential. So I added logic during chunking to detect that label
and narrow just the affected chunk (and the one after it) to the roles named nearby, rather
than treating the whole document as restricted. That's what lets a single company-wide
document carry one exec-only paragraph without needing that modeled separately in the
manifest.

With chunks and their access labels in place, I embed each chunk with OpenAI's embedding model
and store it in Postgres database as one row per chunk, with the access
roles stored as a array column. That means the permission check can happen directly
in the retrieval SQL query instead of as a separate filtering step
afterwards i.e A user isn't allowed to see is never pulled out of the database in the
first place.

Next, I wrapped that retrieval layer behind an MCP server exposing two tools,
`search_knowledge` and `get_document`. This was an important decision: the tools take the
caller's token, not their roles, and resolve the token to roles themselves, server-side. That
way nothing calling the tool can just claim a role; the enforcement
point is the tool call itself, not the prompt.

For the agent, I kept it to a straightforward tool-calling loop against the OpenAI chat
completions API. The system prompt is doing a lot of the safety work here. Citations returned across all tool calls in a conversation are
accumulated and deduped (by document and chunk) so the final answer can show exactly what it
was grounded in.

Finally, I put a thin FastAPI layer in front of the agent, checking the token before even
calling the agent, so an invalid token fails fast and a minimal static chat page so the whole
flow could be exercised by hand instead of only through curl or automated tests.

## Assumptions

I wanted to keep things deliberately simple, since this is a POC. Some of the approaches I took are considerably naive but are naive on purpose:

- Permissions are set on the chunk, not the whole document. This was the main design call — it's what lets one restricted paragraph sit inside an otherwise public document, without having to add per-paragraph info anywhere in the manifest.

- If two documents disagree on a fact, like two different prices for the same plan, the system cites both and says which one looks more current, instead of silently picking one for the user.

- If there's no evidence for something, the agent just says so instead of guessing. That's treated as a correct answer, not a failure.

## What I skipped

- Reranking or hybrid retrieval;just plain cosine similarity right now.

- No real evaluation of chunking/retrieval quality. I only checked it with a handful of known-answer smoke questions, not against an actual ground truth.

- No multi-turn memory or streaming. Each `/ask` call is independent, and the UI waits for the full answer instead of streaming it.

- No logging of tool calls, latency, or token spend yet.

## Next steps

- Build a small set of questions with expected citations and run it through [DeepEval](https://github.com/confident-ai/deepeval) instead of the current smoke-test style checks: it has metrics built for RAG (faithfulness, relevancy, contextual precision/recall) which fit better than just matching expected substrings.

- Improve the PDF reading approach. Instead of simple package, use external services or open source services better suited. Also, markers in the PDF has to be handled differently while reading from the PDF itself.

- Add logging and improve traceability

- Add hybrid retrieval (keyword + vector) so exact numbers and table rows aren't missed by pure similarity search.

- Add multi-turn sessions with memory and streamed responses in the API and UI.
