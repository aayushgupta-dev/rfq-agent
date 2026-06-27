# Generative AI Expert / Applied AI Engineer: Prototyping Assignment

**Prompt-Driven RFQ Data Generation, Extraction & Vendor Comparison System**

*Agillos E-Commerce Pvt. Ltd · Ground Floor, South Tower, Vaishnavi Tech Park, Sarjapur Main Road, Bengaluru 560103 · CIN: U52300KA2016PTC092938*

---

## Important Note

This assignment is designed to evaluate your ability to build a **prompt-driven AI prototype** for a real-world procurement workflow.

The focus is on:

- Prompt quality
- Realistic data generation
- AI accuracy
- Handling messy and exceptional cases
- Buyer-facing product thinking
- Useful vendor comparison
- Evidence-backed outputs

This should be a working AI prototype, not a static dashboard or hardcoded demo. The AI should actively process inputs and generate outputs.

## 1. Goal

Build a working prototype that can:

1. Generate a realistic RFQ and vendor response dataset using prompts
2. Generate complex, messy, real-world-like vendor data using prompts
3. Use prompts to support UI/UX generation or buyer-facing product design
4. Extract important information from vendor responses
5. Identify missing, unclear, conflicting, or risky information
6. Compare vendors across technical, commercial, scope, timeline, and risk dimensions
7. Present the comparison in a way that helps a buyer understand vendor differences clearly

The core expectation is to demonstrate how strong prompt design can create reliable AI workflows for procurement use cases.

## 2. Why This Assignment Exists

In procurement workflows, vendors rarely respond in a clean and standardized format.

Vendor proposals may contain different formats, pricing labels, missing information, contradictory statements, assumptions, vague timelines, unclear compliance claims, bundled pricing, or irrelevant marketing content.

Buyers need to understand what each vendor has submitted, what is missing, where the risks are, and how vendors differ.

AI can help, but only if the prompts and workflow are designed to produce accurate, grounded, and useful outputs.

## 3. What We Want to Evaluate

We want to understand how you approach:

- Prompt writing
- Prompt chaining
- AI-generated test data
- UI/UX generation prompts
- Extraction agents
- Comparison agents
- Exception handling
- Hallucination control
- Buyer-facing product experience

We are not looking for a perfect enterprise product. We are looking for a thoughtful working prototype that demonstrates strong prompt design and practical AI thinking.

## 4. Use Case

Assume the RFQ is for a marketing services procurement event.

The RFQ should include the following line items:

1. Strategy and creative development
2. TVC development
3. TVC production
4. Social organic content
5. Social paid media planning
6. Social paid media buying and optimization
7. Kids advertising and claims compliance review
8. Launch program management

The RFQ should include:

- General information
- Timelines
- Scope of work
- Item requests
- Commercial expectations
- Vendor questionnaire
- Compliance requirements

## 5. Assignment Scope

Your prototype should cover the following flow:

**RFQ Generation → Vendor Response Input/Upload → Extraction Agent → Comparison Agent → Buyer-Facing UI**

The prototype can be built as a web app, Streamlit app, notebook, API-based prototype, or any other usable format.

The UI can be simple, but it should support the buyer's understanding of the RFQ and vendor comparison.

## 6. Required Screens

Your prototype should include the following screens or equivalent flows.

### Screen 1: RFQ Overview

This screen should show the RFQ, including scope, timelines, item requests, commercial expectations, questionnaire, and compliance requirements.

It should make it clear what the procurement event is about and what vendors are expected to respond to.

### Screen 2: Vendor Upload / Input

This screen should allow vendor responses to be uploaded, pasted, or otherwise provided as input.

The system should dynamically process the input rather than relying on hardcoded outputs.

### Screen 3: Extraction Review

This screen should show the extracted information from each vendor response.

It should highlight important fields, missing information, unclear data, conflicting statements, risks, and evidence snippets.

### Screen 4: Vendor Comparison

This screen should compare vendors across technical, commercial, scope, timeline, compliance, and risk dimensions.

The comparison should help the buyer understand which vendors are comparable, where they differ, and what needs further review.

### Screen 5 (Optional): Prompt Trace / Prompt Pack View

This screen or section should show the prompts used in the workflow and at least one trace of input → prompt → model output → final output.

This can also be provided as a separate document, README section, or notebook output.

## 7. Agents Needed (High Level)

Your prototype should include the following high-level AI agents or prompt-driven modules.

### 1. RFQ Generation Agent

