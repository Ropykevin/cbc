import re
from typing import Optional
from app.models.teacher import Teacher

def generate_teacher_code(full_name: str) -> str:
    """Generate a unique teacher code based on the teacher's name."""
    # Extract first name and clean it
    first_name = re.sub(r'[^a-zA-Z]', '', full_name.split()[0])
    base_code = first_name[:3].upper()
    
    # Find the next available number
    existing_codes = Teacher.query.filter(
        Teacher.teacher_code.like(f"{base_code}%")
    ).all()
    used_numbers = {int(code.teacher_code[3:]) for code in existing_codes 
                   if code.teacher_code[3:].isdigit()}
    
    # Find the first available number
    number = 1
    while number in used_numbers:
        number += 1
        
    return f"{base_code}{number:02d}"

def validate_teacher_code(code: str) -> bool:
    """Validate teacher code format."""
    pattern = r'^[A-Z]{3}\d{2}$'
    return bool(re.match(pattern, code))