import os
from google import genai


def evaluate_answer(question, answer, job_role):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        return {
            "technical_score": 0,
            "communication_score": 0,
            "feedback": "Gemini API key is not configured."
        }

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an expert technical interviewer.

Evaluate the candidate's answer for a {job_role} interview.

Interview Question:
{question}

Candidate Answer:
{answer}

Evaluation Criteria:

Technical Score (0-10):
- Technical correctness
- Understanding of the concept
- Relevance to the question
- Completeness
- Practical understanding

Communication Score (0-10):
- Clarity
- Structure
- Ability to explain the answer
- Conciseness
- Professional communication

Scoring Guide:

9-10 = Excellent
7-8 = Good
5-6 = Average
3-4 = Weak
0-2 = Very poor or incorrect

Important:
- Do not give a high score if the answer is technically incorrect.
- If the candidate gives a partially correct answer, give a partial score.
- If the answer is empty or irrelevant, give a low score.
- Evaluate only the answer provided by the candidate.

Return EXACTLY in this format:

Technical Score: X
Communication Score: X
Feedback: [2-4 sentences explaining what was good and what should be improved]

Do not add anything before or after this format.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        result = response.text.strip()

        technical_score = 0
        communication_score = 0
        feedback = result

        for line in result.splitlines():

            line = line.strip()

            if line.lower().startswith("technical score:"):

                technical_score = float(
                    line.split(":", 1)[1].strip()
                )

            elif line.lower().startswith("communication score:"):

                communication_score = float(
                    line.split(":", 1)[1].strip()
                )

            elif line.lower().startswith("feedback:"):

                feedback = line.split(":", 1)[1].strip()

        return {
            "technical_score": technical_score,
            "communication_score": communication_score,
            "feedback": feedback
        }

    except Exception as e:

        return {
            "technical_score": 0,
            "communication_score": 0,
            "feedback": f"Gemini Error: {e}"
        }