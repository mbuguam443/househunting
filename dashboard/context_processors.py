from website.models import Inquiry

def unread_inquiries(request):
    if request.user.is_authenticated and request.user.profile.role == 'landlord':
        count = Inquiry.objects.filter(unit__property__owner=request.user, is_read=False).count()
        recent = Inquiry.objects.filter(unit__property__owner=request.user, is_read=False).select_related('unit', 'unit__property').order_by('-created_at')[:5]
        return {'unread_count': count, 'recent_inquiries': recent}
    return {'unread_count': 0, 'recent_inquiries': []}
