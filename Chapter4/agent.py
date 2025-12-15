from google.adk.agents import SequentialAgent, LlmAgent
from dotenv import load_dotenv
load_dotenv()

# Producer /Critique pipeline
model="gemini-3-pro-preview"
# The first agent generates the initial draft.
generator = LlmAgent( name="DraftWriter",
model=model, 
    description="Generates initial draft content on a given subject.", instruction=
    """Write a single, technically rigorous paragraph about the user’s subject for a CTO/PhD-level audience.

Requirements:

Audience: senior technical leadership and domain experts; assume strong math/engineering literacy.
Length: 120–180 words, 5–7 sentences, dense and information-rich.
Include (in this order, within one paragraph):
A precise definition (what it is / scope boundaries).
The core mechanism or principle of operation (high-level but technically grounded).
Key system components / architecture or main variables (as applicable).
The dominant constraints and failure modes (practical + theoretical).
The primary tradeoffs (e.g., performance vs. cost vs. reliability vs. complexity).
One concrete deployment/use-case example relevant to industry.
Precision rules:
Do not invent facts, numbers, percentages, dates, or “recent breakthroughs” unless explicitly provided by the user.
If a claim depends on missing context, state it as an assumption (e.g., “Assuming X…”).
Avoid marketing language; prefer crisp technical phrasing and conditional statements when uncertain.
Output only the paragraph (no headings, lists, markdown, or code blocks).
Assumptions
The user’s chat message provides the “subject” and any needed constraints/context unless you explicitly ask for them""", output_key="draft_text") # The output is saved to this state key. 
# The second agent critiques the draft from the first agent.
reviewer = LlmAgent(
name="FactChecker",
model=model,
description="Reviews a given text for factual accuracy and provides a structured critique.",
instruction="""
You are a meticulous fact-checker.
Evaluate every factual claim in the text. Treat undefined terms, hidden assumptions, and overstated generalizations as potential errors.
Output requirements:

Return ONLY valid JSON (no markdown fences) with exactly these keys:
"status": "ACCURATE" or "INACCURATE"
"reasoning": A concise, technical explanation that:
quotes or paraphrases the specific claim(s) you evaluated,
states whether each is supported, unsupported, misleading, or wrong,
explains what additional information would be required to make uncertain claims verifiable.
Decision rule:

Set "INACCURATE" if any material claim is wrong, misleading, or unverifiable from the text as written (e.g., implied numbers, “more efficient”, “recent breakthroughs” without evidence). Otherwise set "ACCURATE".
Style constraints:

No extra keys, no lists outside the JSON string, no hedging without explanation.
If the text contains no checkable claims, set "INACCURATE" and explain why.
""",
output_key="review_output")# The structured dictionary is savedhere.
# The SequentialAgent ensures the generator runs before the reviewer.
review_pipeline = SequentialAgent(
name="WriteAndReview_Pipeline",
sub_agents=[generator, reviewer])
# Execution Flow:
# 1. generator runs -> saves its paragraph to state['draft_text'].
# 2. reviewer runs -> reads state['draft_text'] and saves its dictionary output to state['review_output'].
root_agent = review_pipeline
