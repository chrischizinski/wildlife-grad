#!/usr/bin/env python3
"""
Improved graduate assistantship detection model using full description analysis.
"""

import json
import re
from typing import Dict, List, Tuple
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle


class ImprovedGraduateDetector:
    """Enhanced graduate assistantship detection using multiple signals."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.classifier = LogisticRegression(random_state=42)
        self.is_trained = False
        
        # Strong indicators for graduate assistantships
        self.strong_grad_indicators = [
            r'\b(ms|m\.s\.?|master\'?s?)\s+(student|position|assistantship|opportunity)',
            r'\b(phd|ph\.d\.?|doctoral)\s+(student|position|assistantship|opportunity)',
            r'\bgraduate\s+(research\s+)?(assistantship|position)',
            r'\bresearch\s+assistantship',
            r'\bgrad\s+(student|position)',
            r'\bthesis\s+(research|project|opportunity)',
            r'\bdissertation\s+(research|project)',
            r'\bgraduate\s+student\s+(position|opportunity)',
            r'\bgraduate\s+fellowship',
            r'\bteaching\s+assistantship'
        ]
        
        # Strong indicators against graduate assistantships
        self.strong_non_grad_indicators = [
            r'\b\d+\+?\s+years?\s+(of\s+)?experience',
            r'\bprofessional\s+experience',
            r'\bcareer\s+opportunity',
            r'\bfull-?time\s+(permanent|employee)',
            r'\bbenefits?\s+package',
            r'\bsalary\s+range',
            r'\b(manager|director|coordinator|supervisor)\b',
            r'\b(postdoc|post-?doctoral)',
            r'\bfaculty\s+position',
            r'\binstructor\s+position',
            r'\bprofessor\s+position',
            r'\btechnician\s+position',
            r'\bspecialist\s+position',
            r'\banalyst\s+position'
        ]
        
        # Reasonable salary ranges for graduate assistantships (annual, Lincoln-adjusted)
        self.min_reasonable_salary = 8000   # Very low but possible
        self.max_reasonable_salary = 60000  # High end for grad assistantships
    
    def extract_features(self, position: Dict) -> Dict:
        """Extract features for classification."""
        title = position.get('title', '').lower()
        description = position.get('description', '').lower()
        combined_text = f"{title} {description}"
        
        features = {}
        
        # Text-based features
        features['title_length'] = len(title)
        features['description_length'] = len(description)
        features['has_graduate_in_title'] = 'graduate' in title
        features['has_masters_in_title'] = any(x in title for x in ['master', 'ms', 'm.s'])
        features['has_phd_in_title'] = any(x in title for x in ['phd', 'ph.d', 'doctoral'])
        features['has_assistantship_in_title'] = 'assistantship' in title
        
        # Strong positive indicators
        features['strong_grad_score'] = sum(
            1 for pattern in self.strong_grad_indicators 
            if re.search(pattern, combined_text, re.IGNORECASE)
        )
        
        # Strong negative indicators  
        features['strong_non_grad_score'] = sum(
            1 for pattern in self.strong_non_grad_indicators
            if re.search(pattern, combined_text, re.IGNORECASE)
        )
        
        # Salary features
        salary = position.get('salary_lincoln_adjusted', 0)
        features['has_salary'] = salary > 0
        features['reasonable_salary'] = (
            self.min_reasonable_salary <= salary <= self.max_reasonable_salary
            if salary > 0 else False
        )
        features['very_low_salary'] = 0 < salary < self.min_reasonable_salary
        features['very_high_salary'] = salary > self.max_reasonable_salary
        
        return features
    
    def rule_based_classification(self, position: Dict) -> Tuple[bool, float, List[str]]:
        """
        Rule-based classification with confidence score and reasons.
        Returns: (is_graduate, confidence, reasons)
        """
        features = self.extract_features(position)
        reasons = []
        score = 0.5  # Start neutral
        
        # Strong positive indicators
        if features['strong_grad_score'] > 0:
            score += 0.3 * features['strong_grad_score']
            reasons.append(f"Strong graduate indicators: {features['strong_grad_score']}")
        
        # Strong negative indicators
        if features['strong_non_grad_score'] > 0:
            score -= 0.4 * features['strong_non_grad_score']
            reasons.append(f"Strong non-graduate indicators: {features['strong_non_grad_score']}")
        
        # Title-based indicators
        if features['has_assistantship_in_title']:
            score += 0.2
            reasons.append("Title contains 'assistantship'")
            
        if features['has_graduate_in_title']:
            score += 0.15
            reasons.append("Title contains 'graduate'")
            
        if features['has_masters_in_title'] or features['has_phd_in_title']:
            score += 0.1
            reasons.append("Title mentions degree level")
        
        # Salary-based indicators
        if features['very_high_salary']:
            score -= 0.3
            reasons.append("Salary too high for graduate assistantship")
        elif features['very_low_salary']:
            score -= 0.1
            reasons.append("Salary suspiciously low")
        elif features['reasonable_salary']:
            score += 0.1
            reasons.append("Salary in reasonable range")
        
        # Description length
        if features['description_length'] < 50:
            score -= 0.1
            reasons.append("Very short description")
        
        # Final classification
        is_graduate = score > 0.6
        confidence = min(max(score, 0.0), 1.0)
        
        return is_graduate, confidence, reasons
    
    def classify_position(self, position: Dict) -> Dict:
        """Classify a single position with detailed output."""
        is_graduate, confidence, reasons = self.rule_based_classification(position)
        
        # Determine review priority
        if confidence < 0.4 or confidence > 0.9:
            priority = "low"
        elif 0.4 <= confidence <= 0.6:
            priority = "high"  # Uncertain cases need review
        else:
            priority = "medium"
        
        return {
            'is_graduate': is_graduate,
            'confidence': confidence,
            'priority': priority,
            'reasons': reasons,
            'title': position.get('title', ''),
            'organization': position.get('organization', ''),
            'salary_original': position.get('salary', ''),
            'salary_adjusted': position.get('salary_lincoln_adjusted', 0),
            'url': position.get('url', '')
        }


def main():
    """Run the improved graduate detection analysis."""
    print("Loading position data...")
    
    # Load data
    dashboard_dir = Path("dashboard")
    with open(dashboard_dir / "export_data.json", 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} positions")
    
    # Initialize detector
    detector = ImprovedGraduateDetector()
    
    # Classify all positions
    print("Classifying positions...")
    results = []
    
    for pos in data:
        result = detector.classify_position(pos)
        results.append(result)
    
    # Analyze results
    graduate_positions = [r for r in results if r['is_graduate']]
    non_graduate_positions = [r for r in results if not r['is_graduate']]
    
    # Priority review cases
    high_priority = [r for r in results if r['priority'] == 'high']
    medium_priority = [r for r in results if r['priority'] == 'medium']
    
    print(f"\n=== CLASSIFICATION RESULTS ===")
    print(f"Total positions: {len(results)}")
    print(f"Classified as graduate: {len(graduate_positions)}")
    print(f"Classified as non-graduate: {len(non_graduate_positions)}")
    print(f"High priority review: {len(high_priority)}")
    print(f"Medium priority review: {len(medium_priority)}")
    
    # Show high priority review cases
    if high_priority:
        print(f"\n=== HIGH PRIORITY REVIEW CASES (confidence 0.4-0.6) ===")
        for i, result in enumerate(high_priority[:10], 1):
            print(f"\n{i}. {result['title']}")
            print(f"   Organization: {result['organization']}")
            print(f"   Salary: {result['salary_original']} → ${result['salary_adjusted']:,.0f}")
            print(f"   Confidence: {result['confidence']:.2f}")
            print(f"   Reasons: {'; '.join(result['reasons'])}")
    
    # Show graduate positions with salary data
    grad_with_salary = [r for r in graduate_positions if r['salary_adjusted'] > 0]
    
    if grad_with_salary:
        # Sort by salary
        grad_with_salary.sort(key=lambda x: x['salary_adjusted'])
        
        print(f"\n=== GRADUATE POSITIONS WITH SALARY ({len(grad_with_salary)}) ===")
        print(f"Salary range: ${grad_with_salary[0]['salary_adjusted']:,.0f} - ${grad_with_salary[-1]['salary_adjusted']:,.0f}")
        
        # Show potential outliers
        very_low = [r for r in grad_with_salary if r['salary_adjusted'] < 8000]
        very_high = [r for r in grad_with_salary if r['salary_adjusted'] > 60000]
        
        if very_low:
            print(f"\nVery low salaries ({len(very_low)}):")
            for r in very_low[:5]:
                print(f"  ${r['salary_adjusted']:6,.0f} - {r['title']}")
        
        if very_high:
            print(f"\nVery high salaries ({len(very_high)}):")
            for r in very_high[:5]:
                print(f"  ${r['salary_adjusted']:6,.0f} - {r['title']}")
    
    # Save results for review
    review_cases = high_priority + medium_priority
    if review_cases:
        output_file = Path("positions_for_review.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(review_cases, f, indent=2, ensure_ascii=False)
        print(f"\nPositions needing review saved to: {output_file}")
    
    # Save all results
    output_file = Path("classification_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"All classification results saved to: {output_file}")


if __name__ == "__main__":
    main()