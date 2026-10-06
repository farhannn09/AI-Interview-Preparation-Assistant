import os
from google import genai


def generate_interview_questions(job_role, skills, resume_text):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        return "Gemini API key is not configured."

    client = genai.Client(api_key=api_key)

    skills_text = ", ".join(skills)

    prompt = f"""
You are an expert technical interviewer conducting a real job interview.

Create exactly 5 interview questions for the candidate.

Candidate Information:

Job Role:
{job_role}

Candidate Skills:
{skills_text}

Resume:
{resume_text}

Interview Structure:

Question 1:
Ask a technical knowledge question related to the candidate's job role.

Question 2:
Ask a question related to a project or experience mentioned in the resume.

Question 3:
Ask a problem-solving question related to the candidate's technical skills.

Question 4:
Give a practical real-world scenario and ask how the candidate would solve it.

Question 5:
Ask an advanced job-role-specific question.

Requirements:

- Generate exactly 5 questions.
- Questions must be relevant to the selected job role.
- Use the candidate's actual skills where possible.
- Use information from the resume for project-based questions.
- Questions should be suitable for a technical interview.
- Do not provide answers.
- Do not provide explanations.
- Number questions exactly from 1 to 5.
- Keep each question clear and concise.

Return ONLY the five questions.
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        if not response.text:

            return "Unable to generate interview questions. Please try again."

        return response.text.strip()

    except Exception:

        return "Unable to generate interview questions right now. Please try again."