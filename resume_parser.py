import pdfplumber
import re


def extract_text_from_pdf(pdf_path):

    text = ""

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text


def extract_skills(text):

    skills_list = [
        "Python",
        "Java",
        "C",
        "C++",
        "C#",
        "SQL",
        "MySQL",
        "MongoDB",
        "HTML",
        "CSS",
        "JavaScript",
        "Flask",
        "Django",
        "React",
        "Node.js",
        "Pandas",
        "NumPy",
        "Scikit-learn",
        "TensorFlow",
        "PyTorch",
        "Machine Learning",
        "Deep Learning",
        "Artificial Intelligence",
        "Data Science",
        "Data Analysis",
        "Big Data",
        "Hadoop",
        "Spark",
        "Git",
        "GitHub",
        "Docker",
        "AWS",
        "Power BI",
        "Tableau"
    ]

    detected_skills = []

    text_lower = text.lower()

    for skill in skills_list:

        if skill.lower() in text_lower:

            if skill not in detected_skills:
                detected_skills.append(skill)

    return detected_skills

    text_lower = text.lower()

    for skill in skills_list:

        if skill.lower() in text_lower:

            detected_skills.append(skill)

    return detected_skills