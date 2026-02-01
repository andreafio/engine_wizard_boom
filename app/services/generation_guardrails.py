"""Guardrails for generation output validation."""
import re
from typing import Dict, Any, List
from app.core.logging import get_logger

logger = get_logger(__name__)


def check_blueprint_has_metrics(blueprint_dict: Dict[str, Any]) -> bool:
    """Check if blueprint contains quantitative metrics/KPIs.
    
    Args:
        blueprint_dict: Blueprint data
        
    Returns:
        True if metrics found, False otherwise
    """
    # Check for common metric indicators
    metric_keywords = [
        'kpi', 'metric', 'cpl', 'cac', 'roi', 'conversion', 'ctr', 'cpc',
        'revenue', 'profit', 'target', 'goal', 'performance', '%', 'euro', '€'
    ]
    
    # Convert entire blueprint to lowercase string
    blueprint_str = str(blueprint_dict).lower()
    
    # Check for numeric values (potential metrics)
    has_numbers = bool(re.search(r'\d+', blueprint_str))
    
    # Check for metric keywords
    has_metric_keywords = any(keyword in blueprint_str for keyword in metric_keywords)
    
    return has_numbers and has_metric_keywords


def extract_invented_numbers(output: Dict[str, Any], blueprint_dict: Dict[str, Any]) -> List[str]:
    """Detect numbers in output that are not present in blueprint.
    
    Args:
        output: Generated output
        blueprint_dict: Source blueprint
        
    Returns:
        List of suspected invented numeric claims
    """
    invented_claims = []
    
    # Get all numbers from blueprint
    blueprint_str = str(blueprint_dict)
    blueprint_numbers = set(re.findall(r'\d+(?:[.,]\d+)?', blueprint_str))
    
    # Check slides for numbers
    for idx, slide in enumerate(output.get('slides', []), 1):
        for bullet_idx, bullet in enumerate(slide.get('bullets', []), 1):
            # Find numbers in bullet
            bullet_numbers = re.findall(r'\d+(?:[.,]\d+)?', bullet)
            
            for num in bullet_numbers:
                if num not in blueprint_numbers:
                    invented_claims.append(
                        f"Slide {idx}, bullet {bullet_idx}: contains number '{num}' not in blueprint - '{bullet}'"
                    )
    
    # Check report sections for numbers
    for section in output.get('report_sections', []):
        content = section.get('content', '')
        content_numbers = re.findall(r'\d+(?:[.,]\d+)?', content)
        
        for num in content_numbers:
            if num not in blueprint_numbers:
                invented_claims.append(
                    f"Report section '{section.get('title', 'Unknown')}': contains number '{num}' not in blueprint"
                )
    
    return invented_claims


def enforce_assumptions_when_no_metrics(
    output: Dict[str, Any],
    blueprint_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add mandatory assumption when blueprint lacks metrics.
    
    Args:
        output: Generated output
        blueprint_dict: Source blueprint
        
    Returns:
        Modified output with assumption added
    """
    if not check_blueprint_has_metrics(blueprint_dict):
        mandatory_assumption = (
            "Mancano dati quantitativi (CPL, CAC, conversioni, ROI): "
            "le priorità e raccomandazioni sono qualitative"
        )
        
        assumptions = output.get('assumptions', [])
        if mandatory_assumption not in assumptions:
            assumptions.insert(0, mandatory_assumption)
            output['assumptions'] = assumptions
            logger.info("assumption_added", reason="no_metrics_in_blueprint")
    
    return output


def move_invented_numbers_to_assumptions(
    output: Dict[str, Any],
    blueprint_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Move bullets with invented numbers to assumptions and remove from slides.
    
    Args:
        output: Generated output
        blueprint_dict: Source blueprint
        
    Returns:
        Cleaned output with invented numbers moved to assumptions
    """
    invented = extract_invented_numbers(output, blueprint_dict)
    
    if not invented:
        return output
    
    logger.warning("invented_numbers_detected", count=len(invented), details=invented[:3])
    
    # Add disclaimer to assumptions
    output.setdefault('assumptions', [])
    output['assumptions'].insert(0, 
        f"Attenzione: alcuni dati numerici sono stati rimossi perché non presenti nel blueprint confermato ({len(invented)} occorrenze)"
    )
    
    # Remove bullets containing numbers not in blueprint
    blueprint_numbers = set(re.findall(r'\d+(?:[.,]\d+)?', str(blueprint_dict)))
    
    for slide in output.get('slides', []):
        cleaned_bullets = []
        for bullet in slide.get('bullets', []):
            bullet_numbers = set(re.findall(r'\d+(?:[.,]\d+)?', bullet))
            # Keep bullet only if all its numbers are in blueprint (or it has no numbers)
            if not bullet_numbers or bullet_numbers.issubset(blueprint_numbers):
                cleaned_bullets.append(bullet)
            else:
                # Move to assumptions as hypothesis
                output['assumptions'].append(f"Ipotesi rimossa dalle slide: {bullet}")
        
        # Ensure at least 3 bullets remain
        if len(cleaned_bullets) >= 3:
            slide['bullets'] = cleaned_bullets
    
    return output


def apply_all_guardrails(
    output: Dict[str, Any],
    blueprint_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Apply all generation guardrails.
    
    Args:
        output: Generated output
        blueprint_dict: Source blueprint
        
    Returns:
        Validated and cleaned output
    """
    logger.info("applying_guardrails", blueprint_has_metrics=check_blueprint_has_metrics(blueprint_dict))
    
    # 1. Enforce assumptions when no metrics
    output = enforce_assumptions_when_no_metrics(output, blueprint_dict)
    
    # 2. Move invented numbers to assumptions
    output = move_invented_numbers_to_assumptions(output, blueprint_dict)
    
    return output
