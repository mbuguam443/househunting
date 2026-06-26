from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
from units.models import Unit
from .models import Inquiry, Testimonial, Faq, AdminListing
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
    admin_listing_count = AdminListing.objects.filter(status='available').count()
    return render(request, 'website/home.html', {
        'vacant_units': vacant_units,
        'testimonials': testimonials,
        'faqs': faqs,
        'total_units': total_units,
        'total_vacant': total_vacant,
        'total_occupied': total_occupied,
        'total_properties': total_properties,
        'total_landlords': total_landlords,
        'admin_listing_count': admin_listing_count,
    })

def browse(request):
    units = Unit.objects.filter(status='vacant').select_related('property')
    admin_listings = AdminListing.objects.filter(status='available')

    q = request.GET.get('q', '').strip()
    house_type = request.GET.get('house_type', '').strip()
    bedrooms = request.GET.get('bedrooms', '').strip()
    min_rent = request.GET.get('min_rent', '').strip()
    max_rent = request.GET.get('max_rent', '').strip()
    county = request.GET.get('county', '').strip()
    town = request.GET.get('town', '').strip()

    if q:
        units = units.filter(
            Q(property__name__icontains=q) |
            Q(property__town__icontains=q) |
            Q(property__county__icontains=q) |
            Q(property__estate__icontains=q) |
            Q(unit_number__icontains=q) |
            Q(description__icontains=q)
        )
        admin_listings = admin_listings.filter(
            Q(title__icontains=q) | Q(county__icontains=q) | Q(town__icontains=q) | Q(estate__icontains=q)
        )
    if house_type:
        units = units.filter(house_type=house_type)
        admin_listings = admin_listings.filter(house_type=house_type)
    if bedrooms:
        units = units.filter(bedrooms__gte=bedrooms)
        admin_listings = admin_listings.filter(bedrooms__gte=bedrooms)
    if min_rent:
        units = units.filter(monthly_rent__gte=min_rent)
        admin_listings = admin_listings.filter(rent__gte=min_rent)
    if max_rent:
        units = units.filter(monthly_rent__lte=max_rent)
        admin_listings = admin_listings.filter(rent__lte=max_rent)
    if county:
        units = units.filter(property__county__icontains=county)
        admin_listings = admin_listings.filter(county__icontains=county)
    if town:
        units = units.filter(property__town__icontains=town)
        admin_listings = admin_listings.filter(town__icontains=town)

    unit_counties = Unit.objects.filter(status='vacant').values_list(
        'property__county', flat=True).distinct()
    admin_counties = AdminListing.objects.filter(status='available').values_list(
        'county', flat=True).distinct()
    counties = sorted(set(list(unit_counties) + list(admin_counties)))

    combined = []
    for u in units:
        combined.append({
            'id': u.pk,
            'title': u.property.name,
            'subtitle': f'{u.property.town}, {u.property.county}',
            'description': u.description,
            'rent': u.monthly_rent,
            'house_type_display': u.get_house_type_display(),
            'bedrooms': u.bedrooms,
            'bathrooms': u.bathrooms,
            'image': u.image,
            'deposit': u.deposit,
            'url': f'/house/{u.pk}/',
            'source': 'landlord',
            'unit_number': u.unit_number,
            'created_at': u.created_at,
        })
    for a in admin_listings:
        gallery = list(a.images.values_list('image', flat=True))
        images = [a.image.url] + [img for img in gallery] if a.image else gallery
        combined.append({
            'id': a.pk,
            'title': a.title,
            'subtitle': f'{a.town}, {a.county}' + (f' — {a.estate}' if a.estate else ''),
            'description': a.description,
            'rent': a.rent,
            'house_type_display': a.get_house_type_display(),
            'bedrooms': a.bedrooms,
            'bathrooms': a.bathrooms,
            'image': a.image if a.image else None,
            'images': images if images else None,
            'deposit': None,
            'url': None,
            'source': 'admin',
            'contact_phone': a.contact_phone,
            'created_at': a.created_at,
        })

    combined.sort(key=lambda x: x['created_at'], reverse=True)
    total = len(combined)

    return render(request, 'website/browse.html', {
        'combined': combined,
        'counties': counties,
        'house_types': Unit.HOUSE_TYPES,
        'total': total,
        'q': q, 'house_type': house_type, 'bedrooms': bedrooms,
        'min_rent': min_rent, 'max_rent': max_rent, 'county': county, 'town': town,
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



