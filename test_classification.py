#!/usr/bin/env python3
"""
Test classification logic with sample job titles
"""

# Sample test cases
test_jobs = [
    "Masters Thesis opportunity working with the Rio Grande Cooter",
    "PhD Research Assistantship - Feral Swine Ecology and Management", 
    "Graduate Research Assistant--Bat Ecology and Conservation",
    "MS Graduate Assistantship – Deer population demographics",
    "PhD Graduate Research Assistantship: Virtual Fence – Range Cattle",
    "Assistant/Associate Professor in Wildlife Disease Epidemiology",
    "Program Technician - Forages",
    "Natural Resource Specialist 3",
    "Summer Avian Field Technician"
]

def test_classification(title):
    """Simple classification test"""
    
    # Graduate indicators
    graduate_indicators = [
        "graduate assistantship", "graduate assistant", "graduate student",
        "master's student", "ms student", "phd student", "doctoral student",
        "masters", "master's", "phd", "ph.d.", "doctorate", "doctoral",
        "assistantship", "fellowship", "graduate", "grad student",
        "thesis", "dissertation", "research assistant", "teaching assistant", 
        "graduate research", "graduate teaching", "stipend", "tuition waiver",
        "advisor", "adviser", "mentorship", "research project",
        "academic year", "semester", "graduate program", "grad program"
    ]
    
    # Non-graduate indicators
    non_graduate_indicators = [
        "professional position", "full-time employee", "staff position",
        "technician", "tech", "coordinator", "manager", "director", 
        "volunteer", "intern", "internship", "apprentice",
        "biologist", "hydrologist", "scientist", "botanist", "ecologist",
        "conservationist", "park ranger", "crew leader", "crew member",
        "habitat specialist", "regional coordinator", "liaison",
        "educator", "specialist", "officer", "program officer", "programme officer",
        "project manager", "production manager", "seasonal", 
        "human resource officer", "hr officer",
        "continuing education", "certification", "workshop", "training program",
        "degree program", "bachelor", "undergraduate", "post-doc", "postdoc",
        "visiting scholar", "faculty", "professor", "lecturer"
    ]
    
    full_text = title.lower()
    
    # Calculate scores
    grad_score = sum(1 for indicator in graduate_indicators if indicator in full_text)
    non_grad_score = sum(1 for indicator in non_graduate_indicators if indicator in full_text)
    
    # Check key terms
    key_graduate_terms = ["masters", "master's", "phd", "ph.d.", "assistantship", "fellowship"]
    has_key_graduate = any(term in full_text for term in key_graduate_terms)
    
    key_professional_terms = [
        "biologist", "hydrologist", "scientist", "botanist", "technician", 
        "park ranger", "specialist", "coordinator", "manager", "officer"
    ]
    has_key_professional = any(term in full_text for term in key_professional_terms)
    
    print(f"\nTitle: {title}")
    print(f"Graduate score: {grad_score}")
    print(f"Non-graduate score: {non_grad_score}")
    print(f"Has key graduate: {has_key_graduate}")
    print(f"Has key professional: {has_key_professional}")
    
    if has_key_graduate and not has_key_professional:
        result = "Graduate"
    elif has_key_professional and not has_key_graduate:
        result = "Professional" 
    elif grad_score > non_grad_score:
        result = "Graduate"
    else:
        result = "Professional"
        
    print(f"Classification: {result}")
    return result

if __name__ == "__main__":
    print("Testing classification logic...")
    
    for job_title in test_jobs:
        test_classification(job_title)
        
    print("\n" + "="*50)