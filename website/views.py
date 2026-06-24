from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
from units.models import Unit
from .models import Inquiry, Testimonial, Faq
from .forms import InquiryForm

def home(request):
    vacant_units = Unit.objects.filter(status='vacant').select_related('property')[:6]
    testimonials = Testimonial.objects.filter(is_active=True)
    faqs = Faq.objects.filter(is_active=True)
    total_units = Unit.objects.count()
    total_vacant = Unit.objects.filter(status='vacant').count()
    total_occupied = Unit.objects.filter(status='occupied').count()
    total_properties = Unit.objects.values('property').distinct().count()
    total_landlords = Unit.objects.values('property__owner').distinct().count()
    return render(request, 'website/home.html', {
        'vacant_units': vacant_units,
        'testimonials': testimonials,
        'faqs': faqs,
        'total_units': total_units,
        'total_vacant': total_vacant,
        'total_occupied': total_occupied,
        'total_properties': total_properties,
        'total_landlords': total_landlords,
    })

def browse(request):
    units = Unit.objects.filter(status='vacant').select_related('property')

    q = request.GET.get('q')
    house_type = request.GET.get('house_type')
    bedrooms = request.GET.get('bedrooms')
    min_rent = request.GET.get('min_rent')
    max_rent = request.GET.get('max_rent')
    county = request.GET.get('county')
    town = request.GET.get('town')

    if q:
        units = units.filter(
            Q(property__name__icontains=q) |
            Q(property__town__icontains=q) |
            Q(property__county__icontains=q) |
            Q(property__estate__icontains=q) |
            Q(unit_number__icontains=q) |
            Q(description__icontains=q)
        )
    if house_type:
        units = units.filter(house_type=house_type)
    if bedrooms:
        units = units.filter(bedrooms__gte=bedrooms)
    if min_rent:
        units = units.filter(monthly_rent__gte=min_rent)
    if max_rent:
        units = units.filter(monthly_rent__lte=max_rent)
    if county:
        units = units.filter(property__county__icontains=county)
    if town:
        units = units.filter(property__town__icontains=town)

    counties = Unit.objects.filter(status='vacant').values_list(
        'property__county', flat=True).distinct().order_by('property__county')

    return render(request, 'website/browse.html', {
        'units': units,
        'counties': counties,
        'house_types': Unit.HOUSE_TYPES,
    })

def house_detail(request, pk):
    unit = get_object_or_404(Unit.objects.select_related('property'), pk=pk)
    related = Unit.objects.filter(
        property=unit.property, status='vacant'
    ).exclude(pk=unit.pk)[:4]
    form = InquiryForm()

    if request.method == 'POST':
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.unit = unit
            inquiry.save()
            messages.success(request, 'Your inquiry has been sent. The landlord will contact you.')
            return redirect('website:house_detail', pk=unit.pk)

    return render(request, 'website/house_detail.html', {
        'unit': unit, 'related': related, 'form': form
    })

def about(request):
    from units.models import Unit
    total_units = Unit.objects.count()
    total_landlords = Unit.objects.values('property__owner').distinct().count()
    return render(request, 'website/about.html', {
        'total_units': total_units, 'total_landlords': total_landlords
    })

def contact(request):
    if request.method == 'POST':
        Inquiry.objects.create(
            name=request.POST.get('name', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            message=request.POST.get('message', ''),
        )
        messages.success(request, 'Thank you for reaching out. We will get back to you shortly.')
        return redirect('website:contact')
    return render(request, 'website/contact.html')