Generates a realistic RFQ for the given procurement scenario.

### 2. Vendor Response Generation Agent

Generates realistic and messy vendor responses with varying levels of completeness, clarity, assumptions, and commercial detail.

This does not need to be a UI screen, but the prompt used to generate vendor data must be included in the Prompt Pack.

### 3. UI/UX Generation Agent

Generates or guides buyer-facing UI/UX structure, dashboard sections, UX copy, and comparison views.

### 4. Extraction Agent

Extracts important procurement information from vendor responses and identifies missing, unclear, conflicting, or unsupported information.

### 5. Comparison Agent

Compares vendors using extracted information and source evidence, with focus on buyer usability and decision support.

## 8. Part A: RFQ and Vendor Data Generation

Create prompts that generate a realistic RFQ and vendor response dataset.

The generated data should feel like a real procurement scenario, not a clean sample dataset.

Your generated dataset should include:

- One RFQ
- At least 3 vendor responses
- Different vendor styles and response quality
- Technical, commercial, timeline, and compliance information
- Realistic messy data and exception cases

The vendor responses should not all look the same. They should differ in pricing structure, completeness, scope coverage, timelines, assumptions, and response clarity.

The generated data should be good enough to test extraction and comparison agents.

The vendor data generation prompt must be included as part of the Prompt Pack.

## 9. Data Complexity Expectations

The generated vendor data should include multiple real-world complexity cases.

For example, the data may include:

- Missing or incomplete pricing
- Unclear commercial terms such as taxes, currency, assumptions, or exclusions
- Partial scope coverage, vague timelines, or weak compliance responses

The dataset should be complex enough to meaningfully test the extraction and comparison workflow.

Do not create clean or overly simplified vendor responses.

## 10. Part B: UI/UX Prompting

Use prompts to generate or guide the buyer-facing UI/UX.

The UI should help a buyer understand the RFQ, vendor responses, extracted information, missing details, risks, and key comparison points.

Your submission should include the prompts used for UI/UX generation.

These prompts may produce things like:

- Page or dashboard structure
- Comparison views
- Risk, evidence, or clarification sections

The focus is not visual polish alone. The UI should reflect good product thinking for a procurement buyer.

## 11. Part C: Vendor Response Upload or Input

The prototype should allow vendor responses to be uploaded, pasted, or otherwise provided as input.

You may support document formats such as PDF, PPT, Excel, Word, plain text, Markdown, JSON, or extracted text.

Full production-grade OCR or parsing is not mandatory.

However, the AI output should be generated dynamically from the input and should not be hardcoded.

## 12. Part D: Extraction Agent

Build an extraction agent that reads vendor responses and extracts useful procurement information.

The extraction should cover key areas such as:

- Scope, pricing, commercial terms, timeline, compliance, assumptions, exclusions, and risks
- Missing, unclear, conflicting, or unsupported information
- Evidence snippets from the vendor response

The extraction output should be structured and buyer-readable.

The agent should not hallucinate missing information. If information is missing, unclear, unsupported, or conflicting, it should be flagged clearly.

Your submission should include the prompts used for the extraction agent.

## 13. Part E: Comparison Agent

Build a comparison agent that compares vendors based on the extracted information.

The comparison should help the buyer understand differences across vendors.

It should cover key areas such as:

- Scope coverage, pricing clarity, commercial completeness, timeline clarity, and compliance quality
- Vendor experience, assumptions, exclusions, missing information, and risk level
- Buyer attention points and clarification needs

The comparison agent should focus on helping the buyer understand which vendors are comparable, which are not yet comparable, what information is missing, and where key differences exist.

The comparison should be grounded in extracted information and source evidence.

Your submission should include the prompts used for the comparison agent.

## 14. Product Thinking Expectations

We want to see how you think from a buyer's perspective.

Your prototype should show thoughtfulness around:

- What the buyer should see first
- How missing data, risks, uncertainty, and evidence should be surfaced
- How technical and commercial comparisons should be presented without misleading the buyer

Your write-up should briefly explain the product decisions you made.

## 15. Prompt Pack Requirement

Prompt writing is the core of this assignment.

Your submission must include the actual prompts used for:

1. RFQ generation
2. Vendor response generation
3. Complex/messy data generation
4. UI/UX generation
5. Extraction agent
6. Comparison agent
7. Clarification or exception handling

For each major prompt, briefly explain:

- What the prompt is meant to do
- Why you structured it that way
- How it handles unreliable, missing, or conflicting information

