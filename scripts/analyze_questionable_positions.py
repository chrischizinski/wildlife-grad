#!/usr/bin/env python3
"""
Analyze questionable positions to identify potential misclassifications
and positions with problematic salary data.
"""

import json
import pandas as pd
from pathlib import Path
import re


def load_data():
    """Load the export data for analysis."""
    dashboard_dir = Path("dashboard")
    with open(dashboard_dir / "export_data.json", 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_graduate_classifications(data):
    """Analyze positions classified as graduate assistantships."""
    graduate_positions = []
    questionable_positions = []
    
    for pos in data:
        # Check if tagged as graduate
        tags = pos.get('tags', '').lower()
        is_graduate = any(tag in tags for tag in ['graduate', 'grad', 'phd', 'master'])
        
        if is_graduate:
            title = pos.get('title', '').lower()
            description = pos.get('description', '').lower()
            salary = pos.get('salary_lincoln_adjusted', 0)
            
            # Flag questionable ones
            questionable_indicators = []
            
            # Check for problematic keywords in title
            non_grad_keywords = [
                'internship', 'intern', 'volunteer', 'temporary', 'seasonal',
                'contractor', 'consultant', 'manager', 'director', 'coordinator',
                'professor', 'faculty', 'instructor', 'postdoc', 'post-doc',
                'technician', 'specialist', 'analyst', 'staff'
            ]
            
            for keyword in non_grad_keywords:
                if keyword in title:
                    questionable_indicators.append(f"Title contains '{keyword}'")
            
            # Check salary issues
            if salary == 0:
                questionable_indicators.append("Zero salary")
            elif salary < 10000:
                questionable_indicators.append(f"Very low salary: ${salary:,.0f}")
            elif salary > 80000:
                questionable_indicators.append(f"Very high salary: ${salary:,.0f}")
            
            # Check for vague or short descriptions
            if len(description) < 100:
                questionable_indicators.append("Very short description")
            
            # Check for professional job indicators in description
            professional_indicators = [
                'years of experience', 'professional experience', 'career',
                'salary range', 'benefits package', 'full-time position',
                'permanent position', 'employment opportunity'
            ]
            
            for indicator in professional_indicators:
                if indicator in description:
                    questionable_indicators.append(f"Description contains '{indicator}'")
            
            position_info = {
                'title': pos.get('title', ''),
                'organization': pos.get('organization', ''),
                'location': pos.get('location', ''),
                'salary_original': pos.get('salary', ''),
                'salary_adjusted': salary,
                'discipline': pos.get('discipline_primary', ''),
                'tags': pos.get('tags', ''),
                'description_length': len(description),
                'questionable_indicators': questionable_indicators,
                'url': pos.get('url', '')
            }
            
            if questionable_indicators:
                questionable_positions.append(position_info)
            else:
                graduate_positions.append(position_info)
    
    return graduate_positions, questionable_positions


def analyze_salary_distribution(data):
    """Analyze the salary distribution of graduate positions."""
    graduate_salaries = []
    
    for pos in data:
        tags = pos.get('tags', '').lower()
        is_graduate = any(tag in tags for tag in ['graduate', 'grad', 'phd', 'master'])
        salary = pos.get('salary_lincoln_adjusted', 0)
        
        if is_graduate and salary > 0:
            graduate_salaries.append({
                'title': pos.get('title', ''),
                'salary': salary,
                'discipline': pos.get('discipline_primary', ''),
                'original_salary': pos.get('salary', '')
            })
    
    # Sort by salary
    graduate_salaries.sort(key=lambda x: x['salary'])
    
    return graduate_salaries


def main():
    print("Loading position data...")
    data = load_data()
    
    print(f"Total positions: {len(data)}")
    
    # Analyze graduate classifications
    print("\nAnalyzing graduate position classifications...")
    good_positions, questionable_positions = analyze_graduate_classifications(data)
    
    print(f"Good graduate positions: {len(good_positions)}")
    print(f"Questionable graduate positions: {len(questionable_positions)}")
    
    # Show questionable positions
    if questionable_positions:
        print(f"\n=== QUESTIONABLE GRADUATE POSITIONS ({len(questionable_positions)}) ===")
        for i, pos in enumerate(questionable_positions[:20], 1):  # Show first 20
            print(f"\n{i}. {pos['title']}")
            print(f"   Organization: {pos['organization']}")
            print(f"   Location: {pos['location']}")
            print(f"   Salary: {pos['salary_original']} → ${pos['salary_adjusted']:,.0f}")
            print(f"   Discipline: {pos['discipline']}")
            print(f"   Issues: {', '.join(pos['questionable_indicators'])}")
            if pos['url']:
                print(f"   URL: {pos['url']}")
    
    # Analyze salary distribution
    print("\n\nAnalyzing salary distribution...")
    salaries = analyze_salary_distribution(data)
    
    if salaries:
        print(f"\nGraduate positions with salary data: {len(salaries)}")
        print(f"Lowest salary: ${salaries[0]['salary']:,.0f} - {salaries[0]['title']}")
        print(f"Highest salary: ${salaries[-1]['salary']:,.0f} - {salaries[-1]['title']}")
        
        # Show lowest 10 salaries
        print(f"\n=== LOWEST 10 SALARIES ===")
        for i, pos in enumerate(salaries[:10], 1):
            print(f"{i:2d}. ${pos['salary']:6,.0f} - {pos['title']} ({pos['discipline']})")
        
        # Show highest 10 salaries  
        print(f"\n=== HIGHEST 10 SALARIES ===")
        for i, pos in enumerate(salaries[-10:], len(salaries)-9):
            print(f"{i:2d}. ${pos['salary']:6,.0f} - {pos['title']} ({pos['discipline']})")
    
    # Save questionable positions for review
    if questionable_positions:
        output_file = Path("questionable_positions.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(questionable_positions, f, indent=2, ensure_ascii=False)
        print(f"\nQuestionable positions saved to: {output_file}")
    
    print("\n=== SUMMARY ===")
    print(f"Total positions: {len(data)}")
    print(f"Good graduate positions: {len(good_positions)}")
    print(f"Questionable graduate positions: {len(questionable_positions)}")
    print(f"Graduate positions with salary data: {len(salaries) if salaries else 0}")
    
    if questionable_positions:
        print(f"\nRecommendation: Review the {len(questionable_positions)} questionable positions")
        print("to improve the graduate detection model.")


if __name__ == "__main__":
    main()