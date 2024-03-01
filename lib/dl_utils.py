
import torch
from torch.utils.data import Dataset
from sklearn.metrics import f1_score, accuracy_score
import numpy as np

class CustomDataset(Dataset):
    def __init__(self, dataframe, tokenizer):
        self.data = dataframe
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        text = str(self.data.iloc[idx]['text'])
        label = int(self.data.iloc[idx]['label'])

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=512,
            return_tensors='pt',
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }
    
def compute_metrics(p):
    predictions, labels = p
    acc = accuracy_score(labels, list(np.argmax(predictions,axis=1)))
    f1_micro = f1_score(labels, list(np.argmax(predictions,axis=1)), average = 'micro')
    f1_macro = f1_score(labels, list(np.argmax(predictions,axis=1)), average = 'macro')
    f1_weighted = f1_score(labels, list(np.argmax(predictions,axis=1)), average = 'weighted')
    return {
        'acc': acc,
        'f1_micro': f1_micro,
        'f1_macro': f1_macro,
        'f1_weighted': f1_weighted
    }    