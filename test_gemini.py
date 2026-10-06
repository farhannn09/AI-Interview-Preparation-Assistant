from question_generator import generate_interview_questions


job_role = "Data Scientist"

skills = [
    "Python",
    "SQL",
    "Machine Learning",
    "Pandas",
    "NumPy"
]

resume_text = """
Bachelor of Computer Applications.
Skills include Python, SQL, Machine Learning,
Pandas and NumPy.
Worked on data analysis and machine learning projects.
"""


questions = generate_interview_questions(
    job_role,
    skills,
    resume_text
)

print("\nGenerated Interview Questions:\n")
print(questions)