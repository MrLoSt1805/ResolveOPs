
from pathlib import Path
import csv
import joblib

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODEL_FILE = ROOT / "ml" / "incident_classifier.joblib"

examples = {
    "Network": [
        "VPN is not connecting",
        "Corporate VPN connection failed",
        "Office wifi is disconnected",
        "Internet connection is very slow",
        "Cannot access company network",
        "Network connection keeps dropping",
        "Router is not working",
        "Unable to connect to wireless network",
        "Ethernet connection is unavailable",
        "VPN authentication connection timeout",
        "Office internet is down",
        "Cannot reach internal network server",
        "Wifi signal keeps disconnecting",
        "Network latency is extremely high",
        "VPN tunnel connection is failing",
        "Unable to access intranet over VPN",
    ],
    "Hardware": [
        "Laptop screen is broken",
        "Keyboard keys are not working",
        "Mouse is not responding",
        "Laptop battery is not charging",
        "Monitor display is flickering",
        "Printer hardware is jammed",
        "Computer fan is making noise",
        "Laptop power button is broken",
        "External hard drive is damaged",
        "Laptop overheating during use",
        "Monitor is not turning on",
        "USB port is physically damaged",
        "Desktop computer will not power on",
        "Laptop charger is not working",
        "Keyboard has stopped responding",
        "Printer paper feed is broken",
    ],
    "Software": [
        "Outlook application is crashing",
        "Microsoft Word is not opening",
        "Excel application freezes",
        "Software installation is failing",
        "Application shows unexpected error",
        "Browser crashes repeatedly",
        "Teams application is not responding",
        "PDF reader fails to open documents",
        "Office application keeps freezing",
        "Software update installation failed",
        "Outlook emails are not syncing",
        "Application closes unexpectedly",
        "Cannot launch accounting software",
        "Operating system update is stuck",
        "Video conferencing software crashes",
        "Installed application has stopped working",
    ],
    "Access": [
        "Forgot my account password",
        "Cannot login to employee portal",
        "My user account is locked",
        "Need access to shared folder",
        "Password reset is required",
        "Permission denied while opening folder",
        "Cannot sign into employee account",
        "Need permission for internal application",
        "Account credentials are not accepted",
        "Employee login has been disabled",
        "Unable to reset account password",
        "Access rights are missing",
        "My account has been suspended",
        "Need user access to finance portal",
        "Single sign on is failing",
        "Unable to authenticate employee account",
    ],
    "Security": [
        "Suspicious phishing email received",
        "Possible malware infection detected",
        "Company data may have been leaked",
        "Unauthorized login attempt detected",
        "Ransomware warning on laptop",
        "Suspicious attachment was opened",
        "Potential security breach reported",
        "Antivirus detected malicious software",
        "Confidential files were exposed",
        "Employee account may be compromised",
        "Unrecognized device accessed my account",
        "Possible credential theft detected",
        "Suspicious activity on company server",
        "Sensitive information was stolen",
        "Malicious link was clicked",
        "Unauthorized access to confidential data",
    ],
}

rows = [
    (text, category)
    for category, texts in examples.items()
    for text in texts
]

DATA_DIR.mkdir(exist_ok=True)

with open(
    DATA_DIR / "training_data.csv",
    "w",
    newline="",
    encoding="utf-8"
) as file:
    writer = csv.writer(file)
    writer.writerow(["text", "category"])
    writer.writerows(rows)

texts = [row[0] for row in rows]
labels = [row[1] for row in rows]

X_train, X_test, y_train, y_test = train_test_split(
    texts,
    labels,
    test_size=0.25,
    random_state=42,
    stratify=labels
)

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        sublinear_tf=True
    )),
    ("classifier", LogisticRegression(
        max_iter=2000,
        random_state=42
    ))
])

model.fit(X_train, y_train)

predictions = model.predict(X_test)

print("\nMODEL EVALUATION")
print("----------------")
print("Training examples:", len(X_train))
print("Testing examples:", len(X_test))
print("Accuracy:", round(
    accuracy_score(y_test, predictions), 4
))
print("\nClassification Report:")
print(classification_report(
    y_test,
    predictions,
    zero_division=0
))

# After evaluation, fit the final model on all examples.
model.fit(texts, labels)
joblib.dump(model, MODEL_FILE)

print("\nModel saved to:", MODEL_FILE)
