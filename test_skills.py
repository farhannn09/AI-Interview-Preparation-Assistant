from resume_parser import extract_skills


resume_text = """
Farhan Ahmad

Bachelor of Computer Applications

Skills:
Python
Java
SQL
MySQL
Machine Learning
Data Science
Pandas
NumPy
Flask
"""


skills = extract_skills(resume_text)

print("Detected Skills:")
print(skills)