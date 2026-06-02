"""Grade calculation helpers used by the Grade API."""


def calculate_grade(mark):
    """
    Convert a numeric mark (0-100) to a letter grade and GPA point.
    Raises ValueError for invalid input.
    """
    if not isinstance(mark, (int, float)):
        raise TypeError(f"Mark must be a number, got {type(mark).__name__}")
    if mark < 0 or mark > 100:
        raise ValueError(f"Mark must be between 0 and 100, got {mark}")

    if mark >= 85:
        return {
            'mark': mark,
            'grade': 'HD',
            'gpa': 4.0,
            'description': 'High Distinction',
        }
    if mark >= 75:
        return {'mark': mark, 'grade': 'D', 'gpa': 3.0, 'description': 'Distinction'}
    if mark >= 65:
        return {'mark': mark, 'grade': 'C', 'gpa': 2.0, 'description': 'Credit'}
    if mark >= 50:
        return {'mark': mark, 'grade': 'P', 'gpa': 1.0, 'description': 'Pass'}

    return {'mark': mark, 'grade': 'N', 'gpa': 0.0, 'description': 'Fail'}


def calculate_stats(marks):
    """
    Calculate basic statistics for a list of marks.
    Returns dict with average, highest, lowest, pass_rate.
    """
    if not marks:
        return {}

    valid = [m for m in marks if isinstance(m, (int, float)) and 0 <= m <= 100]
    if not valid:
        return {}

    average = sum(valid) / len(valid)
    passing = sum(1 for m in valid if m >= 50)

    return {
        'count': len(valid),
        'average': round(average, 2),
        'highest': max(valid),
        'lowest': min(valid),
        'pass_rate': round((passing / len(valid)) * 100, 1)
    }
