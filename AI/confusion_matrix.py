import json
import os
from sklearn.metrics import confusion_matrix, classification_report
import seaborn as sns
import matplotlib.pyplot as plt

# Path to the folder with data (adjust if different)
path = "MelanoScan-3"
annotations_path = os.path.join(path, "valid", "_annotations.coco.json")

# Load COCO annotation file
with open(annotations_path, 'r') as f:
    data = json.load(f)

# Mapping from category_id -> class name (all lowercase)
id_to_name = {cat['id']: cat['name'].lower() for cat in data['categories']}

# Extract true labels from annotations
true_labels_ids = [ann['category_id'] for ann in data['annotations']]
true_labels = [id_to_name[cat_id] for cat_id in true_labels_ids]

# Insert your model predictions here (currently assuming perfect match)
pred_labels = true_labels.copy()

# List of classes (all lowercase)
labels = ['melanoma', 'nevus', 'keratosis']

# Filter only those labels that are in the labels list
true_labels_filtered = [label for label in true_labels if label in labels]
pred_labels_filtered = [label for label in pred_labels if label in labels]

# Generate confusion matrix
cm = confusion_matrix(true_labels_filtered, pred_labels_filtered, labels=labels)

# Visualize confusion matrix
plt.figure(figsize=(8,6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
plt.xlabel('Predicted label')
plt.ylabel('True label')
plt.title('Confusion Matrix')
plt.show()

# Generate classification report
report = classification_report(true_labels_filtered, pred_labels_filtered, labels=labels, target_names=labels)
print("Classification Report:")
print(report)