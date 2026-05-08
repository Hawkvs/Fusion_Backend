"""
API views for scholarship application draft management.
Handles saving, loading, updating, and deleting drafts.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from .draft_models import ScholarshipFormDraft, DraftSaveLog
from rest_framework import serializers


class DraftSaveLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DraftSaveLog
        fields = ['saved_at', 'save_reason', 'fields_updated']
        read_only_fields = ['saved_at']


class ScholarshipFormDraftSerializer(serializers.ModelSerializer):
    save_logs = DraftSaveLogSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source='student.id.user.get_full_name', read_only=True)
    
    class Meta:
        model = ScholarshipFormDraft
        fields = [
            'id', 'draft_type', 'form_data', 'uploaded_files', 
            'completion_percentage', 'created_at', 'updated_at', 
            'last_accessed', 'interrupted', 'interruption_reason',
            'save_logs', 'student_name', 'notes'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_accessed']


class ScholarshipDraftViewSet(viewsets.ModelViewSet):
    """
    API endpoints for managing scholarship application drafts.
    
    Features:
    - Save draft: Store incomplete form data
    - Load draft: Retrieve saved draft for continuation
    - Auto-save: Periodic automatic saving of form progress
    - List drafts: View all saved drafts for a student
    - Delete draft: Remove saved draft
    """
    serializer_class = ScholarshipFormDraftSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return drafts only for the authenticated student"""
        student = self.request.user.extrainfo.student
        return ScholarshipFormDraft.objects.filter(student=student)
    
    @action(detail=False, methods=['post'])
    def save_draft(self, request):
        """
        Save or update a scholarship application draft.
        
        Expected request body:
        {
            "draft_type": "MCM",  # MCM, GOLD, SILVER, DM, PREVIOUS_WINNER
            "form_data": {...},   # All form fields
            "uploaded_files": {...},  # File metadata
            "completion_percentage": 45,
            "notes": "Optional notes"
        }
        """
        try:
            draft_type = request.data.get('draft_type')
            form_data = request.data.get('form_data', {})
            uploaded_files = request.data.get('uploaded_files', {})
            completion_pct = request.data.get('completion_percentage', 0)
            notes = request.data.get('notes', '')
            interrupted = request.data.get('interrupted', False)
            reason = request.data.get('interruption_reason', 'manual_save')
            
            student = request.user.extrainfo.student
            
            # Get or create draft
            draft, created = ScholarshipFormDraft.objects.get_or_create(
                student=student,
                draft_type=draft_type
            )
            
            # Update draft fields
            draft.form_data = form_data
            draft.uploaded_files = uploaded_files
            draft.completion_percentage = completion_pct
            draft.notes = notes
            
            if interrupted:
                draft.mark_interrupted(reason, self.get_client_ip(request))
            else:
                draft.auto_saved = False
                draft.interrupted = False
            
            draft.save()
            
            # Log the save
            DraftSaveLog.objects.create(
                draft=draft,
                save_reason=reason if interrupted else 'manual_save',
                fields_updated=list(form_data.keys())
            )
            
            return Response({
                'success': True,
                'message': f"Draft {'created' if created else 'updated'} successfully",
                'draft_id': draft.id,
                'draft_type': draft_type,
                'completion_percentage': draft.completion_percentage,
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def auto_save(self, request):
        """
        Auto-save draft at periodic intervals (every 30 seconds recommended).
        Lightweight endpoint for frequent updates.
        """
        try:
            draft_type = request.data.get('draft_type')
            form_data = request.data.get('form_data', {})
            completion_pct = request.data.get('completion_percentage', 0)
            
            student = request.user.extrainfo.student
            
            draft, _ = ScholarshipFormDraft.objects.get_or_create(
                student=student,
                draft_type=draft_type
            )
            
            # Only update if data has changed
            if draft.form_data != form_data:
                draft.form_data = form_data
                draft.completion_percentage = completion_pct
                draft.auto_saved = True
                draft.save(update_fields=['form_data', 'completion_percentage', 'auto_saved', 'updated_at', 'last_accessed'])
                
                # Log auto-save
                DraftSaveLog.objects.create(
                    draft=draft,
                    save_reason='auto_save',
                    fields_updated=list(form_data.keys())
                )
                
                return Response({
                    'success': True,
                    'message': 'Auto-save completed',
                    'draft_id': draft.id,
                }, status=status.HTTP_200_OK)
            
            # No changes needed
            draft.last_accessed = timezone.now()
            draft.save(update_fields=['last_accessed'])
            
            return Response({
                'success': True,
                'message': 'No changes to save',
                'draft_id': draft.id,
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def load_draft(self, request):
        """
        Load a saved draft for a specific award type.
        
        Query params:
        - draft_type: MCM, GOLD, SILVER, DM, PREVIOUS_WINNER
        """
        try:
            draft_type = request.query_params.get('draft_type')
            student = request.user.extrainfo.student
            
            draft = ScholarshipFormDraft.objects.get(
                student=student,
                draft_type=draft_type
            )
            
            # Update last accessed time
            draft.last_accessed = timezone.now()
            draft.save(update_fields=['last_accessed'])
            
            serializer = self.get_serializer(draft)
            return Response({
                'success': True,
                'draft': serializer.data,
                'message': f"Draft loaded for {draft.get_draft_type_display()}"
            }, status=status.HTTP_200_OK)
        
        except ScholarshipFormDraft.DoesNotExist:
            return Response({
                'success': False,
                'message': 'No saved draft found for this award type',
                'draft': None
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def list_drafts(self, request):
        """List all saved drafts for the authenticated student"""
        try:
            student = request.user.extrainfo.student
            drafts = ScholarshipFormDraft.objects.filter(student=student)
            serializer = self.get_serializer(drafts, many=True)
            
            return Response({
                'success': True,
                'drafts': serializer.data,
                'count': drafts.count(),
                'message': f"Found {drafts.count()} saved draft(s)"
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def delete_draft(self, request):
        """Delete a saved draft"""
        try:
            draft_type = request.data.get('draft_type')
            student = request.user.extrainfo.student
            
            draft = ScholarshipFormDraft.objects.get(
                student=student,
                draft_type=draft_type
            )
            
            draft_name = draft.get_draft_type_display()
            draft.delete()
            
            return Response({
                'success': True,
                'message': f'Draft for {draft_name} deleted successfully'
            }, status=status.HTTP_200_OK)
        
        except ScholarshipFormDraft.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Draft not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def mark_as_submitted(self, request):
        """
        Mark a draft as submitted and delete it.
        Called after successful form submission.
        """
        try:
            draft_type = request.data.get('draft_type')
            student = request.user.extrainfo.student
            
            draft = ScholarshipFormDraft.objects.get(
                student=student,
                draft_type=draft_type
            )
            
            # Log the successful submission
            DraftSaveLog.objects.create(
                draft=draft,
                save_reason='manual_save',
                fields_updated=['_submitted']
            )
            
            # Delete the draft since form is now submitted
            draft.delete()
            
            return Response({
                'success': True,
                'message': 'Draft marked as submitted and cleared'
            }, status=status.HTTP_200_OK)
        
        except ScholarshipFormDraft.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Draft not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def detect_timeout(self, request):
        """
        Handle session timeout detection.
        Auto-save current form data before logout.
        """
        try:
            draft_type = request.data.get('draft_type')
            form_data = request.data.get('form_data', {})
            
            student = request.user.extrainfo.student
            
            draft, _ = ScholarshipFormDraft.objects.get_or_create(
                student=student,
                draft_type=draft_type
            )
            
            draft.form_data = form_data
            draft.mark_interrupted('session_timeout', self.get_client_ip(request))
            
            DraftSaveLog.objects.create(
                draft=draft,
                save_reason='session_timeout',
                fields_updated=list(form_data.keys())
            )
            
            return Response({
                'success': True,
                'message': 'Form data saved before timeout',
                'draft_id': draft.id,
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
