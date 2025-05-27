from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class ProcessingJob(models.Model):
    """Model to track document processing jobs"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    LANGUAGE_CHOICES = [
        ('auto', 'Auto Detect'),
        ('english', 'English'),
        ('bengali', 'Bengali'),
        ('bangla', 'Bangla'),
    ]
    
    QUESTION_TYPE_CHOICES = [
        ('SHORT', 'Short Answer'),
        ('MULTIPLECHOICE', 'Multiple Choice'),
    ]
    
    DOCUMENT_TYPE_CHOICES = [
        ('text_pdf', 'Text PDF'),
        ('image_pdf', 'Image PDF'),
        ('image', 'Image'),
        ('text', 'Raw Text'),
    ]
    
    # Basic fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='processing_jobs')
    document_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Processing parameters
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='auto')
    num_questions = models.PositiveIntegerField(null=True, blank=True, help_text="Number of questions to generate")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='MULTIPLECHOICE')
    
    # Document information
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, null=True, blank=True)
    is_question_paper = models.BooleanField(default=False)
    
    # File fields
    document_file = models.FileField(upload_to='brain/uploads/', null=True, blank=True)
    extracted_text_file = models.FileField(upload_to='brain/temp_extracts/', null=True, blank=True)
    output_file = models.FileField(upload_to='brain/qa_outputs/', null=True, blank=True)
    
    # Metadata
    processing_metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Processing Job'
        verbose_name_plural = 'Processing Jobs'
    
    def __str__(self):
        return f"{self.document_name} - {self.get_status_display()}"
    
    def mark_completed(self):
        """Mark the job as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message):
        """Mark the job as failed with error message"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
    
    def get_qa_pairs(self):
        """Get all question-answer pairs for this job"""
        return self.question_answers.all()


class QuestionAnswer(models.Model):
    """Model to store individual question-answer pairs"""
    
    QUESTION_TYPE_CHOICES = [
        ('SHORT', 'Short Answer'),
        ('MULTIPLECHOICE', 'Multiple Choice'),
    ]
    
    job = models.ForeignKey(ProcessingJob, on_delete=models.CASCADE, related_name='question_answers')
    question = models.TextField()
    answer = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    
    # For multiple choice questions
    options = models.JSONField(default=list, blank=True, help_text="List of options for multiple choice questions")
    correct_option = models.CharField(max_length=10, blank=True, help_text="Correct option label (A, B, C, D, etc.)")
    
    # Metadata
    confidence_score = models.FloatField(null=True, blank=True, help_text="AI confidence score for this Q&A pair")
    source_text = models.TextField(blank=True, help_text="Source text from which this question was generated")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Question Answer'
        verbose_name_plural = 'Question Answers'
    
    def __str__(self):
        return f"Q: {self.question[:50]}..."
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        data = {
            'question': self.question,
            'answer': self.answer,
            'question_type': self.question_type,
        }
        
        if self.question_type == 'MULTIPLECHOICE' and self.options:
            data['options'] = self.options
            data['correct_option'] = self.correct_option
        
        if self.confidence_score is not None:
            data['confidence_score'] = self.confidence_score
            
        return data
