"""
Medical data processing service for the Vaidya chatbot.
This module handles medical data analysis, symptom processing, drug interactions,
and medical entity extraction using NLP techniques.
"""

import re
import json
import spacy
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..core.config import settings
from ..utils.helpers import sanitize_input, extract_urgency_level


class UrgencyLevel(Enum):
    """Medical urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class SymptomCategory(Enum):
    """Medical symptom categories."""
    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    NEUROLOGICAL = "neurological"
    GASTROINTESTINAL = "gastrointestinal"
    MUSCULOSKELETAL = "musculoskeletal"
    DERMATOLOGICAL = "dermatological"
    PSYCHIATRIC = "psychiatric"
    INFECTIOUS = "infectious"
    ENDOCRINE = "endocrine"
    GENITOURINARY = "genitourinary"
    GENERAL = "general"


@dataclass
class MedicalEntity:
    """Represents a medical entity extracted from text."""
    text: str
    label: str
    confidence: float
    start_pos: int
    end_pos: int
    category: Optional[str] = None
    severity: Optional[str] = None
    temporal_info: Optional[str] = None


@dataclass
class SymptomAnalysis:
    """Comprehensive symptom analysis result."""
    symptoms: List[str]
    urgency_level: UrgencyLevel
    category: SymptomCategory
    severity_score: float
    duration_mentioned: bool
    temporal_patterns: List[str]
    associated_conditions: List[str]
    red_flags: List[str]
    recommendations: List[str]
    medical_entities: List[MedicalEntity]


@dataclass
class DrugInteraction:
    """Drug interaction information."""
    drug_a: str
    drug_b: str
    interaction_type: str
    severity: str
    description: str
    recommendations: List[str]
    clinical_significance: str


@dataclass
class MedicalDataAnalysis:
    """Complete medical data analysis result."""
    symptom_analysis: SymptomAnalysis
    drug_interactions: List[DrugInteraction]
    risk_factors: List[str]
    contraindications: List[str]
    follow_up_recommendations: List[str]
    confidence_score: float
    processing_time: float


class MedicalDataProcessor:
    """Advanced medical data processing service."""
    
    def __init__(self):
        """Initialize the medical data processor."""
        self.nlp = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._initialize_nlp()
        self._load_medical_knowledge()
    
    def _initialize_nlp(self):
        """Initialize spaCy NLP model."""
        try:
            # Try to load the medical NLP model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Initialized spaCy NLP model")
        except OSError:
            logger.warning("spaCy model not found. Some NLP features may be limited.")
            self.nlp = None
    
    def _load_medical_knowledge(self):
        """Load medical knowledge bases."""
        # Medical symptom patterns
        self.symptom_patterns = {
            SymptomCategory.CARDIOVASCULAR: [
                r"chest pain|heart attack|palpitations|shortness of breath|dizziness|fainting",
                r"high blood pressure|low blood pressure|irregular heartbeat|chest tightness"
            ],
            SymptomCategory.RESPIRATORY: [
                r"cough|wheeze|shortness of breath|difficulty breathing|chest congestion",
                r"asthma|bronchitis|pneumonia|sore throat|runny nose"
            ],
            SymptomCategory.NEUROLOGICAL: [
                r"headache|migraine|seizure|confusion|memory loss|tremor|weakness",
                r"stroke|dizziness|numbness|tingling|vision problems"
            ],
            SymptomCategory.GASTROINTESTINAL: [
                r"nausea|vomiting|diarrhea|constipation|stomach pain|heartburn",
                r"bloating|gas|loss of appetite|weight loss|blood in stool"
            ],
            SymptomCategory.MUSCULOSKELETAL: [
                r"joint pain|muscle pain|back pain|stiffness|swelling|arthritis",
                r"fracture|sprain|strain|weakness|limited mobility"
            ],
            SymptomCategory.DERMATOLOGICAL: [
                r"rash|itching|redness|swelling|skin lesion|moles|acne",
                r"eczema|psoriasis|hives|bruising|wound|burn"
            ],
            SymptomCategory.PSYCHIATRIC: [
                r"anxiety|depression|mood swings|panic attacks|insomnia|stress",
                r"hallucinations|delusions|suicidal thoughts|substance abuse"
            ],
            SymptomCategory.INFECTIOUS: [
                r"fever|chills|sweating|fatigue|malaise|body aches|infection",
                r"flu|cold|viral|bacterial|fungal|parasitic"
            ]
        }
        
        # Emergency red flags
        self.red_flags = [
            "chest pain", "difficulty breathing", "severe headache", "sudden weakness",
            "unconscious", "severe bleeding", "suicide", "overdose", "heart attack",
            "stroke", "severe allergic reaction", "choking", "severe burn"
        ]
        
        # Drug interaction database (simplified)
        self.drug_interactions = {
            ("warfarin", "aspirin"): {
                "severity": "major",
                "description": "Increased bleeding risk",
                "recommendations": ["Monitor INR closely", "Consider dose adjustment"]
            },
            ("metformin", "alcohol"): {
                "severity": "moderate",
                "description": "Increased risk of lactic acidosis",
                "recommendations": ["Limit alcohol consumption", "Monitor for symptoms"]
            }
        }
        
        # Medical abbreviations
        self.medical_abbreviations = {
            "bp": "blood pressure",
            "hr": "heart rate",
            "temp": "temperature",
            "rr": "respiratory rate",
            "o2": "oxygen",
            "dx": "diagnosis",
            "tx": "treatment",
            "hx": "history",
            "sx": "symptoms",
            "rx": "prescription"
        }
    
    async def process_medical_data(
        self,
        symptoms: str,
        medications: List[str] = None,
        medical_history: List[str] = None,
        user_context: Dict[str, Any] = None
    ) -> MedicalDataAnalysis:
        """
        Process comprehensive medical data analysis.
        
        Args:
            symptoms: User-reported symptoms
            medications: List of current medications
            medical_history: User's medical history
            user_context: Additional user context
            
        Returns:
            Complete medical data analysis
        """
        start_time = datetime.now()
        
        try:
            # Sanitize input
            clean_symptoms = sanitize_input(symptoms)
            
            # Expand abbreviations
            expanded_symptoms = self._expand_medical_abbreviations(clean_symptoms)
            
            # Process symptoms
            symptom_analysis = await self._analyze_symptoms(expanded_symptoms)
            
            # Check drug interactions
            drug_interactions = []
            if medications:
                drug_interactions = await self._check_drug_interactions(medications)
            
            # Assess risk factors
            risk_factors = self._assess_risk_factors(
                symptom_analysis, medical_history, user_context
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                symptom_analysis, drug_interactions, risk_factors
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                symptom_analysis, len(drug_interactions)
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return MedicalDataAnalysis(
                symptom_analysis=symptom_analysis,
                drug_interactions=drug_interactions,
                risk_factors=risk_factors,
                contraindications=self._identify_contraindications(medications),
                follow_up_recommendations=recommendations,
                confidence_score=confidence_score,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error processing medical data: {e}")
            raise
    
    async def _analyze_symptoms(self, symptoms: str) -> SymptomAnalysis:
        """
        Analyze symptoms using NLP and medical knowledge.
        
        Args:
            symptoms: Symptom description
            
        Returns:
            Symptom analysis result
        """
        # Extract medical entities
        medical_entities = await self._extract_medical_entities(symptoms)
        
        # Categorize symptoms
        category = self._categorize_symptoms(symptoms)
        
        # Extract urgency level
        urgency_level = UrgencyLevel(extract_urgency_level(symptoms))
        
        # Calculate severity score
        severity_score = self._calculate_severity_score(symptoms, medical_entities)
        
        # Identify temporal patterns
        temporal_patterns = self._extract_temporal_patterns(symptoms)
        
        # Find associated conditions
        associated_conditions = self._find_associated_conditions(symptoms, category)
        
        # Identify red flags
        red_flags = self._identify_red_flags(symptoms)
        
        # Generate recommendations
        recommendations = self._generate_symptom_recommendations(
            urgency_level, category, red_flags
        )
        
        return SymptomAnalysis(
            symptoms=self._extract_symptom_list(symptoms),
            urgency_level=urgency_level,
            category=category,
            severity_score=severity_score,
            duration_mentioned=self._check_duration_mentioned(symptoms),
            temporal_patterns=temporal_patterns,
            associated_conditions=associated_conditions,
            red_flags=red_flags,
            recommendations=recommendations,
            medical_entities=medical_entities
        )
    
    async def _extract_medical_entities(self, text: str) -> List[MedicalEntity]:
        """
        Extract medical entities from text using NLP.
        
        Args:
            text: Input text
            
        Returns:
            List of medical entities
        """
        entities = []
        
        if not self.nlp:
            # Fallback to rule-based extraction
            return self._rule_based_entity_extraction(text)
        
        # Use spaCy for entity extraction
        doc = self.nlp(text)
        
        for ent in doc.ents:
            # Check if entity is medically relevant
            if self._is_medical_entity(ent.label_):
                entities.append(MedicalEntity(
                    text=ent.text,
                    label=ent.label_,
                    confidence=0.8,  # Default confidence for spaCy entities
                    start_pos=ent.start_char,
                    end_pos=ent.end_char,
                    category=self._get_entity_category(ent.text),
                    severity=self._assess_entity_severity(ent.text)
                ))
        
        # Add custom medical entity extraction
        custom_entities = self._extract_custom_medical_entities(text)
        entities.extend(custom_entities)
        
        return entities
    
    def _rule_based_entity_extraction(self, text: str) -> List[MedicalEntity]:
        """
        Rule-based medical entity extraction fallback.
        
        Args:
            text: Input text
            
        Returns:
            List of medical entities
        """
        entities = []
        
        # Define medical entity patterns
        patterns = {
            "SYMPTOM": [
                r"pain|ache|soreness|discomfort|burning|stinging|throbbing",
                r"fever|chills|sweating|nausea|vomiting|diarrhea|constipation",
                r"headache|dizziness|fatigue|weakness|numbness|tingling",
                r"cough|wheeze|shortness of breath|chest tightness",
                r"rash|itching|swelling|redness|bruising"
            ],
            "BODY_PART": [
                r"head|neck|chest|back|stomach|abdomen|arm|leg|hand|foot",
                r"heart|lung|liver|kidney|brain|muscle|joint|skin|eye|ear"
            ],
            "DURATION": [
                r"minutes?|hours?|days?|weeks?|months?|years?",
                r"since|for|lasting|ongoing|persistent|chronic|acute"
            ],
            "SEVERITY": [
                r"mild|moderate|severe|excruciating|unbearable|slight",
                r"getting worse|improving|constant|intermittent"
            ]
        }
        
        for label, pattern_list in patterns.items():
            for pattern in pattern_list:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entities.append(MedicalEntity(
                        text=match.group(),
                        label=label,
                        confidence=0.7,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        category=self._get_entity_category(match.group())
                    ))
        
        return entities
    
    def _categorize_symptoms(self, symptoms: str) -> SymptomCategory:
        """
        Categorize symptoms into medical categories.
        
        Args:
            symptoms: Symptom description
            
        Returns:
            Symptom category
        """
        symptoms_lower = symptoms.lower()
        
        # Check each category
        for category, patterns in self.symptom_patterns.items():
            for pattern in patterns:
                if re.search(pattern, symptoms_lower):
                    return category
        
        return SymptomCategory.GENERAL
    
    def _calculate_severity_score(self, symptoms: str, entities: List[MedicalEntity]) -> float:
        """
        Calculate severity score based on symptoms and entities.
        
        Args:
            symptoms: Symptom description
            entities: Extracted medical entities
            
        Returns:
            Severity score (0.0 to 1.0)
        """
        score = 0.0
        
        # Base score from urgency level
        urgency = extract_urgency_level(symptoms)
        urgency_scores = {
            "low": 0.2,
            "medium": 0.4,
            "high": 0.7,
            "emergency": 1.0
        }
        score += urgency_scores.get(urgency, 0.2)
        
        # Adjust based on severity descriptors
        severity_keywords = {
            "mild": 0.1,
            "moderate": 0.3,
            "severe": 0.7,
            "excruciating": 0.9,
            "unbearable": 1.0
        }
        
        for keyword, value in severity_keywords.items():
            if keyword in symptoms.lower():
                score = max(score, value)
        
        # Consider number of symptoms
        symptom_count = len(self._extract_symptom_list(symptoms))
        score += min(symptom_count * 0.05, 0.2)
        
        # Red flags increase severity
        red_flag_count = sum(1 for flag in self.red_flags if flag in symptoms.lower())
        score += red_flag_count * 0.2
        
        return min(score, 1.0)
    
    def _extract_temporal_patterns(self, symptoms: str) -> List[str]:
        """
        Extract temporal patterns from symptoms.
        
        Args:
            symptoms: Symptom description
            
        Returns:
            List of temporal patterns
        """
        patterns = []
        
        temporal_keywords = {
            "acute": "sudden onset",
            "chronic": "long-term",
            "intermittent": "comes and goes",
            "persistent": "continuous",
            "recurring": "repeated episodes",
            "progressive": "worsening over time",
            "sudden": "acute onset",
            "gradual": "slow progression"
        }
        
        for keyword, pattern in temporal_keywords.items():
            if keyword in symptoms.lower():
                patterns.append(pattern)
        
        # Extract time durations
        duration_pattern = r"(\d+)\s*(minute|hour|day|week|month|year)s?"
        durations = re.findall(duration_pattern, symptoms, re.IGNORECASE)
        
        for duration, unit in durations:
            patterns.append(f"{duration} {unit}(s) duration")
        
        return patterns
    
    def _find_associated_conditions(self, symptoms: str, category: SymptomCategory) -> List[str]:
        """
        Find conditions associated with symptoms.
        
        Args:
            symptoms: Symptom description
            category: Symptom category
            
        Returns:
            List of associated conditions
        """
        conditions = []
        
        # Define condition associations
        condition_patterns = {
            "hypertension": ["high blood pressure", "headache", "dizziness"],
            "diabetes": ["frequent urination", "excessive thirst", "fatigue"],
            "migraine": ["severe headache", "nausea", "light sensitivity"],
            "asthma": ["wheezing", "shortness of breath", "chest tightness"],
            "arthritis": ["joint pain", "stiffness", "swelling"],
            "depression": ["sadness", "fatigue", "sleep problems"],
            "anxiety": ["worry", "panic", "rapid heartbeat"]
        }
        
        symptoms_lower = symptoms.lower()
        
        for condition, patterns in condition_patterns.items():
            if sum(1 for pattern in patterns if pattern in symptoms_lower) >= 2:
                conditions.append(condition)
        
        return conditions
    
    def _identify_red_flags(self, symptoms: str) -> List[str]:
        """
        Identify red flag symptoms requiring immediate attention.
        
        Args:
            symptoms: Symptom description
            
        Returns:
            List of red flags
        """
        identified_flags = []
        
        for flag in self.red_flags:
            if flag in symptoms.lower():
                identified_flags.append(flag)
        
        return identified_flags
    
    async def _check_drug_interactions(self, medications: List[str]) -> List[DrugInteraction]:
        """
        Check for drug interactions.
        
        Args:
            medications: List of medications
            
        Returns:
            List of drug interactions
        """
        interactions = []
        
        # Check all pairs of medications
        for i in range(len(medications)):
            for j in range(i + 1, len(medications)):
                drug_a = medications[i].lower()
                drug_b = medications[j].lower()
                
                # Check both orders
                for combo in [(drug_a, drug_b), (drug_b, drug_a)]:
                    if combo in self.drug_interactions:
                        interaction_data = self.drug_interactions[combo]
                        
                        interactions.append(DrugInteraction(
                            drug_a=drug_a,
                            drug_b=drug_b,
                            interaction_type="drug-drug",
                            severity=interaction_data["severity"],
                            description=interaction_data["description"],
                            recommendations=interaction_data["recommendations"],
                            clinical_significance="Monitor closely"
                        ))
        
        return interactions
    
    def _assess_risk_factors(
        self,
        symptom_analysis: SymptomAnalysis,
        medical_history: List[str] = None,
        user_context: Dict[str, Any] = None
    ) -> List[str]:
        """
        Assess risk factors based on symptoms and history.
        
        Args:
            symptom_analysis: Analyzed symptoms
            medical_history: Medical history
            user_context: User context
            
        Returns:
            List of risk factors
        """
        risk_factors = []
        
        # Age-based risk factors
        if user_context and "age" in user_context:
            age = user_context["age"]
            if age > 65:
                risk_factors.append("Advanced age")
            elif age < 18:
                risk_factors.append("Pediatric population")
        
        # Symptom-based risk factors
        if symptom_analysis.urgency_level == UrgencyLevel.HIGH:
            risk_factors.append("High urgency symptoms")
        
        if symptom_analysis.red_flags:
            risk_factors.append("Red flag symptoms present")
        
        # Medical history risk factors
        if medical_history:
            high_risk_conditions = [
                "diabetes", "hypertension", "heart disease", "stroke",
                "cancer", "kidney disease", "liver disease"
            ]
            
            for condition in high_risk_conditions:
                if any(condition in history.lower() for history in medical_history):
                    risk_factors.append(f"History of {condition}")
        
        return risk_factors
    
    def _generate_recommendations(
        self,
        symptom_analysis: SymptomAnalysis,
        drug_interactions: List[DrugInteraction],
        risk_factors: List[str]
    ) -> List[str]:
        """
        Generate follow-up recommendations.
        
        Args:
            symptom_analysis: Analyzed symptoms
            drug_interactions: Drug interactions
            risk_factors: Risk factors
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Urgency-based recommendations
        if symptom_analysis.urgency_level == UrgencyLevel.EMERGENCY:
            recommendations.append("Seek immediate emergency medical attention")
            recommendations.append("Call emergency services if symptoms worsen")
        elif symptom_analysis.urgency_level == UrgencyLevel.HIGH:
            recommendations.append("Consult healthcare provider within 24 hours")
            recommendations.append("Monitor symptoms closely")
        elif symptom_analysis.urgency_level == UrgencyLevel.MEDIUM:
            recommendations.append("Schedule appointment with healthcare provider")
            recommendations.append("Keep symptom diary")
        else:
            recommendations.append("Monitor symptoms and consult if they persist")
        
        # Drug interaction recommendations
        if drug_interactions:
            recommendations.append("Discuss medication interactions with pharmacist")
            recommendations.append("Review all medications with healthcare provider")
        
        # Risk factor recommendations
        if risk_factors:
            recommendations.append("Discuss risk factors with healthcare provider")
            recommendations.append("Consider preventive measures")
        
        # General recommendations
        recommendations.extend([
            "Follow up with healthcare provider as needed",
            "Maintain detailed symptom records",
            "Adhere to prescribed medications",
            "Practice healthy lifestyle habits"
        ])
        
        return recommendations
    
    def _generate_symptom_recommendations(
        self,
        urgency_level: UrgencyLevel,
        category: SymptomCategory,
        red_flags: List[str]
    ) -> List[str]:
        """
        Generate symptom-specific recommendations.
        
        Args:
            urgency_level: Urgency level
            category: Symptom category
            red_flags: Red flag symptoms
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Category-specific recommendations
        category_recommendations = {
            SymptomCategory.CARDIOVASCULAR: [
                "Monitor blood pressure regularly",
                "Avoid strenuous activity if chest pain",
                "Keep nitroglycerin available if prescribed"
            ],
            SymptomCategory.RESPIRATORY: [
                "Use inhaler as prescribed",
                "Avoid respiratory irritants",
                "Monitor oxygen levels if available"
            ],
            SymptomCategory.NEUROLOGICAL: [
                "Avoid driving if dizzy or confused",
                "Keep seizure medications available",
                "Monitor for changes in symptoms"
            ]
        }
        
        if category in category_recommendations:
            recommendations.extend(category_recommendations[category])
        
        # Red flag recommendations
        if red_flags:
            recommendations.append("Immediate medical attention required")
            recommendations.append("Do not delay seeking care")
        
        return recommendations
    
    def _calculate_confidence_score(
        self,
        symptom_analysis: SymptomAnalysis,
        interaction_count: int
    ) -> float:
        """
        Calculate confidence score for the analysis.
        
        Args:
            symptom_analysis: Analyzed symptoms
            interaction_count: Number of drug interactions
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 0.7  # Base confidence
        
        # Adjust based on entity count
        entity_count = len(symptom_analysis.medical_entities)
        score += min(entity_count * 0.05, 0.2)
        
        # Adjust based on temporal patterns
        if symptom_analysis.temporal_patterns:
            score += 0.1
        
        # Adjust based on red flags (more confident if present)
        if symptom_analysis.red_flags:
            score += 0.1
        
        # Adjust based on drug interactions
        if interaction_count > 0:
            score += 0.05
        
        return min(score, 1.0)
    
    def _expand_medical_abbreviations(self, text: str) -> str:
        """
        Expand medical abbreviations in text.
        
        Args:
            text: Input text
            
        Returns:
            Text with expanded abbreviations
        """
        expanded = text
        
        for abbrev, full_form in self.medical_abbreviations.items():
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            expanded = re.sub(pattern, full_form, expanded, flags=re.IGNORECASE)
        
        return expanded
    
    def _extract_symptom_list(self, symptoms: str) -> List[str]:
        """
        Extract list of individual symptoms.
        
        Args:
            symptoms: Symptom description
            
        Returns:
            List of symptoms
        """
        # Split by common separators
        symptom_list = re.split(r'[,;]+|and|also|plus', symptoms)
        
        # Clean and filter
        cleaned_symptoms = []
        for symptom in symptom_list:
            symptom = symptom.strip()
            if symptom and len(symptom) > 2:
                cleaned_symptoms.append(symptom)
        
        return cleaned_symptoms
    
    def _check_duration_mentioned(self, symptoms: str) -> bool:
        """
        Check if duration is mentioned in symptoms.
        
        Args:
            symptoms: Symptom description
            
        Returns:
            True if duration is mentioned
        """
        duration_patterns = [
            r'\d+\s*(minute|hour|day|week|month|year)s?',
            r'since|for|lasting|ongoing|chronic|acute'
        ]
        
        for pattern in duration_patterns:
            if re.search(pattern, symptoms, re.IGNORECASE):
                return True
        
        return False
    
    def _is_medical_entity(self, label: str) -> bool:
        """
        Check if an entity label is medically relevant.
        
        Args:
            label: Entity label
            
        Returns:
            True if medically relevant
        """
        medical_labels = {
            "PERSON", "ORG", "SYMPTOM", "DISEASE", "MEDICATION",
            "BODY_PART", "DURATION", "SEVERITY"
        }
        
        return label in medical_labels
    
    def _get_entity_category(self, entity_text: str) -> Optional[str]:
        """
        Get category for a medical entity.
        
        Args:
            entity_text: Entity text
            
        Returns:
            Entity category
        """
        # Simple categorization based on keywords
        categories = {
            "symptom": ["pain", "ache", "fever", "nausea", "cough"],
            "body_part": ["head", "chest", "back", "stomach", "arm", "leg"],
            "duration": ["minute", "hour", "day", "week", "month", "year"],
            "severity": ["mild", "moderate", "severe", "acute", "chronic"]
        }
        
        entity_lower = entity_text.lower()
        
        for category, keywords in categories.items():
            if any(keyword in entity_lower for keyword in keywords):
                return category
        
        return None
    
    def _assess_entity_severity(self, entity_text: str) -> Optional[str]:
        """
        Assess severity of a medical entity.
        
        Args:
            entity_text: Entity text
            
        Returns:
            Severity level
        """
        severity_keywords = {
            "mild": ["mild", "slight", "minor"],
            "moderate": ["moderate", "medium"],
            "severe": ["severe", "intense", "extreme", "excruciating"]
        }
        
        entity_lower = entity_text.lower()
        
        for severity, keywords in severity_keywords.items():
            if any(keyword in entity_lower for keyword in keywords):
                return severity
        
        return None
    
    def _extract_custom_medical_entities(self, text: str) -> List[MedicalEntity]:
        """
        Extract custom medical entities using rule-based patterns.
        
        Args:
            text: Input text
            
        Returns:
            List of custom medical entities
        """
        entities = []
        
        # Vital signs pattern
        vital_patterns = [
            (r"blood pressure.*?(\d+)/(\d+)", "VITAL_SIGNS"),
            (r"heart rate.*?(\d+)", "VITAL_SIGNS"),
            (r"temperature.*?(\d+\.?\d*)", "VITAL_SIGNS"),
            (r"weight.*?(\d+\.?\d*)", "VITAL_SIGNS")
        ]
        
        for pattern, label in vital_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(MedicalEntity(
                    text=match.group(),
                    label=label,
                    confidence=0.8,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    category="vital_signs"
                ))
        
        return entities
    
    def _identify_contraindications(self, medications: List[str] = None) -> List[str]:
        """
        Identify contraindications for medications.
        
        Args:
            medications: List of medications
            
        Returns:
            List of contraindications
        """
        contraindications = []
        
        if not medications:
            return contraindications
        
        # Simple contraindication rules
        contraindication_rules = {
            "warfarin": ["pregnancy", "severe liver disease", "active bleeding"],
            "aspirin": ["allergy to aspirin", "active bleeding", "severe asthma"],
            "metformin": ["kidney disease", "liver disease", "heart failure"]
        }
        
        for medication in medications:
            med_lower = medication.lower()
            for drug, contras in contraindication_rules.items():
                if drug in med_lower:
                    contraindications.extend(contras)
        
        return list(set(contraindications))


# Create service instance
medical_data_processor = MedicalDataProcessor()
