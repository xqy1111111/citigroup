import pandas as pd
import numpy as np
import joblib
pd.options.display.max_columns = None
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, log_loss
from sklearn.ensemble import AdaBoostClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

path = r'PS_20174392719_1491204439457_log.csv'

df = pd.read_csv(path,encoding='utf-8')
df=df[['type','amount','oldbalanceOrg','newbalanceOrig','isFraud']]
df = df[np.isclose(df['amount'], abs(df['oldbalanceOrg'] - df['newbalanceOrig']), atol=1)]
df.to_csv("updatedData1.csv", index=False,encoding='utf-8')  # 保存为 CSV 文件
df = pd.read_csv('updatedData1.csv',encoding='utf-8')
encoded_df = pd.get_dummies(df,columns=['type'])
#print(encoded_df)
X = encoded_df.drop(columns=['isFraud'])  # 替换为目标变量的实际列名
y = encoded_df['isFraud']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
ada_model = AdaBoostClassifier(n_estimators=100,learning_rate=1.0,random_state=42,algorithm='SAMME')
ada_model.fit(X_train, y_train)
joblib.dump(ada_model,'adaboost_model.joblib')

print("Test:")
y_pred = ada_model.predict(X_test)
y_pred_proba = ada_model.predict_proba(X_test)[:, 1]
print(y_pred_proba)
roc_auc = roc_auc_score(y_test, y_pred_proba)
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
roc_auc = roc_auc_score(y_test, y_pred_proba)
logloss = log_loss(y_test, y_pred_proba)
conf_matrix = confusion_matrix(y_test, y_pred)
print(f"Accuracy: {accuracy:.10f}")
print(f"Precision: {precision:.10f}")
print(f"Recall: {recall:.10f}")
print(f"F1 Score: {f1:.10f}")
print(f"ROC AUC: {roc_auc:.10f}")
print(f"Log Loss: {logloss:.10f}")
print("Confusion Matrix:")
print(conf_matrix)
print("Train:")
y_pred = ada_model.predict(X_train)
y_pred_proba = ada_model.predict_proba(X_train)[:, 1]
print(y_pred_proba)
roc_auc = roc_auc_score(y_train, y_pred_proba)
accuracy = accuracy_score(y_train, y_pred)
precision = precision_score(y_train, y_pred)
recall = recall_score(y_train, y_pred)
f1 = f1_score(y_train, y_pred)
roc_auc = roc_auc_score(y_train, y_pred_proba)
logloss = log_loss(y_train, y_pred_proba)
conf_matrix = confusion_matrix(y_train, y_pred)
print(f"Accuracy: {accuracy:.10f}")
print(f"Precision: {precision:.10f}")
print(f"Recall: {recall:.10f}")
print(f"F1 Score: {f1:.10f}")
print(f"ROC AUC: {roc_auc:.10f}")
print(f"Log Loss: {logloss:.10f}")
print("Confusion Matrix:")
print(conf_matrix)
