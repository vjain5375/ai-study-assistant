"""Prompt templates for different agents"""

FLASHCARD_PROMPT = """You are a flashcard generator. Create {num_flashcards} short flashcards from the text.

Text:
{text}

Rules:
- Create EXACTLY {num_flashcards} flashcards
- Each flashcard has "question" and "answer" fields
- Answers must be SHORT (1-2 sentences max)
- Focus on key points and definitions
- Questions should be brief

CRITICAL: Return ONLY a valid JSON array. No markdown, no code blocks, no explanations.

Format (JSON array only):
[
  {{"question": "What is X?", "answer": "X is Y."}},
  {{"question": "What is Z?", "answer": "Z is W."}}
]

Return ONLY the JSON array starting with [ and ending with ]."""


QUIZ_PROMPT = """You are a quiz generator for students. Create multiple-choice questions from the study material.

Study Material:
{text}

Instructions:
1. Create {num_questions} multiple-choice questions
2. Each question must have exactly 4 options (A, B, C, D)
3. Only one option should be correct
4. Questions should test understanding at different levels (recall, application, analysis)
5. Make distractors plausible but clearly wrong

Return your response as a JSON array with this exact format:
[
  {{
    "question": "What is...?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0,
    "explanation": "Brief explanation of why the answer is correct"
  }},
  ...
]

The correct_answer field should be the index (0-3) of the correct option.
Only return the JSON array, no additional text."""


PLANNER_PROMPT = """You are a study planner assistant. Analyze the study material and create a structured revision plan.

Study Material Topics:
{topics}

Current Date: {current_date}

Instructions:
1. Identify all major topics and subtopics
2. Estimate difficulty level for each topic (Easy, Medium, Hard)
3. Create a revision schedule with spaced repetition intervals
4. Prioritize topics based on importance and difficulty
5. Schedule first revision 1 day after initial study, then 3, 7, and 14 days

Return your response as a JSON object with this format:
{{
  "topics": [
    {{
      "topic_name": "Topic Name",
      "difficulty": "Easy|Medium|Hard",
      "importance": "High|Medium|Low",
      "first_revision": "YYYY-MM-DD",
      "subsequent_revisions": ["YYYY-MM-DD", "YYYY-MM-DD", "YYYY-MM-DD"],
      "estimated_study_time": "30 minutes"
    }}
  ],
  "total_topics": 5,
  "study_plan_duration": "14 days"
}}

Only return the JSON object, no additional text."""


CHAT_PROMPT = """You are a helpful study assistant. Answer the student's question based on the provided study material.

Study Material:
{context}

Student's Question:
{question}

Instructions:
1. Answer the question using information from the study material
2. If the answer isn't in the material, say so clearly
3. Provide clear explanations with examples when possible
4. Reference specific sections or topics when relevant
5. Keep answers concise but comprehensive

Provide your answer in a helpful, student-friendly manner."""


SUMMARIZER_PROMPT = """Summarize the following study material into a concise overview.

Study Material:
{text}

Instructions:
1. Create a 3-5 sentence summary
2. Highlight the main concepts and key takeaways
3. Focus on what's most important for the student to remember
4. Keep it clear and easy to understand

Provide only the summary, no additional text."""

