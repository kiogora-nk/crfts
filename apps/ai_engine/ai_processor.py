import re
import hashlib
from collections import Counter
from datetime import timedelta
from django.utils import timezone

class AIProcessor:
    KEYWORDS = {
        'URGENT': ['urgent','immediate','asap','critical','emergency','deadline'],
        'FINANCE': ['budget','invoice','payment','financial','accounting','expenditure','revenue','tax','audit'],
        'LEGAL': ['legal','court','law','attorney','compliance','regulation','contract','liability'],
        'HR': ['employee','staff','recruitment','salary','leave','promotion','termination','benefits'],
        'PROCUREMENT': ['tender','bid','procurement','supplier','purchase','vendor','quotation'],
        'TECHNICAL': ['system','software','hardware','network','database','server','security'],
    }
    
    @classmethod
    def classify_document(cls, text):
        if not text: return 'GENERAL', 0.0
        text = text.lower()
        scores = {}
        for category, keywords in cls.KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            scores[category] = score
        if max(scores.values()) == 0: return 'GENERAL', 0.0
        best = max(scores, key=scores.get)
        confidence = scores[best] / len(cls.KEYWORDS[best])
        return best, min(confidence, 1.0)
    
    @classmethod
    def extract_keywords(cls, text, top_n=10):
        if not text: return []
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        stopwords = {'this','that','with','from','have','been','were','they','their','will','would','could','should','about','which','there'}
        filtered = [w for w in words if w not in stopwords]
        return [word for word, count in Counter(filtered).most_common(top_n)]
    
    @classmethod
    def generate_summary(cls, text, max_sentences=3):
        if not text: return ''
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        if not sentences: return text[:200] + '...'
        return '. '.join(sentences[:max_sentences]) + '.'
    
    @classmethod
    def analyze_sentiment(cls, text):
        if not text: return 'NEUTRAL'
        positive = ['approve','approved','complete','success','good','excellent','positive']
        negative = ['reject','rejected','fail','failed','poor','bad','negative','complaint','issue','problem','delay']
        text_lower = text.lower()
        pos_score = sum(1 for w in positive if w in text_lower)
        neg_score = sum(1 for w in negative if w in text_lower)
        if pos_score > neg_score: return 'POSITIVE'
        elif neg_score > pos_score: return 'NEGATIVE'
        return 'NEUTRAL'
    
    @classmethod
    def suggest_priority(cls, text, department):
        if not text: return 'MEDIUM'
        text_lower = text.lower()
        urgent = ['urgent','immediate','asap','critical','emergency']
        high = ['important','priority','deadline','required','necessary']
        if any(kw in text_lower for kw in urgent): return 'URGENT'
        if any(kw in text_lower for kw in high): return 'HIGH'
        return 'MEDIUM'
    
    @classmethod
    def compute_file_hash(cls, file_path):
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except: return None
    
    @classmethod
    def detect_anomalies(cls, file_obj):
        anomalies = []
        if file_obj.days_held > 30:
            anomalies.append({'type': 'LONG_HOLD', 'desc': f'File held for {file_obj.days_held} days', 'risk': min(file_obj.days_held / 30 * 0.5, 1.0)})
        movements = file_obj.movements.count()
        if movements > 20:
            anomalies.append({'type': 'EXCESSIVE_MOVEMENT', 'desc': f'File moved {movements} times', 'risk': min(movements / 20 * 0.3, 0.8)})
        recent = file_obj.transfers.filter(transferred_at__gte=timezone.now()-timedelta(hours=24)).count()
        if recent > 5:
            anomalies.append({'type': 'RAPID_TRANSFERS', 'desc': f'{recent} transfers in 24 hours', 'risk': min(recent / 5 * 0.6, 1.0)})
        return anomalies
    
    @classmethod
    def search_relevant(cls, query, files_queryset):
        if not query: return files_queryset
        query_lower = query.lower()
        scored = []
        for f in files_queryset:
            score = 0
            if query_lower in f.file_number.lower(): score += 10
            if query_lower in f.subject.lower(): score += 8
            if f.description and query_lower in f.description.lower(): score += 5
            if score > 0: scored.append((f, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [f for f, s in scored]
