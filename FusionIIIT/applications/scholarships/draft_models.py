"""
Django model for storing scholarship application drafts.
Allows students to save incomplete form data and resume later.
"""
import datetime
from django.db import models
from applications.academic_information.models import Student

class ScholarshipFormDraft(models.Model):
    """
    Model to store draft scholarship applications for various award types.
    Allows students to save form progress and resume at any time.
    """
    DRAFT_TYPE_CHOICES = (
        ('MCM', 'Merit-cum-Means Scholarship'),
        ('GOLD', "Director's Gold Medal"),
        ('SILVER', "Director's Silver Medal"),
        ('DM', 'D&M Proficiency Gold Medal'),
        ('PREVIOUS_WINNER', 'Previous Winner'),
    )
    
    # Basic information
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='scholarship_drafts',
        help_text="Student who created this draft"
    )
    draft_type = models.CharField(
        max_length=20, 
        choices=DRAFT_TYPE_CHOICES,
        help_text="Type of scholarship application"
    )
    
    # Form data stored as JSON to support any field combination
    form_data = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Complete form data stored as JSON"
    )
    
    # Uploaded files metadata
    uploaded_files = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Metadata of uploaded files (filename, file_path)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the draft was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the draft was last updated"
    )
    last_accessed = models.DateTimeField(
        auto_now=True,
        help_text="When the draft was last accessed by student"
    )
    
    # Draft metadata
    auto_saved = models.BooleanField(
        default=False,
        help_text="Whether this was auto-saved (vs manually saved)"
    )
    completion_percentage = models.IntegerField(
        default=0,
        help_text="Estimated completion percentage (0-100)"
    )
    
    # Timeout/interruption tracking
    interrupted = models.BooleanField(
        default=False,
        help_text="Whether draft was saved due to timeout/interruption"
    )
    interruption_reason = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        choices=[
            ('timeout', 'Session Timeout'),
            ('inactivity', 'User Inactivity'),
            ('network_error', 'Network Error'),
            ('manual_save', 'Manual Save'),
            ('browser_close', 'Browser Close'),
        ],
        help_text="Reason why draft was saved"
    )
    
    # Additional metadata
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Optional notes from student"
    )
    ip_address = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="IP address where draft was saved"
    )
    
    class Meta:
        db_table = 'ScholarshipFormDraft'
        verbose_name = 'Scholarship Form Draft'
        verbose_name_plural = 'Scholarship Form Drafts'
        ordering = ['-updated_at']
        # Only one draft per student per application type at a time
        unique_together = [['student', 'draft_type']]
        
    def __str__(self):
        return f"{self.student} - {self.get_draft_type_display()} (Draft)"
    
    def get_summary(self):
        """Return a summary of the draft for display"""
        return {
            'id': self.id,
            'student': str(self.student),
            'type': self.draft_type,
            'completion': self.completion_percentage,
            'created': self.created_at,
            'updated': self.updated_at,
            'fields_count': len(self.form_data) if self.form_data else 0,
            'files_count': len(self.uploaded_files) if self.uploaded_files else 0,
        }
    
    def mark_interrupted(self, reason='timeout', ip_address=None):
        """Mark this draft as having been saved due to interruption"""
        self.interrupted = True
        self.interruption_reason = reason
        if ip_address:
            self.ip_address = ip_address
        self.auto_saved = True
        self.save()


class DraftSaveLog(models.Model):
    """
    Log entries for when drafts are saved (for audit and debugging).
    Helps track when students are losing connection or experiencing issues.
    """
    draft = models.ForeignKey(
        ScholarshipFormDraft,
        on_delete=models.CASCADE,
        related_name='save_logs'
    )
    saved_at = models.DateTimeField(auto_now_add=True)
    save_reason = models.CharField(
        max_length=100,
        choices=[
            ('auto_save', 'Auto-save (interval-based)'),
            ('field_change', 'Field value changed'),
            ('form_incomplete', 'Form incomplete - timeout warning'),
            ('session_timeout', 'Session about to timeout'),
            ('network_error', 'Network error detected'),
            ('manual_save', 'Manual save by student'),
            ('browser_close', 'Browser about to close'),
            ('inactivity', 'Inactivity detected'),
        ]
    )
    fields_updated = models.JSONField(
        default=list,
        help_text="List of fields that were updated in this save"
    )
    
    class Meta:
        db_table = 'DraftSaveLog'
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"Draft #{self.draft.id} saved on {self.saved_at}"