We want to see your prompt design choices, not just the final output.

## 16. Prompt Trace Requirement

Include at least one prompt trace from the workflow.

The trace should show:

- Input
- Prompt
- Model output
- Final displayed or structured output

The trace can be included in the app, README, notebook, logs, or write-up.

## 17. AI Reliability Expectations

The AI system should be designed to avoid hallucination and unsupported claims.

It should clearly identify when information is missing, unclear, conflicting, unsupported, not comparable, or requiring buyer review.

Important outputs should be supported by evidence from the vendor response wherever possible.

## 18. Suggested Prototype Flow

A good prototype may follow this flow:

1. Generate RFQ and vendor responses using prompts
2. Upload or input vendor responses
3. Run extraction on vendor responses
4. Show buyer-facing comparison, risks, evidence, clarification points, and prompt traces

You may change the flow if your approach is better.

## 19. Technology Guidance

You may use any technology stack.

Examples include Python, Node.js, Streamlit, FastAPI, React, Next.js, LangChain, LlamaIndex, OpenAI, Azure AI, Gemini, Claude, AWS Bedrock, Hugging Face, OCR tools, PDF parsers, spreadsheet parsers, or UI/code generation tools.

Choose the tools that best help you demonstrate the workflow.

## 20. Deliverables

You are expected to submit the assignment within **5 days** of receiving it.

### Required Deliverables

#### 1. Working Prototype

Submit a working prototype as a web app, local runnable app, Streamlit app, notebook prototype, or API-based prototype with instructions.

The prototype should process inputs dynamically.

#### 2. Generated Sample Data

Include:

- One generated RFQ
- At least 3 generated vendor responses
- Realistic complexity and exception cases

The data should be generated using prompts, not manually written as simple static examples.

#### 3. Prompt Pack

Include the prompts used for RFQ generation, vendor response generation, UI/UX generation, extraction, comparison, and exception handling.

#### 4. UI/UX Output

Include the UI/UX generated or guided by your prompts.

This may include screens, wireframes, component structure, frontend code, UX copy, dashboard layout, or screenshots.

#### 5. Extraction and Comparison Outputs

Include examples showing extracted information, missing or unclear fields, evidence snippets, vendor comparison, buyer attention points, and clarification questions.

#### 6. Prompt Trace

Include at least one complete prompt trace.

#### 7. Demo Video

Maximum duration: **5 minutes**.

The demo should explain the system flow, how prompts are used, how data is generated, how extraction and comparison work, and how messy or exceptional cases are handled.

#### 8. Short Write-Up

Length: **1–2 pages**.

Cover the problem solved, assumptions, prompt architecture, product thinking, UI/UX decisions, extraction approach, comparison approach, limitations, and what you would improve with more time.

#### 9. README

Include setup instructions, how to run the prototype, model/API requirements, environment variables, sample flow instructions, and assumptions.

## 21. Optional but Valuable

The following are optional but will strengthen the submission:

- Architecture diagram
- Prompt versioning or prompt evaluation notes
- Prompt failure examples and improvements
- More vendor responses or document formats
- OCR support
- Better UI polish
- Human review workflow
- Structured schemas
- Feedback loop design

## 22. Evaluation Rubric

| Evaluation Area | Weight |
|---|---|
| Prompt quality and prompt architecture | 30% |
| Realistic data generation quality | 20% |
| Extraction agent accuracy and reliability | 20% |
| Product thinking in vendor comparison | 15% |
| UI/UX prompt quality and buyer usability | 10% |
| Demo clarity and documentation | 5% |

## 23. What Strong Submissions Will Show

A strong submission will show:

- Well-structured prompts
- Realistic procurement data
- Useful UI/UX thinking
- Accurate extraction
- Evidence-backed outputs
- Clear handling of missing or conflicting information
- Buyer-friendly comparison
- No hallucinated commercial or technical claims
- Clear prompt traces

## 24. What to Avoid

Avoid:

- Hardcoded outputs
- Static dashboards
- Generic prompts
- Unrealistically clean test data
- Unsupported AI claims
- Heavy normalization work
- Ignoring missing or contradictory information
- Misleading vendor comparisons
- UI polish without strong AI behavior

## 25. Final Note

This assignment is intentionally open-ended.

There is no single correct answer.

We are looking for how you design a prompt-driven AI workflow for messy, real-world procurement data.

The best submissions will show how prompts can be used to generate realistic data, design useful UI, extract information accurately, and compare vendors in a way that helps buyers make sense of complex responses.
