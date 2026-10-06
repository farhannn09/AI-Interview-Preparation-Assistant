from answer_evaluator import evaluate_answer


question = """
What is the difference between supervised and unsupervised
machine learning?
"""

answer = """
Supervised learning uses labelled data to train a model.
For example, we can use labelled data to predict house prices.
Unsupervised learning uses data without labels and tries to
find patterns or groups in the data.
"""

job_role = "Data Scientist"


result = evaluate_answer(
    question,
    answer,
    job_role
)


print("\nAI Evaluation Result:\n")

print("Technical Score:", result["technical_score"])
print("Communication Score:", result["communication_score"])
print("Feedback:", result["feedback"])