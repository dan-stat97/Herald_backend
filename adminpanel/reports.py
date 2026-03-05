from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.pagination import PageNumberPagination
from django.db import models
from users.models import User as UserProfile
from .models import AdminReport, Ban
import uuid


class Report(models.Model):
    """Extended content report model"""
    RESOURCE_TYPE_CHOICES = [
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('user', 'User'),
    ]
    
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('copyright', 'Copyright Violation'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='reports_made')
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPE_CHOICES)
    resource_id = models.CharField(max_length=100)
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'content_reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report {self.id} - {self.resource_type} {self.resource_id}"


class AdminReportView(APIView):
    """Create and manage content reports"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get all reports (admin only)"""
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            
            # Check if admin
            if not profile.user_id.is_staff:
                return Response(
                    {'error': 'Admin access required'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Filter by status if provided
            report_status = request.query_params.get('status')
            reports = Report.objects.all()
            
            if report_status:
                reports = reports.filter(status=report_status)
            
            # Paginate
            paginator = PageNumberPagination()
            paginator.page_size = int(request.query_params.get('limit', 50))
            page = paginator.paginate_queryset(reports, request)
            
            reports_data = [{
                'id': report.id,
                'reporter': {
                    'id': report.reporter.id,
                    'username': report.reporter.username
                },
                'resource_type': report.resource_type,
                'resource_id': report.resource_id,
                'reason': report.reason,
                'description': report.description,
                'status': report.status,
                'created_at': report.created_at
            } for report in page]
            
            return paginator.get_paginated_response(reports_data)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch reports: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Create a new report"""
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            
            resource_type = request.data.get('resource_type')
            resource_id = request.data.get('resource_id')
            reason = request.data.get('reason')
            description = request.data.get('description', '')
            
            if not all([resource_type, resource_id, reason]):
                return Response(
                    {'error': 'resource_type, resource_id, and reason are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if resource_type not in ['post', 'comment', 'user']:
                return Response(
                    {'error': 'Invalid resource_type. Use: post, comment, or user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create report
            report = Report.objects.create(
                reporter=profile,
                resource_type=resource_type,
                resource_id=resource_id,
                reason=reason,
                description=description
            )
            
            return Response({
                'success': True,
                'message': 'Report submitted successfully',
                'report': {
                    'id': report.id,
                    'resource_type': report.resource_type,
                    'resource_id': report.resource_id,
                    'reason': report.reason,
                    'status': report.status,
                    'created_at': report.created_at
                }
            }, status=status.HTTP_201_CREATED)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminReportDetailView(APIView):
    """Update report status (admin only)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, report_id):
        """Update report status"""
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            
            # Check if admin
            if not profile.user_id.is_staff:
                return Response(
                    {'error': 'Admin access required'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            report = Report.objects.get(id=report_id)
            new_status = request.data.get('status')
            
            if new_status not in ['pending', 'reviewed', 'resolved', 'dismissed']:
                return Response(
                    {'error': 'Invalid status'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            report.status = new_status
            report.reviewed_by = profile
            
            if new_status == 'reviewed':
                from django.utils import timezone
                report.reviewed_at = timezone.now()
            
            report.save()
            
            return Response({
                'success': True,
                'report': {
                    'id': report.id,
                    'status': report.status,
                    'reviewed_by': profile.username,
                    'reviewed_at': report.reviewed_at
                }
            }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Report.DoesNotExist:
            return Response(
                {'error': 'Report not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to update report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
